from django.contrib import admin

from .models import Afiliado, FormulaBase, FormulaBaseTecnologia, Medico, SoporteFormulaBase


@admin.register(Afiliado)
class AfiliadoAdmin(admin.ModelAdmin):
    list_display = ("numero_documento", "nombres", "apellidos", "tipo_documento", "activo")
    search_fields = ("numero_documento", "nombres", "apellidos")


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ("registro_medico", "nombres", "apellidos", "activo")
    search_fields = ("registro_medico", "nombres", "apellidos")


@admin.register(FormulaBase)
class FormulaBaseAdmin(admin.ModelAdmin):
    list_display = ("codigo_formula", "afiliado", "medico", "institucion", "fecha_formula", "activo")
    search_fields = ("codigo_formula", "afiliado__numero_documento", "medico")


@admin.register(SoporteFormulaBase)
class SoporteFormulaBaseAdmin(admin.ModelAdmin):
    list_display = ("formula_base", "tipo_soporte", "medicamento_nombre", "version", "activo")
    search_fields = ("formula_base__codigo_formula", "medicamento_nombre")


@admin.register(FormulaBaseTecnologia)
class FormulaBaseTecnologiaAdmin(admin.ModelAdmin):
    list_display = ("formula", "medicamento_nombre", "cantidad_formulada", "contrato_asignado", "activo")
    search_fields = ("formula__codigo_formula", "medicamento_nombre")
