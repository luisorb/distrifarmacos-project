from django.urls import path

from . import views

app_name = "radicacion"

urlpatterns = [
    path("", views.AfiliadoListView.as_view(), name="lista"),
    path(
        "crear/modal/",
        views.AfiliadoCreateView.as_view(),
        name="crear_modal",
    ),
    path(
        "<int:pk>/editar/modal/",
        views.AfiliadoUpdateView.as_view(),
        name="editar_modal",
    ),
    path("<int:pk>/eliminar/", views.afiliado_eliminar, name="eliminar"),
    path("radicar/", views.radicar_formula, name="radicar"),
]
