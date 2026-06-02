from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, ListView, UpdateView

from core.utils import is_ajax_request
from parametricas.models import Medicamento

from .forms import AfiliadoForm, FormulaBaseForm, SoporteForm, TecnologiaForm
from .models import Afiliado, FormulaBase, FormulaBaseTecnologia, SoporteFormulaBase


class AjaxModelFormMixin:
    ajax_template_name = None

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
                }
            )
        return redirect(self.get_success_url())


class AfiliadoListView(ListView):
    model = Afiliado
    template_name = "radicacion/afiliado_lista.html"
    context_object_name = "afiliados"

    def get_queryset(self):
        return Afiliado.objects.all().order_by("apellidos", "nombres")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        afiliados = list(context["afiliados"])
        context["afiliados_data"] = [
            {
                "id": afiliado.pk,
                "numero_documento": afiliado.numero_documento,
                "nombres": afiliado.nombres,
                "apellidos": afiliado.apellidos,
                "tipo_documento": afiliado.tipo_documento,
                "tipo_documento_label": afiliado.get_tipo_documento_display(),
                "activo": afiliado.activo,
                "activo_label": "Activo" if afiliado.activo else "Inactivo",
                "activo_badge_class": "text-bg-success" if afiliado.activo else "text-bg-secondary",
                "full_name": f"{afiliado.nombres} {afiliado.apellidos}",
                "edit_url": reverse("radicacion:editar_modal", args=[afiliado.pk]),
                "radicar_url": f"{reverse('radicacion:radicar')}?afiliado={afiliado.pk}",
                "delete_url": reverse("radicacion:eliminar", args=[afiliado.pk]),
            }
            for afiliado in afiliados
        ]
        return context


class AfiliadoCreateView(AjaxModelFormMixin, CreateView):
    model = Afiliado
    form_class = AfiliadoForm
    template_name = "radicacion/afiliado_modal_form.html"
    ajax_template_name = "radicacion/afiliado_modal_form.html"
    success_url = reverse_lazy("radicacion:lista")


class AfiliadoUpdateView(AjaxModelFormMixin, UpdateView):
    model = Afiliado
    form_class = AfiliadoForm
    template_name = "radicacion/afiliado_modal_form.html"
    ajax_template_name = "radicacion/afiliado_modal_form.html"
    success_url = reverse_lazy("radicacion:lista")


@require_POST
def afiliado_eliminar(request, pk):
    afiliado = get_object_or_404(Afiliado, pk=pk)
    afiliado.delete()
    if is_ajax_request(request):
        return JsonResponse({"ok": True})
    return redirect("radicacion:lista")


def radicar_formula(request):
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
                    import json
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
                return render(request, template, {"form": form, "desde_afiliados": True, "afiliado_id": afiliado_id})

            if is_ajax_request(request):
                return JsonResponse({
                    "ok": True,
                    "redirect_url": reverse("formula:detalle", kwargs={"pk": formula.pk}),
                })
            messages.success(request, f"Formula {formula.codigo_formula} creada.")
            return redirect("formula:detalle", pk=formula.pk)
        else:
            # Form invalid
            if is_ajax_request(request):
                html = render_to_string(
                    "radicacion/formula_modal_form.html",
                    {"form": form, "desde_afiliados": True, "afiliado_id": afiliado_id},
                    request=request,
                )
                return HttpResponse(html, status=422)
    else:
        form = FormulaBaseForm(initial=initial)

    template = "radicacion/formula_modal_form.html" if is_ajax_request(request) else "radicacion/formula_form.html"
    return render(request, template, {
        "form": form,
        "desde_afiliados": True,
        "afiliado_id": afiliado_id,
    })


class FormulaListView(ListView):
    model = FormulaBase
    template_name = "radicacion/formula_lista.html"
    context_object_name = "formulas"
    paginate_by = 20

    def get_queryset(self):
        queryset = FormulaBase.objects.select_related("afiliado")
        term = self.request.GET.get("q", "").strip()
        if term:
            queryset = queryset.filter(
                Q(codigo_formula__icontains=term)
                | Q(afiliado__numero_documento__icontains=term)
                | Q(afiliado__nombres__icontains=term)
                | Q(afiliado__apellidos__icontains=term)
            )
        return queryset.order_by("-fecha_creacion")


class FormulaCreateView(AjaxModelFormMixin, CreateView):
    model = FormulaBase
    form_class = FormulaBaseForm
    template_name = "radicacion/formula_form.html"
    ajax_template_name = "radicacion/formula_modal_form.html"
    success_url = reverse_lazy("formula:lista")


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
            return JsonResponse({"ok": True, "redirect_url": reverse_lazy("formula:detalle", kwargs={"pk": formula.pk})})
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
