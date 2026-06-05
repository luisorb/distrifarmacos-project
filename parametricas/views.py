from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView

from core.utils import GruposRequeridosMixin, grupos_requeridos, is_ajax_request

from .forms import MedicamentoForm
from .models import Medicamento


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


class MedicamentoListView(GruposRequeridosMixin, ListView):
    grupos_requeridos = ("Digitador",)
    model = Medicamento
    template_name = "parametricas/medicamento_lista.html"
    context_object_name = "medicamentos"

    def get_queryset(self):
        return Medicamento.objects.all().order_by("nombre_generico", "cum")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        medicamentos = list(context["medicamentos"])
        context["medicamentos_data"] = [
            {
                "id": m.pk,
                "cum": m.cum,
                "nombre_generico": m.nombre_generico,
                "titular_registro": m.titular_registro,
                "concentracion": m.concentracion,
                "activo": m.activo,
                "activo_label": "Activo" if m.activo else "Inactivo",
                "activo_badge_class": "text-bg-success" if m.activo else "text-bg-secondary",
                "editar_url": reverse("parametricas:editar_modal", args=[m.pk]),
                "eliminar_url": reverse("parametricas:eliminar", args=[m.pk]),
            }
            for m in medicamentos
        ]
        return context


class MedicamentoCreateView(GruposRequeridosMixin, AjaxModelFormMixin, CreateView):
    grupos_requeridos = ("Digitador",)
    model = Medicamento
    form_class = MedicamentoForm
    template_name = "parametricas/medicamento_form.html"
    ajax_template_name = "parametricas/medicamento_modal_form.html"
    success_url = reverse_lazy("parametricas:lista")


class MedicamentoUpdateView(GruposRequeridosMixin, AjaxModelFormMixin, UpdateView):
    grupos_requeridos = ("Digitador",)
    model = Medicamento
    form_class = MedicamentoForm
    template_name = "parametricas/medicamento_form.html"
    ajax_template_name = "parametricas/medicamento_modal_form.html"
    success_url = reverse_lazy("parametricas:lista")


@grupos_requeridos("Digitador",)
@require_POST
def medicamento_eliminar(request, pk):
    medicamento = get_object_or_404(Medicamento, pk=pk)
    medicamento.delete()
    if is_ajax_request(request):
        return JsonResponse({"ok": True})
    return redirect("parametricas:lista")
