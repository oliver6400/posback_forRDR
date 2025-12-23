from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProductoViewSet, InventarioSucursalViewSet, 
    MovimientoInventarioViewSet, MovimientoInventarioDetalleViewSet,
    ImagenProductoViewSet, 
)

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'imagenes-producto', ImagenProductoViewSet)
router.register(r'inventarios', InventarioSucursalViewSet)
router.register(r'movimientos', MovimientoInventarioViewSet)
router.register(r'movimientos-detalle', MovimientoInventarioDetalleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]