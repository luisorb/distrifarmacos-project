from django.contrib import messages
from django.db import transaction
from django.db.models import Q
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, ListView, UpdateView

from core.utils import GruposRequeridosMixin, grupos_requeridos, is_ajax_request
from parametricas.models import Medicamento

from .forms import AfiliadoForm, FormulaBaseForm, SoporteForm, TecnologiaForm
from .models import Afiliado, FormulaBase, FormulaBaseTecnologia, SoporteFormulaBase


def _serializar_afiliado(a):
    return {
        "id": a.pk,
        "numero_documento": a.numero_documento,
        "nombres": a.nombres,
        "apellidos": a.apellidos,
        "tipo_documento": a.tipo_documento,
        "tipo_documento_label": a.get_tipo_documento_display(),
        "activo": a.activo,
        "activo_label": "Activo" if a.activo else "Inactivo",
        "activo_badge_class": "text-bg-success" if a.activo else "text-bg-secondary",
        "full_name": f"{a.nombres} {a.apellidos}",
        "edit_url": reverse("radicacion:editar_modal", args=[a.pk]),
        "radicar_url": f"{reverse('radicacion:radicar')}?afiliado={a.pk}",
        "delete_url": reverse("radicacion:eliminar", args=[a.pk]),
    }


def _serializar_formula(f):
    return {
        "id": f.pk,
        "codigo_formula": f.codigo_formula,
        "afiliado": str(f.afiliado),
        "afiliado_documento": f.afiliado.numero_documento,
        "medico": f.medico or "",
        "institucion": f.institucion,
        "fecha_formula": f.fecha_formula.strftime("%Y-%m-%d"),
        "fecha_formula_display": f.fecha_formula.strftime("%d/%m/%Y"),
        "activo": f.activo,
        "activo_label": "Activo" if f.activo else "Inactivo",
        "activo_badge_class": "text-bg-success" if f.activo else "text-bg-secondary",
        "detalle_url": reverse("formula:detalle", args=[f.pk]),
        "editar_url": reverse("formula:editar_modal", args=[f.pk]),
        "eliminar_url": reverse("formula:eliminar", args=[f.pk]),
        "delete_name": f"{f.codigo_formula} — {f.afiliado}",
    }


class AjaxModelFormMixin:
    ajax_template_name = None
    success_message = ""

    def form_invalid(self, form):
        if is_ajax_request(self.request) and self.ajax_template_name:
            html = render_to_string(
                self.ajax_template_name,
                self.get_context_data(form=form),
                request=self.request,
            )
            return HttpResponse(html, status=422)
        return super().form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        if is_ajax_request(self.request):
            return JsonResponse(
                {
                    "ok": True,
                    "redirect_url": self.get_success_url(),
                    "id": self.object.pk,
                    "label": str(self.object),
                    "message": self.success_message,
                }
            )
        return redirect(self.get_success_url())


class AfiliadoListView(GruposRequeridosMixin, ListView):
    grupos_requeridos = ("Digitador",)
    model = Afiliado
    template_name = "radicacion/afiliado_lista.html"
    context_object_name = "afiliados"

    def get_queryset(self):
        return Afiliado.objects.all().order_by("apellidos", "nombres")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        afiliados = list(context["afiliados"])
        context["afiliados_data"] = [_serializar_afiliado(a) for a in afiliados]
        return context


@grupos_requeridos("Digitador",)
@require_GET
def afiliados_json(request):
    afiliados = Afiliado.objects.all().order_by("apellidos", "nombres")
    return JsonResponse({"data": [_serializar_afiliado(a) for a in afiliados]})


class AfiliadoCreateView(GruposRequeridosMixin, AjaxModelFormMixin, CreateView):
    grupos_requeridos = ("Digitador",)
    model = Afiliado
    form_class = AfiliadoForm
    template_name = "radicacion/afiliado_modal_form.html"
    ajax_template_name = "radicacion/afiliado_modal_form.html"
    success_url = reverse_lazy("radicacion:lista")
    success_message = "Afiliado creado correctamente"


class AfiliadoUpdateView(GruposRequeridosMixin, AjaxModelFormMixin, UpdateView):
    grupos_requeridos = ("Digitador",)
    model = Afiliado
    form_class = AfiliadoForm
    template_name = "radicacion/afiliado_modal_form.html"
    ajax_template_name = "radicacion/afiliado_modal_form.html"
    success_url = reverse_lazy("radicacion:lista")
    success_message = "Afiliado actualizado correctamente"


@grupos_requeridos("Digitador",)
@require_POST
def afiliado_eliminar(request, pk):
    afiliado = get_object_or_404(Afiliado, pk=pk)
    nombre = str(afiliado)
    afiliado.delete()
    if is_ajax_request(request):
        return JsonResponse({"ok": True, "message": f"Afiliado \"{nombre}\" eliminado correctamente"})
    return redirect("radicacion:lista")


