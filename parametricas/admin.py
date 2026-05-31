from django.contrib import admin

from .models import Medicamento


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ("cum", "nombre_generico", "titular_registro", "concentracion", "activo")
    search_fields = ("cum", "nombre_generico", "titular_registro")
    list_filter = ("activo",)
