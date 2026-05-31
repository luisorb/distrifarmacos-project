from django.db import models


class ModeloBase(models.Model):
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Medicamento(ModeloBase):
    cum = models.CharField(max_length=30, unique=True)
    nombre_generico = models.CharField(max_length=255)
    titular_registro = models.CharField(max_length=255)
    concentracion = models.CharField(max_length=120)

    class Meta:
        ordering = ("nombre_generico", "cum")

    def __str__(self) -> str:
        return f"{self.cum} - {self.nombre_generico}"
