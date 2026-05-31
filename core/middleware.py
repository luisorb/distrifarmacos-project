from django.conf import settings
from django.shortcuts import redirect, resolve_url


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        exempt_prefixes = (
            "/accounts/",
            "/admin/",
            settings.STATIC_URL,
            settings.MEDIA_URL,
        )
        if request.user.is_authenticated or path.startswith(exempt_prefixes):
            return self.get_response(request)
        return redirect(resolve_url(settings.LOGIN_URL))
