from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from users.models import User

from recipes.constants import (INGREDIENT_MAX_LENGTH, MAX_COOKING_TIME,
                               MAX_INGEDIENT_AMOUNT, MAX_LENGTH,
                               MIN_COOKING_TIME, MIN_INGEDIENT_AMOUNT,
                               SLUG_MAX_LENGTH, TAG_MAX_LENGTH,
                               UNIT_MAX_LENGTH, URL_LENGTH)


class Tag(models.Model):
    """Модель для тегов"""

    name = models.CharField("Тег", max_length=TAG_MAX_LENGTH, unique=True)
    slug = models.SlugField("Слаг", max_length=SLUG_MAX_LENGTH, unique=True)

    class Meta:
        ordering = ("id",)
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для ингредиентов"""

    name = models.CharField(
        verbose_name="Название ингредиента", max_length=INGREDIENT_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения", max_length=UNIT_MAX_LENGTH
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="Такой ингредиент уже существует",
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    """Модель для рецепта"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )

    creation_date = models.DateTimeField("Создан", auto_now_add=True)

    name = models.CharField("Название", max_length=MAX_LENGTH)
    text = models.TextField("Процесс приготовления")
    image = models.ImageField("Картинка", upload_to="recipes/images/")
    tags = models.ManyToManyField(Tag, verbose_name="Теги")
    ingredients = models.ManyToManyField(
        Ingredient, verbose_name="Ингредиенты", through="RecipeIngredient"
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления в минутах",
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                "Время приготовления не менее " f"{MIN_COOKING_TIME} минут",
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                "Время приготовления не дольше " f"{MAX_COOKING_TIME} минут",
            ),
        ],
    )

    class Meta:
        ordering = ("-creation_date",)
        default_related_name = "recipes"
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель для ингредиента рецепта"""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name="Рецепт"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        "Количество ингредиента",
        validators=[
            MinValueValidator(
                MIN_INGEDIENT_AMOUNT,
                f"Значение должно быть не меньше {MIN_INGEDIENT_AMOUNT}",
            ),
            MaxValueValidator(
                MAX_INGEDIENT_AMOUNT,
                f"Значение должно быть не больше {MAX_INGEDIENT_AMOUNT}",
            ),
        ],
    )

    class Meta:
        default_related_name = "recipe_ingredients"
        constraints = [
            models.UniqueConstraint(
                fields=["ingredient", "recipe"],
                name="Ингредиенты не должны повторяться",
            )
        ]
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"

    def __str__(self):
        return (
            f"{self.ingredient}"
            " = {self.amount} "
            "{self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    """Модель списка избранного"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )

    recipe = models.ForeignKey(
        "recipes.Recipe", on_delete=models.CASCADE, verbose_name="Рецепт"
    )

    class Meta:
        default_related_name = "favorites"
        verbose_name = "Список избранного"
        verbose_name_plural = "Список избранного"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="Рецепт уже есть в избранном"
            )
        ]

    def __str__(self):
        return f"{self.recipe.name}" " в избранном у " f"{self.user.username}"


class ShoppingCart(models.Model):
    """Модель списка покупок"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )

    recipe = models.ForeignKey(
        "recipes.Recipe", on_delete=models.CASCADE, verbose_name="Рецепт"
    )

    class Meta:
        default_related_name = "shopping_cart"
        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="Рецепт уже в списке покупок"
            )
        ]

    def __str__(self):
        return (f"{self.recipe.name!r}" " в списке покупок "
                f"{self.user.username!r}")
