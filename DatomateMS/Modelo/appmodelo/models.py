import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PrediccionTomate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)

    # Datos base de la predicción
    dia_predicho = models.DateField()
    produccion_predicha_kg = models.FloatField()

    # Campos adicionales opcionales
    dias_usados = models.JSONField()  # guarda los días que usaste del histórico
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = "Predicción de tomate"
        verbose_name_plural = "Predicciones de tomate"

    def __str__(self):
        return f"Predicción {self.id} - Usuario {self.user_id}"
