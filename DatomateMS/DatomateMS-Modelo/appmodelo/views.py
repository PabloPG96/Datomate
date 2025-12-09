import requests
import numpy as np
import threading
import grpc
import tensorflow as tf
from datetime import datetime, timedelta

from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Importaciones específicas de gRPC y TF Serving
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc

from .models import PrediccionTomate
from .serializers import PrediccionTomateSerializer

# ------------------------------
# Configuración gRPC
# ------------------------------
TF_SERVING_HOST = 'localhost:8500'  # IP del contenedor Docker
MODEL_NAME = 'tomates'  # Nombre definido en el comando docker run
SIGNATURE_NAME = 'serving_default'  # Firma por defecto

HISTORICO_MS_URL = "http://127.0.0.1:6000/api/v1/historico/"


def ejecutar_prediccion_async(user_id, lecturas_invertidas, resultado, dia_siguiente):
    """
    Guarda la predicción en la base de datos en segundo plano
    para no bloquear la respuesta al usuario.
    """
    try:
        PrediccionTomate.objects.create(
            user_id=user_id,
            dia_predicho=dia_siguiente.date(),
            produccion_predicha_kg=abs(resultado),
            dias_usados=[l["created_at"] for l in lecturas_invertidas]
        )
        print(f"✅ Predicción guardada para usuario {user_id}")
    except Exception as e:
        print(f"❌ Error guardando predicción async: {e}")


class PrediccionTomateViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='predecir')
    def predecir(self, request):
        user_id = request.user.id
        token = request.auth
        headers = {"Authorization": f"Bearer {token}"}

        # ------------------------------------------------
        # 1. Obtener datos del histórico
        # ------------------------------------------------
        try:
            response = requests.get(HISTORICO_MS_URL, headers=headers, timeout=40)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error conexión histórico: {e}")
            return Response({"error": "No se pudo conectar al microservicio histórico."}, status=502)

        historicos = response.json()
        if not historicos or len(historicos) < 5:
            return Response(
                {"error": f"Se requieren al menos 5 registros. Solo hay {len(historicos) if historicos else 0}."},
                status=400)

        # ------------------------------------------------
        # 2. Procesar datos (CORREGIDO EL ORDEN)
        # ------------------------------------------------
        # Tomamos los últimos 5 cronológicamente
        lecturas = sorted(historicos, key=lambda x: x["created_at"])[-5:]
        # Invertimos si tu lógica lo requiere (revisa si el modelo espera t-5, t-4... o t-1, t-2...)
        # Asumiré orden cronológico normal (del más antiguo al más nuevo de esos 5) para LSTM
        # Si tu modelo se entrenó con los datos invertidos, mantén el reversed.
        lecturas_procesar = list(lecturas)

        try:
            # ¡OJO AQUÍ! El orden debe ser EXACTAMENTE el mismo que en features_list del entrenamiento:
            # features_list = ['Temp_Media', 'Humedad_Media', 'Longitud_Tallo', 'Diametro_Tallo']
            datos = np.array([
                [
                    float(l["Temp_Media"]),  # 1. Temperatura
                    float(l["Humedad_Media"]),  # 2. Humedad
                    float(l["Longitud_Tallo"]),  # 3. Longitud
                    float(l["Diametro_Tallo"])  # 4. Diámetro
                ]
                for l in lecturas_procesar
            ], dtype=np.float32)
        except KeyError as e:
            return Response({"error": f"Datos incompletos en histórico: {str(e)}"}, status=500)

        # Reshape: (Batch_Size=1, Pasos_Tiempo=5, Features=4)
        entrada = datos.reshape(1, 5, 4)

        # ------------------------------------------------
        # 3. PREDICCIÓN VÍA gRPC (TENSORFLOW SERVING)
        # ------------------------------------------------
        try:
            channel = grpc.insecure_channel(TF_SERVING_HOST)
            stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

            request_grpc = predict_pb2.PredictRequest()
            request_grpc.model_spec.name = MODEL_NAME
            request_grpc.model_spec.signature_name = SIGNATURE_NAME

            # --- NOMBRE DE LA ENTRADA ---
            # Basado en tu código de entrenamiento: name="datos_normales_de_entrada"
            # Si Docker te da error, usa 'saved_model_cli' para ver el nombre real (ej: 'serving_default_datos_normales_de_entrada')
            INPUT_NAME = 'datos_normales_de_entrada'

            request_grpc.inputs[INPUT_NAME].CopyFrom(
                tf.make_tensor_proto(entrada, shape=entrada.shape)
            )

            result_grpc = stub.Predict(request_grpc, 10.0)

            # Extraer resultado
            output_key = list(result_grpc.outputs.keys())[0]
            pred_proto = result_grpc.outputs[output_key]
            resultado = float(tf.make_ndarray(pred_proto)[0][0])

        except grpc.RpcError as e:
            print(f"Error gRPC: {e.details()}")
            return Response(
                {"error": "El servicio de IA no está disponible en este momento."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            print(f"Error procesando predicción: {e}")
            # Si falla el nombre de la entrada, aquí caerá el error
            if 'KeyError' in str(e) or 'not found' in str(e).lower():
                return Response(
                    {"error": f"Error de configuración del modelo (Nombre de entrada incorrecto: {INPUT_NAME})"},
                    status=500)
            return Response({"error": str(e)}, status=500)

        # ------------------------------------------------
        # 4. Guardar Async y Responder
        # ------------------------------------------------
        ultimo_dia = datetime.fromisoformat(lecturas[-1]["created_at"].replace("Z", ""))
        dia_siguiente = ultimo_dia + timedelta(days=1)

        threading.Thread(
            target=ejecutar_prediccion_async,
            args=(user_id, lecturas, resultado, dia_siguiente)
        ).start()

        return Response({
            "usuario": str(user_id),
            "dia_predicho": dia_siguiente.strftime("%Y-%m-%d"),
            "produccion_predicha_kg": round(abs(resultado), 5),
            "mensaje": "Predicción generada exitosamente con IA."
        }, status=status.HTTP_200_OK)


# ============================================================
# CLASE PARA LISTAR
# ============================================================

class ListarPrediccionesViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user_id = request.user.id

        predicciones = PrediccionTomate.objects.filter(
            user_id=user_id
        ).order_by('-creado_en')

        serializer = PrediccionTomateSerializer(predicciones, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)