
from django.urls import path

from accounts.views import RegistroUsuarioView, ActivarUsuarioView, DatosDeUsuarioView, EditarPerfilUsuarioView, LoginView, LogoutView, ForgotPasswordView, ResetPasswordView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns  = [
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('activar/', ActivarUsuarioView.as_view(), name='activar'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('forgot/', ForgotPasswordView.as_view(), name='forgot'),
    path('reset/', ResetPasswordView.as_view(), name='reset'),
    path('editarPerfil/', EditarPerfilUsuarioView.as_view(), name='editarPerfil'),
    path('datosUsuario/', DatosDeUsuarioView.as_view(), name='datosUsuario'),
]