# apps/reportes/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LogAuditoriaViewSet, ArqueoCajaViewSet, AnaliticaVentasViewSet
router = DefaultRouter()
router.register(r'logauditoria', LogAuditoriaViewSet)
router.register(r'arqueocaja', ArqueoCajaViewSet)
router.register(r'analitica-ventas', AnaliticaVentasViewSet, basename='analitica-ventas')

urlpatterns = [
    path('', include(router.urls)),
]