@grupos_requeridos("Digitador",)
def radicar_formula(request):
    desde_afiliados = "afiliado" in request.GET or request.POST.get("desde_afiliados") == "1"
    initial = {}
    afiliado_id = request.GET.get("afiliado") or request.POST.get("afiliado_id_hidden")
    if afiliado_id:
        try:
            afiliado_obj = Afiliado.objects.get(pk=afiliado_id)
            initial["afiliado"] = f"{afiliado_obj.nombres} {afiliado_obj.apellidos}"
        except Afiliado.DoesNotExist:
            afiliado_id = None
            initial["afiliado"] = ""

    if request.method == "POST":
        form = FormulaBaseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Save the base formula
                    formula = form.save(commit=False)
                    if afiliado_id:
                        formula.afiliado_id = afiliado_id
                    formula.save()

                    # 2. Save medications from the JSON payload
                    medicamentos_raw = request.POST.get("medicamentos_json", "[]")
                    try:
                        medicamentos_lista = json.loads(medicamentos_raw)
                    except (ValueError, TypeError):
                        medicamentos_lista = []

                    for item in medicamentos_lista:
                        try:
                            med_id = int(item.get("id", 0))
                            cantidad = int(item.get("cantidad", 0))
                            if med_id and cantidad > 0:
                                FormulaBaseTecnologia.objects.create(
                                    formula=formula,
                                    medicamento_id=med_id,
                                    cantidad_formulada=cantidad,
                                    indicaciones=item.get("info", ""),
                                )
                        except (ValueError, TypeError, Medicamento.DoesNotExist):
                            continue

                    # 3. Save uploaded files as soportes
                    archivos = request.FILES.getlist("archivos_formula")
                    for archivo in archivos:
                        SoporteFormulaBase.objects.create(
                            formula_base=formula,
                            archivo=archivo,
                            tipo_soporte="PRESCRIPCION",
                            usuario_carga=request.user if request.user.is_authenticated else None,
                        )

            except Exception as exc:
                if is_ajax_request(request):
                    return JsonResponse({"ok": False, "error": str(exc)}, status=500)
                messages.error(request, f"Error al guardar la fórmula: {exc}")
                form = FormulaBaseForm(request.POST, initial=initial)
                template = "radicacion/formula_modal_form.html" if is_ajax_request(request) else "radicacion/formula_form.html"
                return render(request, template, {"form": form, "desde_afiliados": desde_afiliados, "afiliado_id": afiliado_id})

            if is_ajax_request(request):
                return JsonResponse({"ok": True, "message": f"Fórmula {formula.codigo_formula} creada correctamente"})
            messages.success(request, f"Formula {formula.codigo_formula} creada.")
            return redirect("formula:detalle", pk=formula.pk)
        else:
            # Form invalid
            if is_ajax_request(request):
                html = render_to_string(
                    "radicacion/formula_modal_form.html",
                    {"form": form, "desde_afiliados": desde_afiliados, "afiliado_id": afiliado_id},
                    request=request,
                )
                return HttpResponse(html, status=422)
    else:
        form = FormulaBaseForm(initial=initial)

    template = "radicacion/formula_modal_form.html" if is_ajax_request(request) else "radicacion/formula_form.html"
    return render(request, template, {
        "form": form,
        "desde_afiliados": desde_afiliados,
        "afiliado_id": afiliado_id,
    })


class FormulaListView(GruposRequeridosMixin, ListView):
    grupos_requeridos = ("Digitador",)
    model = FormulaBase
    template_name = "radicacion/formula_lista.html"
    context_object_name = "formulas"

    def get_queryset(self):
        return FormulaBase.objects.select_related("afiliado").order_by("-fecha_creacion")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formulas = list(context["formulas"])
        context["formulas_data"] = [_serializar_formula(f) for f in formulas]
        return context


@grupos_requeridos("Digitador",)
@require_GET
def formulas_json(request):
    formulas = FormulaBase.objects.select_related("afiliado").all().order_by("-fecha_creacion")
    return JsonResponse({"data": [_serializar_formula(f) for f in formulas]})


