from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Usuario
from accounts.serializers import RegistroUsuarioSerializer, LoginUsuarioSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from accounts.utilities.utils import enviar_otp_mail
from django.utils import timezone

# Create your views here.

class RegistroUsuarioView(APIView):
    def post(self, request):
        serializer = RegistroUsuarioSerializer(data=request.data)
        usuario = None
        if serializer.is_valid():
            usuario = serializer.save()

            # Generar el codigo OTP y enviarlo por correo
            print(f"Codigo OTP: {usuario.otp_codigo}")

            try:
                enviar_otp_mail(usuario)
            except Exception as e:
                return Response({"error": f"No se pudo enviar el OTP por Correo Electrónico: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # Regresamos una respuesta
            return Response({"mensaje": "Usuario registrado. Revisa tu Correo Electrónico"},
                     status=status.HTTP_201_CREATED)
            # return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View en accounts
class ActivarUsuarioView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        # Verificar que los parametros traigain información
        if not email or not otp:
            return Response(
                {'Error': 'Se requiere email y codigo otp'},
                    status = status.HTTP_400_BAD_REQUEST
            )
        # Verificar si existe el usuario
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response(
                {"error":"Usuario no existe"},
                status=status.HTTP_404_NOT_FOUND
            )
        # Validar el código OTP
        if usuario.otp_codigo != otp:
            return Response(
                {"error":"El código de OTP no es correcto"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Validar el tiempo del tiempo otp
        tiempo_expiracion= usuario.otp_creado_en + timezone.timedelta(minutes=15)
        if timezone.now() > tiempo_expiracion:
            return Response(
                {"error":"Código Otp ha expirado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        #Activar Usuario
        usuario.is_active = True
        usuario.otp_codigo = None
        usuario.save()
        return Response(
            {"message":"Cuenta activada correctamente. Ya puedes iniciar sesión"},
            status=status.HTTP_200_OK
        )

class LoginView(APIView):
    permission_classes = []
    def post(self, request):
        serializer = LoginUsuarioSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                serializer.validated_data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class LogoutView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if refresh_token is None:
            return Response({
                "error": "Se requiere refresh token"
            },
            status = status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Logged out exitoso"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Ocurrió un error: {str(e)}"},
                     status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                {"message": "  Se envió un codigo para recuperar la contraseña"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Contraseña restablecida correctamente"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditarPerfilUsuarioView(APIView):
    def patch(self, request):
        usuario = request.user   # Usuario autenticado por JWT

        # Extraer datos opcionales
        nombre_usuario = request.data.get("nombre_usuario")
        pais = request.data.get("pais")
        bio = request.data.get("bio")
        # Validaciones
        errores = {}

        if nombre_usuario is not None:
            if nombre_usuario.strip() == "":
                errores["nombre_usuario"] = "El nombre de usuario no puede estar vacío."
            elif len(nombre_usuario) > 255:
                errores["nombre_usuario"] = "Máximo 255 caracteres."

        if pais is not None:
            if pais.strip() == "":
                errores["pais"] = "El país no puede estar vacío."
            elif len(pais) > 20:
                errores["pais"] = "Máximo 20 caracteres."

        if bio is not None:
            if len(bio) > 255:
                errores["bio"] = "La bio/descripcion debe tener máximo 255 caracteres."

        if errores:
            return Response({"errores": errores}, status=status.HTTP_400_BAD_REQUEST)

        # Guardar solo los campos enviados
        if nombre_usuario is not None:
            usuario.nombre_usuario = nombre_usuario

        if pais is not None:
            usuario.pais = pais or ""   # acepta string vacío a propósito

        if bio is not None:
            usuario.bio = bio or ""

        usuario.save()

        return Response({
            "mensaje": "Perfil actualizado correctamente.",
            "perfil": {
                "email": usuario.email,
                "nombre_usuario": usuario.nombre_usuario,
                "pais": usuario.pais or "",
                "bio": usuario.bio or "",
            }
        }, status=status.HTTP_200_OK)



class DatosDeUsuarioView(APIView):

    def get(self, request):
        usuario = request.user

        return Response({
            "email": usuario.email,
            "nombre_usuario": usuario.nombre_usuario,
            "pais": usuario.pais or "",
            "bio": usuario.bio or "",
            "telefono_celular": usuario.telefono_celular,
            "id": str(usuario.id),
        }, status=status.HTTP_200_OK)