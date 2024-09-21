from django.contrib import admin
from django.utils.html import format_html

from .constants import MIN_INGEDIENT_AMOUNT
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    list_display_links = ("name", "slug")
    search_fields = ("name", "slug")


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
    )
    list_display_links = ("name",)
    search_fields = ("name",)
    search_help_text = "Поиск по названию ингредиента"
    list_filter = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = MIN_INGEDIENT_AMOUNT


class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "in_favorites")
    list_display_links = ("name", "author")
    search_fields = ("name", "author__username", "ingredients__name")
    search_help_text = "Поиск по названию рецепта или имени пользователя"
    filter_horizontal = ("tags", "ingredients")
    list_filter = ("tags",)
    readonly_fields = ("in_favorites",)
    inlines = (RecipeIngredientInline,)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "author",
                    ("name", "cooking_time", "in_favorites"),
                    "text",
                    "image",
                    "tags",
                )
            },
        ),
    )

    @admin.display(
        description=format_html(
            "<strong>Число добавлений рецепта в избранное</strong>"
        )
    )
    def in_favorites(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


class FavoriteAdmin(admin.ModelAdmin):

    list_display = ("id", "__str__")
    list_display_links = ("id", "__str__")


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "__str__")
    list_display_links = ("id", "__str__")


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
