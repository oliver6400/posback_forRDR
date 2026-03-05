from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.usuarios.models import Rol, Usuario


class UsuariosPermisosTests(APITestCase):
    def setUp(self):
        self.rol_superadmin = Rol.objects.create(nombre="SuperAdmin")
        self.rol_admin = Rol.objects.create(nombre="Admin")
        self.rol_supervisor = Rol.objects.create(nombre="Supervisor")
        self.rol_cajero = Rol.objects.create(nombre="Cajero")

        self.superadmin = Usuario.objects.create_user(
            username="root",
            ci="1",
            email="root@example.com",
            nombre="Root",
            apellido="User",
            fecha_nacimiento="1990-01-01",
            password="test12345",
            rol=self.rol_superadmin,
        )
        self.admin = Usuario.objects.create_user(
            username="admin1",
            ci="2",
            email="admin@example.com",
            nombre="Admin",
            apellido="User",
            fecha_nacimiento="1991-01-01",
            password="test12345",
            rol=self.rol_admin,
        )

    def test_admin_no_puede_crear_otro_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("usuario-list")
        payload = {
            "username": "admin2",
            "ci": "3",
            "email": "admin2@example.com",
            "nombre": "Admin",
            "apellido": "Dos",
            "fecha_nacimiento": "1992-01-01",
            "password": "test12345",
            "rol_id": self.rol_admin.id,
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_si_puede_crear_cajero(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("usuario-list")
        payload = {
            "username": "caja1",
            "ci": "4",
            "email": "caja1@example.com",
            "nombre": "Caja",
            "apellido": "Uno",
            "fecha_nacimiento": "1993-01-01",
            "password": "test12345",
            "rol_id": self.rol_cajero.id,
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_solo_superadmin_gestiona_roles(self):
        url = reverse("rol-list")

        self.client.force_authenticate(user=self.admin)
        response_admin = self.client.get(url)
        self.assertEqual(response_admin.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.superadmin)
        response_superadmin = self.client.get(url)
        self.assertEqual(response_superadmin.status_code, status.HTTP_200_OK)
