from django.urls import path
from appmodelo.views import PrediccionTomateViewSet, ListarPrediccionesViewSet

prediccion_view = PrediccionTomateViewSet.as_view({'get': 'predecir'})
predicciones_view = ListarPrediccionesViewSet.as_view({'get': 'list'})

urlpatterns = [
    path('predecir/', prediccion_view, name='predecir'),
    path('predicciones/', predicciones_view, name='predicciones')
]
