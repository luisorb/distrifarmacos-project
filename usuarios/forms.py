from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Contraseña"}),
        required=False,
        help_text="Dejar en blanco para mantener la contraseña actual (solo en edición).",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirmar contraseña"}),
        required=False,
        label="Confirmar contraseña",
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Usuario"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Correo electrónico"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombres"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellidos"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "username": "Usuario",
            "email": "Correo electrónico",
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "is_active": "Activo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["password"].help_text = "Dejar en blanco para mantener la contraseña actual."
            self.fields["password"].required = False
            self.fields["confirm_password"].required = False
            self.fields["username"].disabled = True
        else:
            self.fields["password"].required = True
            self.fields["confirm_password"].required = True
            self.fields["password"].help_text = ""

        for field_name, field in self.fields.items():
            if field_name == "is_active":
                continue
            if field_name in ("first_name", "last_name", "email"):
                field.required = True
            if field.required:
                field.widget.attrs["data-req"] = "true"

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password or confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class UsuarioGruposForm(forms.Form):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=False,
        label="Grupos",
    )
