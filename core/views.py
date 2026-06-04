from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView


class DashboardView(TemplateView):
    template_name = "dashboard.html"


@require_POST
def logout_view(request):
    auth_logout(request)
    return HttpResponseRedirect(resolve_url(settings.LOGIN_URL))
