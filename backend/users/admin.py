from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.models import Group

from .models import Subscription, User


class UserAdmin(AuthUserAdmin):

    list_display_links = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    search_help_text = "Поиск по указанным полям"
    list_filter = (
        "username", "email", "is_staff", "is_superuser", "is_active"
    )


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "author",
    )


admin.site.register(User, UserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
# Удаляем из админки вкладку "Группы"
admin.site.unregister(Group)