class FormulaCreateView(GruposRequeridosMixin, AjaxModelFormMixin, CreateView):
    grupos_requeridos = ("Digitador",)
    model = FormulaBase
    form_class = FormulaBaseForm
    template_name = "radicacion/formula_form.html"
    ajax_template_name = "radicacion/formula_modal_form.html"
    success_url = reverse_lazy("formula:lista")

    def form_valid(self, form):
        afiliado_id = self.request.POST.get("afiliado_id_hidden")
        with transaction.atomic():
            self.object = form.save(commit=False)
            if afiliado_id:
                self.object.afiliado_id = afiliado_id
            self.object.save()

            medicamentos_raw = self.request.POST.get("medicamentos_json", "[]")
            try:
                medicamentos_lista = json.loads(medicamentos_raw)
            except (ValueError, TypeError):
                medicamentos_lista = []

            for item in medicamentos_lista:
                try:
                    med_id = int(item.get("id", 0))
                    cantidad = int(item.get("cantidad", 0))
                    if med_id and cantidad > 0:
                        FormulaBaseTecnologia.objects.create(
                            formula=self.object,
                            medicamento_id=med_id,
                            cantidad_formulada=cantidad,
                            indicaciones=item.get("info", ""),
                        )
                except (ValueError, TypeError, Medicamento.DoesNotExist):
                    continue

            archivos = self.request.FILES.getlist("archivos_formula")
            for archivo in archivos:
                SoporteFormulaBase.objects.create(
                    formula_base=self.object,
                    archivo=archivo,
                    tipo_soporte="PRESCRIPCION",
                    usuario_carga=self.request.user if self.request.user.is_authenticated else None,
                )

        if is_ajax_request(self.request):
            return JsonResponse({"ok": True, "message": "Fórmula creada correctamente"})
        return redirect(self.get_success_url())


@grupos_requeridos("Digitador",)
def formula_detalle(request, pk):
    formula = get_object_or_404(
        FormulaBase.objects.select_related("afiliado").prefetch_related("tecnologias", "soportes"),
        pk=pk,
    )
    tecnologias = formula.tecnologias.all()
    soportes = formula.soportes.all()
    context = {
        "formula": formula,
        "tecnologias": tecnologias,
        "soportes": soportes,
    }
    return render(request, "radicacion/formula_detalle.html", context)


@grupos_requeridos("Digitador",)
def editar_formula(request, pk):
    formula = get_object_or_404(
        FormulaBase.objects.select_related("afiliado").prefetch_related("tecnologias", "soportes"),
        pk=pk,
    )
    afiliado = formula.afiliado
    afiliado_display = f"{afiliado.nombres} {afiliado.apellidos}"

    if request.method == "POST":
        form = FormulaBaseForm(request.POST, instance=formula)
        if form.is_valid():
            try:
                with transaction.atomic():
                    FormulaBase.objects.filter(pk=formula.pk).update(
                        medico=form.cleaned_data.get("medico", ""),
                        institucion=form.cleaned_data.get("institucion", ""),
                        fecha_formula=form.cleaned_data.get("fecha_formula"),
                        observaciones=form.cleaned_data.get("observaciones", ""),
                        activo=form.cleaned_data.get("activo", True),
                    )
                    formula.refresh_from_db()

                    medicamentos_raw = request.POST.get("medicamentos_json", "[]")
                    try:
                        medicamentos_lista = json.loads(medicamentos_raw)
                    except (ValueError, TypeError):
                        medicamentos_lista = []

                    formula.tecnologias.all().delete()
                    for item in medicamentos_lista:
                        try:
                            med_id = int(item.get("id", 0))
                            cantidad = int(item.get("cantidad", 0))
                            if med_id and cantidad > 0:
                                FormulaBaseTecnologia.objects.create(
                                    formula=formula,
                                    medicamento_id=med_id,
                                    cantidad_formulada=cantidad,
                                    indicaciones=item.get("info", ""),
                                )
                        except (ValueError, TypeError):
                            continue

                    archivos = request.FILES.getlist("archivos_formula")
                    for archivo in archivos:
                        SoporteFormulaBase.objects.create(
                            formula_base=formula,
                            archivo=archivo,
                            tipo_soporte="PRESCRIPCION",
                            usuario_carga=request.user if request.user.is_authenticated else None,
                        )

                # Success — return outside the transaction so any commit errors are caught
                if is_ajax_request(request):
                    return JsonResponse({"ok": True, "message": f"Fórmula {formula.codigo_formula} actualizada correctamente"})
                messages.success(request, f"Formula {formula.codigo_formula} actualizada.")
                return redirect("formula:detalle", pk=formula.pk)

            except Exception as exc:
                if is_ajax_request(request):
                    return JsonResponse({"ok": False, "error": str(exc)}, status=500)
                messages.error(request, f"Error al guardar: {exc}")
                return render(request, "radicacion/formula_editar_modal.html",
                              _editar_context(formula, form, afiliado_display))

        # Form invalid
        if is_ajax_request(request):
            html = render_to_string(
                "radicacion/formula_editar_modal.html",
                _editar_context(formula, form, afiliado_display),
                request=request,
            )
            return HttpResponse(html, status=422)
        return render(request, "radicacion/formula_editar_modal.html",
                      _editar_context(formula, form, afiliado_display), status=400)

    else:
        initial = {
            "afiliado": afiliado_display,
            "fecha_formula": formula.fecha_formula,
        }
        form = FormulaBaseForm(instance=formula, initial=initial)

    context = _editar_context(formula, form, afiliado_display)
    template = "radicacion/formula_editar_modal.html" if is_ajax_request(request) else "radicacion/formula_form.html"
    return render(request, template, context)


