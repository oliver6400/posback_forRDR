from rest_framework.permissions import BasePermission


ROLE_SUPERADMIN = "SuperAdmin"
ROLE_ADMIN = "Admin"
ROLE_SUPERVISOR = "Supervisor"
ROLE_CAJERO = "Cajero"


def _role_name(user):
    role = getattr(user, "rol", None)
    return (getattr(role, "nombre", "") or "").strip().lower()


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and _role_name(request.user) == ROLE_SUPERADMIN.lower())


class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and _role_name(request.user) in {ROLE_SUPERADMIN.lower(), ROLE_ADMIN.lower()}
        )


class IsSupervisorOrHigher(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and _role_name(request.user)
            in {ROLE_SUPERADMIN.lower(), ROLE_ADMIN.lower(), ROLE_SUPERVISOR.lower()}
        )
