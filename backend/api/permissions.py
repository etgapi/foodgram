from rest_framework.permissions import SAFE_METHODS, BasePermission


class AdminOrReadOnly(BasePermission):
    """Пермишн с правами доступа для админа"""

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS or request.user
            and request.user.is_superuser
        )


class AuthorOrReadOnly(BasePermission):
    """Пермишн с правами доступа для авторов"""

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or request.user == obj.author


class AdminOrAuthor(BasePermission):
    """Пермишн с правами доступа для админа и авторов"""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user == obj.author
            or request.user.is_superuser
        )