def _editar_context(formula, form, afiliado_display):
    tecnologias_data = [
        {
            "id": str(t.medicamento_id),
            "label": t.medicamento_nombre,
            "cantidad": t.cantidad_formulada,
            "info": t.indicaciones,
        }
        for t in formula.tecnologias.select_related("medicamento").all()
    ]
    soportes_existentes = [
        {
            "nombre": s.nombre_archivo,
            "url": s.archivo.url,
            "version": s.version,
            "tipo": s.get_tipo_soporte_display(),
            "es_pdf": s.nombre_archivo.lower().endswith(".pdf"),
        }
        for s in formula.soportes.all()
    ]
    return {
        "formula": formula,
        "form": form,
        "afiliado_display": afiliado_display,
        "tecnologias_data": tecnologias_data,
        "soportes_existentes": soportes_existentes,
    }


@grupos_requeridos("Digitador",)
@require_POST
def formula_eliminar(request, pk):
    formula = get_object_or_404(FormulaBase, pk=pk)
    nombre = formula.codigo_formula
    formula.delete()
    if is_ajax_request(request):
        return JsonResponse({"ok": True, "message": f"Fórmula {nombre} eliminada correctamente"})
    return redirect("formula:lista")


@grupos_requeridos("Digitador",)
@require_POST
def formula_agregar_tecnologia(request, pk):
    formula = get_object_or_404(FormulaBase, pk=pk)
    form = TecnologiaForm(request.POST)
    if form.is_valid():
        tecnologia = form.save(commit=False)
        tecnologia.formula = formula
        tecnologia.save()
        messages.success(request, "Tecnología agregada correctamente.")
        return redirect("formula:detalle", pk=formula.pk)
    return render(
        request,
        "radicacion/formula_detalle.html",
        {
            "formula": formula,
            "tecnologias": formula.tecnologias.all(),
            "soportes": formula.soportes.all(),
            "tecnologia_form": form,
            "soporte_form": SoporteForm(),
        },
        status=400,
    )


@grupos_requeridos("Digitador",)
@require_POST
def cargar_soporte(request, pk):
    formula = get_object_or_404(FormulaBase, pk=pk)
    form = SoporteForm(request.POST, request.FILES)
    if form.is_valid():
        soporte = form.save(commit=False)
        soporte.formula_base = formula
        soporte.usuario_carga = request.user if request.user.is_authenticated else None
        soporte.save()
        if is_ajax_request(request):
            return JsonResponse({"ok": True, "redirect_url": reverse_lazy("formula:detalle", kwargs={"pk": formula.pk}), "message": "Soporte cargado correctamente"})
        messages.success(request, "Soporte cargado correctamente.")
        return redirect("formula:detalle", pk=formula.pk)
    if is_ajax_request(request):
        html = render_to_string(
            "radicacion/soporte_modal_form.html",
            {"form": form, "formula": formula},
            request=request,
        )
        return HttpResponse(html, status=422)
    return render(
        request,
        "radicacion/cargar_soporte.html",
        {"form": form, "formula": formula},
        status=400,
    )


@grupos_requeridos("Digitador",)
@require_GET
def buscar_medicamento(request):
    query = request.GET.get("q", "").strip()
    medicamentos = Medicamento.objects.filter(activo=True)
    if query:
        medicamentos = medicamentos.filter(
            Q(cum__icontains=query)
            | Q(nombre_generico__icontains=query)
            | Q(titular_registro__icontains=query)
            | Q(concentracion__icontains=query)
        )
    resultados = [
        {"id": medicamento.pk, "text": f"{medicamento.cum} - {medicamento.nombre_generico} {medicamento.concentracion}"}
        for medicamento in medicamentos.order_by("nombre_generico", "cum")[:10]
    ]
    return JsonResponse({"results": resultados})


@grupos_requeridos("Digitador",)
@require_GET
def buscar_afiliado(request):
    query = request.GET.get("q", "").strip()
    afiliados = Afiliado.objects.all()
    if query:
        afiliados = afiliados.filter(
            Q(numero_documento__icontains=query)
            | Q(nombres__icontains=query)
            | Q(apellidos__icontains=query)
        )
    resultados = [
        {"id": a.pk, "text": f"{a.numero_documento} - {a.nombres} {a.apellidos}"}
        for a in afiliados.order_by("apellidos", "nombres")[:15]
    ]
    return JsonResponse({"results": resultados})
