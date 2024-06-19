from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

from .models import Follow, User


class UserAdmin(AuthUserAdmin):

    list_display_links = (
        'username',
        'email'
    )
    search_help_text = 'Поиск по указанным полям'
    list_filter = (
        'username', 'email', 'is_staff', 'is_superuser', 'is_active'
    )


class FollowAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "user",
    )
    search_fields = (
        "user",
        "author",
    )


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
