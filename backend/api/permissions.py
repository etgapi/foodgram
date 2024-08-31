from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Пермишн с правами доступа для админа"""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
            or request.user.is_staff
        )


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Пермишн с правами доступа для авторов"""

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or request.user == obj.author
