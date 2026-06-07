from django.urls import path

from . import views

app_name = "parametricas"

urlpatterns = [
    path("", views.MedicamentoListView.as_view(), name="lista"),
    path("crear/", views.MedicamentoCreateView.as_view(), name="crear"),
    path(
        "crear/modal/",
        views.MedicamentoCreateView.as_view(template_name="parametricas/medicamento_modal_form.html"),
        name="crear_modal",
    ),
    path("<int:pk>/editar/", views.MedicamentoUpdateView.as_view(), name="editar"),
    path(
        "<int:pk>/editar/modal/",
        views.MedicamentoUpdateView.as_view(template_name="parametricas/medicamento_modal_form.html"),
        name="editar_modal",
    ),
    path("<int:pk>/eliminar/", views.medicamento_eliminar, name="eliminar"),
    path("datos/", views.medicamentos_json, name="datos_json"),
]
