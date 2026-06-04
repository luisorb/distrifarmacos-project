from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from parametricas.models import Medicamento
from radicacion.models import Afiliado, FormulaBase


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_medicamentos"] = Medicamento.objects.filter(activo=True).count()
        context["total_afiliados"] = Afiliado.objects.filter(activo=True).count()
        context["formulas_pendientes"] = FormulaBase.objects.filter(activo=True).count()
        return context


@require_POST
def logout_view(request):
    auth_logout(request)
    return HttpResponseRedirect(resolve_url(settings.LOGIN_URL))
