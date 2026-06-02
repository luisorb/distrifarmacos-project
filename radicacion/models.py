from django.conf import settings
from django.db import models
from django.db.models import Max

from parametricas.models import Medicamento, ModeloBase


class TipoDocumento(models.TextChoices):
    CC = "CC", "Cédula de ciudadanía"
    CE = "CE", "Cédula de extranjería"
    TI = "TI", "Tarjeta de identidad"
    PA = "PA", "Pasaporte"
    RC = "RC", "Registro civil"
    OTRO = "OTRO", "Otro"


class TipoSoporte(models.TextChoices):
    PRESCRIPCION = "PRESCRIPCION", "Prescripción"
    AUTORIZACION = "AUTORIZACION", "Autorización"
    ANEXO = "ANEXO", "Anexo"
    OTRO = "OTRO", "Otro"


class ContratoAsignado(models.TextChoices):
    CAPITA = "CAPITA", "Capita"
    EVENTO = "EVENTO", "Evento"


class Afiliado(ModeloBase):
    tipo_documento = models.CharField(max_length=10, choices=TipoDocumento.choices)
    numero_documento = models.CharField(max_length=30, unique=True)
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)

    class Meta:
        ordering = ("apellidos", "nombres")

    def __str__(self) -> str:
        return f"{self.numero_documento} - {self.nombres} {self.apellidos}"


class FormulaBase(ModeloBase):
    codigo_formula = models.CharField(max_length=20, unique=True, blank=True)
    afiliado = models.ForeignKey(Afiliado, on_delete=models.PROTECT, related_name="formulas")
    medico = models.CharField(max_length=255, blank=True)
    institucion = models.CharField(max_length=255)
    fecha_formula = models.DateField()
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ("-fecha_creacion",)

    def save(self, *args, **kwargs):
        if not self.codigo_formula:
            max_id = FormulaBase.objects.aggregate(max_id=Max("id")).get("max_id") or 0
            self.codigo_formula = f"FOR-{max_id + 1:06d}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.codigo_formula or "Nueva fórmula"


class SoporteFormulaBase(ModeloBase):
    formula_base = models.ForeignKey(FormulaBase, on_delete=models.CASCADE, related_name="soportes")
    archivo = models.FileField(upload_to="soportes/")
    tipo_soporte = models.CharField(max_length=50, choices=TipoSoporte.choices)
    medicamento = models.ForeignKey(
        Medicamento,
        on_delete=models.PROTECT,
        related_name="soportes",
        null=True,
        blank=True,
    )
    medicamento_nombre = models.CharField(max_length=400, blank=True)
    indicaciones = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1, editable=False)
    usuario_carga = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="soportes_formula",
    )

    class Meta:
        ordering = ("-fecha_creacion",)

    def save(self, *args, **kwargs):
        if self.medicamento_id:
            self.medicamento_nombre = (
                f"{self.medicamento.cum} - {self.medicamento.nombre_generico} {self.medicamento.concentracion}"
            )
        if not self.pk:
            ultimo_version = (
                SoporteFormulaBase.objects.filter(
                    formula_base=self.formula_base,
                    tipo_soporte=self.tipo_soporte,
                ).aggregate(max_version=Max("version")).get("max_version")
                or 0
            )
            self.version = ultimo_version + 1
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.formula_base} - {self.tipo_soporte} v{self.version}"

    @property
    def nombre_archivo(self):
        """Returns just the filename without the upload path."""
        return self.archivo.name.split("/")[-1] if self.archivo else ""


class FormulaBaseTecnologia(ModeloBase):
    formula = models.ForeignKey(FormulaBase, on_delete=models.CASCADE, related_name="tecnologias")
    medicamento = models.ForeignKey(Medicamento, on_delete=models.PROTECT, related_name="tecnologias")
    medicamento_nombre = models.CharField(max_length=400, blank=True)
    cantidad_formulada = models.PositiveIntegerField()
    dosis = models.CharField(max_length=120, blank=True)
    indicaciones = models.TextField(blank=True)
    contrato_asignado = models.CharField(max_length=20, choices=ContratoAsignado.choices, blank=True)

    class Meta:
        ordering = ("-fecha_creacion",)

    def save(self, *args, **kwargs):
        if self.medicamento_id:
            self.medicamento_nombre = (
                f"{self.medicamento.cum} - {self.medicamento.nombre_generico} {self.medicamento.concentracion}"
            )
        nombre_busqueda = (self.medicamento_nombre or "").upper()
        if not self.contrato_asignado:
            self.contrato_asignado = (
                ContratoAsignado.CAPITA if "GENERICO" in nombre_busqueda else ContratoAsignado.EVENTO
            )
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.formula} - {self.medicamento_nombre or self.medicamento}"
