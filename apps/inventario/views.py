from django.db.models import F
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, filters
from rest_framework.exceptions import APIException
from django.db import IntegrityError

from .models import (
    Producto, InventarioSucursal,
    MovimientoInventario, MovimientoInventarioDetalle,
    ImagenProducto,
)
from .serializers import (
    ProductoSerializer, InventarioSucursalSerializer,
    MovimientoInventarioSerializer,
    ImagenProductoSerializer, MovimientoInventarioDetalleSerializer
)


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [filters.SearchFilter]
    search_fields = ['codigo_barras', 'codigo', 'nombre'] 

class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all().order_by("-fecha_hora")
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAuthenticated]

class InventarioSucursalViewSet(viewsets.ModelViewSet):
    queryset = InventarioSucursal.objects.all()
    serializer_class = InventarioSucursalSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def bajo_stock(self, request):
        """Listar productos con stock menor al mínimo"""
        qs = InventarioSucursal.objects.filter(stock_actual__lt=F('stock_minimo'))
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError as e:
            raise APIException(f"Error de integridad en la base de datos: {str(e)}")
        except ValidationError as e:
            raise APIException(f"Error de validación: {str(e)}")

    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError as e:
            raise APIException(f"Error de integridad en la base de datos: {str(e)}")
        except ValidationError as e:
            raise APIException(f"Error de validación: {str(e)}")

class ImagenProductoViewSet(viewsets.ModelViewSet):
    queryset = ImagenProducto.objects.all()
    serializer_class = ImagenProductoSerializer
    permission_classes = [IsAuthenticated]

class MovimientoInventarioDetalleViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventarioDetalle.objects.all()
    serializer_class = MovimientoInventarioDetalleSerializer
    permission_classes = [IsAuthenticated]
