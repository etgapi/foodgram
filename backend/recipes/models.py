from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from users.models import User

MIN_VALUE = 1
MAX_VALUE = 32000


class Tag(models.Model):
    """Модель для тегов"""

    name = models.CharField(
        "Тег",
        max_length=32,
        unique=True,
    )
    slug = models.SlugField(
        "Слаг",
        max_length=32,
        null=True,
        unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для ингредиентов"""

    name = models.CharField(
        "Ингредиент",
        max_length=128,
    )
    measurement_unit = models.CharField(
        "Единица измерения",
        max_length=64,
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} {self.measurement_unit}"


class Recipe(models.Model):
    """Модель рецептов"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта",
    )
    name = models.CharField(
        "Название",
        max_length=256,
    )
    image = models.ImageField(
        "Картинка",
    )
    text = models.TextField(
        "Описание",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Список ингредиентов",
        through="IngredientsAmount",
        related_name="recipes",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="Тег",
    )
    pub_date = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True,
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления (в минутах)",
        validators=[
            MinValueValidator(
                MIN_VALUE,
                message="Время приготовления должно быть больше 0"),
            MaxValueValidator(
                MAX_VALUE,
                message="Время приготовления должно быть не более 32000")
        ],
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)

    def __str__(self):
        return self.name


class IngredientsAmount(models.Model):
    """Модель количества ингредиентов"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="ingredient_amount",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
        related_name="ingredient_amount",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(
                MIN_VALUE,
                message="Количество ингредиентов должно быть больше 0"),
            MaxValueValidator(
                MAX_VALUE,
                message="Количество ингредиентов не должно быть больше 32000")
        ],
    )

    class Meta:
        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиентов"
        ordering = ("ingredient",)

    def __str__(self):
        return f"{self.amount} {self.ingredient}"


class Favorite(models.Model):
    """Модель списка избранного"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="favorite",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="favorite",
    )

    class Meta:
        verbose_name = "Список избранного"
        verbose_name_plural = "Список избранного"
        ordering = ("recipe",)
    
    def __str__(self):
        return f"{self.user} {self.recipe}"


class ShoppingCart(models.Model):
    """Модель списка покупок"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="shopping_cart",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="shopping_cart",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"
        ordering = ("recipe",)
    
    def __str__(self):
        return f"{self.user} {self.recipe}"
