"""
Vista que obtiene las últimas lecturas del MS Histórico
y predice la producción del siguiente día.
"""

"""
Usa los últimos 5 registros del usuario autenticado para predecir la producción.
Devuelve el valor predicho y los días usados.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from appmodelo.serializers import PrediccionTomateSerializer
from appmodelo.models import PrediccionTomate
from appmodelo.permissions import IsOwner
import numpy as np
from tensorflow.keras.models import load_model
from datetime import datetime, timedelta
import requests


# Cargar modelo de predicción
MODEL_PATH = "model/prediccion_tomates_5dias.keras"
model = load_model(MODEL_PATH)

# URL del microservicio histórico
HISTORICO_MS_URL = "http://127.0.0.1:4000/api/v1/predicciones/"

class PrediccionTomateViewSet(viewsets.ViewSet):
    """
    Endpoint que obtiene datos del MS-Histórico y usa el modelo TensorFlow para predecir producción.
    """
    permission_classes = [permissions.IsAuthenticated]
    @action(detail=False, methods=['get'], url_path='predecir')
    def predecir(self, request):

        user_id = request.user.id
        token = request.auth  # JWT del usuario
        headers = {"Authorization": f"Bearer {token}"}

        # Obtener lecturas del MS Histórico
        try:
            response = requests.get(HISTORICO_MS_URL, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return Response({"error": f"No se pudo obtener datos del MS Histórico: {str(e)}"},
                            status=status.HTTP_502_BAD_GATEWAY)

        historicos = response.json()

        # Validar que haya registros suficientes
        if not historicos or len(historicos) < 5:
            return Response({
                "error": f"Se requieren al menos 5 registros para predecir, solo hay {len(historicos)} disponibles."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Ordenar por fecha y tomar los últimos 5 registros
        lecturas = sorted(historicos, key=lambda x: x["created_at"])[-5:]

        # Crear array (5, 4) con las variables del modelo
        try:
            datos = np.array([
                [
                    float(l["Humedad_Media"]),
                    float(l["Temp_Media"]),
                    float(l["Longitud_Tallo"]),
                    float(l["Diametro_Tallo"])
                ]
                for l in lecturas
            ])
        except KeyError as e:
            return Response({"error": f"Falta el campo {str(e)} en los datos del histórico"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        entrada = datos.reshape(1, 5, 4)

        # Hacer la predicción
        prediccion = model.predict(entrada)
        resultado = float(prediccion[0][0])

        # Calcular el siguiente día
        ultimo_dia = datetime.fromisoformat(lecturas[-1]["created_at"].replace("Z", ""))
        dia_siguiente = ultimo_dia + timedelta(days=1)

        pred = PrediccionTomate.objects.create(
            user_id=request.user.id,
            dia_predicho=dia_siguiente,
            produccion_predicha_kg=resultado,
            dias_usados=[l["created_at"] for l in lecturas]
        )

        serializer = PrediccionTomateSerializer(pred)

        return Response({
            "usuario": str(user_id),
            "dias_usados": [str(l["created_at"]) for l in lecturas],
            "dia_predicho": dia_siguiente.strftime("%Y-%m-%d"),
            "produccion_predicha_kg": round(resultado, 2)
        }, status=status.HTTP_200_OK)


# appmodelo/views.py

# ... Tus imports y configuraciones ...

class ListarPrediccionesViewSet(viewsets.ViewSet):  # ⬅️ Usar viewsets.ViewSet (más simple)
    permission_classes = [permissions.IsAuthenticated]

    # 💡 Renombramos la función a "list" o "get_predicciones" por convención.
    # Si la mapeas directamente en urls.py, NO necesitas el decorador @action aquí.
    def list(self, request):
        """Devuelve todas las predicciones previas del usuario autenticado."""
        user_id = request.user.id

        # ⚠️ OJO: Usar '-dia_predicho' o '-pk' si 'creado_en' no es un campo del modelo.
        # Asumo que 'creado_en' es un campo real o que tu intención era usar '-dia_predicho'
        predicciones = PrediccionTomate.objects.filter(user_id=user_id).order_by('-creado_en')

        serializer = PrediccionTomateSerializer(predicciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)