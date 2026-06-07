from django.urls import path

from . import views

app_name = "formula"

urlpatterns = [
    path("", views.FormulaListView.as_view(), name="lista"),
    path("crear/", views.FormulaCreateView.as_view(), name="crear"),
    path(
        "crear/modal/",
        views.FormulaCreateView.as_view(template_name="radicacion/formula_modal_form.html"),
        name="crear_modal",
    ),
    path("<int:pk>/", views.formula_detalle, name="detalle"),
    path("<int:pk>/editar/modal/", views.editar_formula, name="editar_modal"),
    path("<int:pk>/eliminar/", views.formula_eliminar, name="eliminar"),
    path("<int:pk>/tecnologia/", views.formula_agregar_tecnologia, name="agregar_tecnologia"),
    path("<int:pk>/soporte/", views.cargar_soporte, name="cargar_soporte"),
    path("radicar/", views.radicar_formula, name="radicar"),
    path("api/medicamentos/", views.buscar_medicamento, name="api_medicamentos"),
    path("api/afiliados/", views.buscar_afiliado, name="api_afiliados"),
    path("datos/", views.formulas_json, name="datos_json"),
]
