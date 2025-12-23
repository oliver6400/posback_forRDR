from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LogAuditoriaViewSet, ArqueoCajaViewSet
router = DefaultRouter()
router.register(r'logauditoria', LogAuditoriaViewSet)
router.register(r'arqueocaja', ArqueoCajaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
