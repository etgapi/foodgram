from django.contrib import admin
from django.utils.html import format_html

from .models import (
    IngredientsAmount, Favorite, Ingredient, Recipe, ShoppingCart, Tag
)


class OtherAdmin(admin.ModelAdmin):
    pass


class IngredientInRecipe(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 10
    min_num = 1


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    search_help_text = 'Поиск по названию ингредиента'
    list_filter = ("name",)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_display_links = ('name', 'author')
    search_fields = ('name', 'author__username')
    search_help_text = 'Поиск по названию рецепта или имени пользователя'
    filter_horizontal = ('tags',)
    list_filter = ('tags',)
    readonly_fields = ('in_favorites',)
    inlines = (IngredientInRecipe,)

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'author',
                    ('name', 'cooking_time', 'in_favorites'),
                    'text',
                    'image',
                    'tags',
                )
            },
        ),
    )

    @admin.display(
        description=format_html(
            '<strong>Число добавлений рецепта в избранное</strong>'
            )
    )
    def in_favorites(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "recipe",
    )
    list_filter = ("user",)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "recipe",
        "__str__"
        
    )
    list_display_links = (
        "user",
        "recipe",
        "__str__"
        
    )
    list_filter = ("user",)


admin.site.register(Tag, OtherAdmin)
admin.site.register(IngredientsAmount, OtherAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
