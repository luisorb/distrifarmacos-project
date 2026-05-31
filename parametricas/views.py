from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView

from core.utils import is_ajax_request

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


class MedicamentoListView(ListView):
    model = Medicamento
    template_name = "parametricas/medicamento_lista.html"
    context_object_name = "medicamentos"
    paginate_by = 20

    def get_queryset(self):
        return Medicamento.objects.all().order_by("nombre_generico", "cum")


class MedicamentoCreateView(AjaxModelFormMixin, CreateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = "parametricas/medicamento_form.html"
    ajax_template_name = "parametricas/medicamento_modal_form.html"
    success_url = reverse_lazy("parametricas:lista")


class MedicamentoUpdateView(AjaxModelFormMixin, UpdateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = "parametricas/medicamento_form.html"
    ajax_template_name = "parametricas/medicamento_modal_form.html"
    success_url = reverse_lazy("parametricas:lista")


@require_POST
def medicamento_eliminar(request, pk):
    medicamento = get_object_or_404(Medicamento, pk=pk)
    medicamento.delete()
    if is_ajax_request(request):
        return JsonResponse({"ok": True})
    return redirect("parametricas:lista")
