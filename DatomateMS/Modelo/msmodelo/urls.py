from django.contrib import admin
from django.urls import path, include

from django.urls import path
from appmodelo.views import PrediccionTomateViewSet

# Creamos la vista basada en la acción del ViewSet
prediccion_view = PrediccionTomateViewSet.as_view({'get': 'predecir'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('appmodelo.urls')),
]

