# apps/authentication/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('verify-token/', views.verify_token, name='verify_token'),
]