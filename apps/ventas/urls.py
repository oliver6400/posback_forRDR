from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VentaViewSet, FacturaSimuladaViewSet,
    DetalleVentaViewSet, MetodoPagoViewSet,
    VentaPagoViewSet
)

router = DefaultRouter()
router.register(r'ventas', VentaViewSet, basename="ventas")
router.register(r'detalles-venta', DetalleVentaViewSet, basename="detalles-venta")
router.register(r'facturas', FacturaSimuladaViewSet, basename="facturas")
router.register(r'metodos-pago', MetodoPagoViewSet, basename="metodos-pago")
router.register(r'pagos', VentaPagoViewSet, basename="pagos")
urlpatterns = [
    path('', include(router.urls)),
]
