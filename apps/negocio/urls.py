from rest_framework_nested import routers
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClienteViewSet, SucursalViewSet, PuntoVentaViewSet
    , EstadoVentaViewSet, CiudadViewSet,
    ClienteListView
)

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'sucursales', SucursalViewSet)
router.register(r'puntos-venta', PuntoVentaViewSet, basename='puntos-venta')
router.register(r'estados-venta', EstadoVentaViewSet)
router.register(r'ciudades', CiudadViewSet)
router.register(r'cliente-list', ClienteListView, basename='cliente-list')

# rutas anidadas
sucursal_router = routers.NestedSimpleRouter(router, r'sucursales', lookup='sucursal')
sucursal_router.register(r'puntos-venta', PuntoVentaViewSet, basename='sucursal-puntos-venta')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(sucursal_router.urls)),
]