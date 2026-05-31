from django import forms

from parametricas.models import Medicamento

from .models import Afiliado, FormulaBase, FormulaBaseTecnologia, Medico, SoporteFormulaBase


class AfiliadoForm(forms.ModelForm):
    class Meta:
        model = Afiliado
        fields = ["tipo_documento", "numero_documento", "nombres", "apellidos", "activo"]
        widgets = {
            "tipo_documento": forms.Select(attrs={"class": "form-select"}),
            "numero_documento": forms.TextInput(attrs={"class": "form-control", "placeholder": "Número de documento"}),
            "nombres": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombres"}),
            "apellidos": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellidos"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class FormulaBaseForm(forms.ModelForm):
    class Meta:
        model = FormulaBase
        fields = ["afiliado", "medico", "institucion", "fecha_formula", "observaciones", "activo"]
        widgets = {
            "afiliado": forms.Select(attrs={"class": "form-select"}),
            "medico": forms.Select(attrs={"class": "form-select"}),
            "institucion": forms.TextInput(attrs={"class": "form-control", "placeholder": "Institución"}),
            "fecha_formula": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TecnologiaForm(forms.ModelForm):
    medicamento = forms.ModelChoiceField(
        queryset=Medicamento.objects.none(),
        widget=forms.Select(attrs={"class": "form-select medicamento-select"}),
    )

    class Meta:
        model = FormulaBaseTecnologia
        fields = ["medicamento", "cantidad_formulada", "dosis", "indicaciones"]
        widgets = {
            "cantidad_formulada": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "dosis": forms.TextInput(attrs={"class": "form-control", "placeholder": "Dosis"}),
            "indicaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["medicamento"].queryset = Medicamento.objects.filter(activo=True).order_by(
            "nombre_generico", "cum"
        )


class SoporteForm(forms.ModelForm):
    medicamento = forms.ModelChoiceField(
        queryset=Medicamento.objects.none(),
        widget=forms.Select(attrs={"class": "form-select medicamento-select"}),
    )

    class Meta:
        model = SoporteFormulaBase
        fields = ["tipo_soporte", "medicamento", "archivo", "indicaciones"]
        widgets = {
            "tipo_soporte": forms.Select(attrs={"class": "form-select"}),
            "archivo": forms.FileInput(attrs={"class": "form-control"}),
            "indicaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["medicamento"].queryset = Medicamento.objects.filter(activo=True).order_by(
            "nombre_generico", "cum"
        )
