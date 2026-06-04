from functools import wraps

from django.core.exceptions import PermissionDenied


def is_ajax_request(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def grupos_requeridos(*grupos):
    grupos_normalizados = {grupo for grupo in grupos if grupo}

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                if user.is_superuser or user.groups.filter(name__in=grupos_normalizados).exists():
                    return view_func(request, *args, **kwargs)
            raise PermissionDenied

        return wrapped

    return decorator


class GruposRequeridosMixin:
    grupos_requeridos = ()

    def dispatch(self, request, *args, **kwargs):
        grupos = tuple(self.grupos_requeridos or ())
        if request.user.is_authenticated and (request.user.is_superuser or request.user.groups.filter(name__in=grupos).exists()):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied
