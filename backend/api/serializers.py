from django.core.validators import MinValueValidator
from django.db import transaction
from django.forms import ValidationError
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.constants import MIN_COOKING_TIME, MIN_INGEDIENT_AMOUNT
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers, validators
from rest_framework.validators import UniqueValidator
from users.constants import (MAX_EMAIL_LENGTH, MAX_NAME_LENGTH,
                             MIN_USERNAME_LENGTH_API)
from users.models import Subscription, User
from users.validators import username_validator


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей"""

    email = serializers.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Такая электронная почта уже зарегистрирована",
            ),
        ],
    )
    username = serializers.CharField(
        min_length=MIN_USERNAME_LENGTH_API,
        max_length=MAX_NAME_LENGTH,
        validators=(
            username_validator,
            UniqueValidator(
                queryset=User.objects.all(),
                message="Такое имя логина уже занято",
            ),
        ),
    )
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "email", "id", "username", "first_name", "last_name", "password"
        )


class CustomUserSerializer(UserSerializer):
    """Сериализатор для пользователей (модель User)"""

    username = serializers.CharField(
        min_length=MIN_USERNAME_LENGTH_API,
        max_length=MAX_NAME_LENGTH,
        validators=(username_validator,),
    )
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None:
            return False
        current_user = request.user
        return (
            current_user.is_authenticated
            and current_user != obj
            and current_user.subscriptions.filter(author=obj).exists()
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписчиков (модель Subscription)"""

    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username",
        default=serializers.CurrentUserDefault(),
    )
    author = serializers.SlugRelatedField(
        slug_field="username",
        queryset=User.objects.all(),
    )

    class Meta:
        model = Subscription
        fields = ("user", "author",)

        validators = (
            validators.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=("user", "author"),
                message=("Вы уже подписаны на данного автора!"),
            ),
        )

    def validate_author(self, value):
        if self.context["user"] == value:
            raise serializers.ValidationError(
                detail="Нельзя подписаться на самого себя!",
            )
        return value

    def to_representation(self, instance):
        return UserRecipeSerializer(
            instance.author,
            context=self.context,
        ).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов (модель Tag)"""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов (модель Ingredient)"""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class ReceipeIngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов рецепта"""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount", "measurement_unit", "name")


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов при создании рецепта"""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient"
    )
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                MIN_INGEDIENT_AMOUNT,
                message="Количество ингредиента должно быть больше 0",
            ),
        )
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class ShortInfoRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор краткого просмотра рецептов"""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов"""

    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = ReceipeIngredientGetSerializer(
        many=True, source="recipe_ingredients"
    )
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        default=False, read_only=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и изменения рецептов"""

    ingredients = RecipeIngredientCreateSerializer(
        required=True,
        many=True,
        source="recipe_ingredients"
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                MIN_COOKING_TIME, message="Ошибка времени приготовления!"
            ),
        )
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def validate(self, value):
        if not value.get("recipe_ingredients"):
            raise serializers.ValidationError("Добавьте хотя бы 1 ингредиент")
        if not value.get("tags"):
            raise serializers.ValidationError("Добавьте хотя бы 1 тег")
        return value

    def validate_ingredients(self, value):
        ingredients = [ingredient["ingredient"] for ingredient in value]
        if len(set(ingredients)) != len(ingredients):
            raise serializers.ValidationError(
                "Ингредиенты повторяются!"
            )
        return value

    def validate_tags(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Теги повторяются!")
        return value

    def validate_image(self, image):
        if image is None:
            raise serializers.ValidationError("Фото блюда обязательно!")
        return image

    def create(self, validated_data):
        ingredients = validated_data.pop("recipe_ingredients")
        tags = validated_data.pop("tags")
        with transaction.atomic():
            recipe = Recipe.objects.create(
                author=self.context["request"].user, **validated_data
            )
            self.add_tags_ingredients(recipe, tags, ingredients)
            return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("recipe_ingredients")
        tags = validated_data.pop("tags")
        with transaction.atomic():
            instance.ingredients.clear()
            instance.tags.clear()
            self.add_tags_ingredients(instance, tags, ingredients)
            super().update(instance, validated_data)
            return instance

    @staticmethod
    def add_tags_ingredients(recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient["ingredient"],
                amount=ingredient["amount"],
            )
            for ingredient in ingredients
        )

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class UserRecipeSerializer(CustomUserSerializer):
    """Сериализатор для рецептов пользователей (модель User)"""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        read_only=True, source="recipes.count"
    )

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes = obj.recipes.all()
        try:
            recipes_limit = int(request.query_params.get("recipes_limit"))

        except (ValueError, TypeError):
            pass
        else:
            recipes = recipes[:recipes_limit]

        return ShortInfoRecipeSerializer(recipes, many=True).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов в избранном"""

    class Meta:
        model = Favorite
        fields = ("user", "recipe")
        read_only_fields = ("user",)

    def validate(self, attrs):
        recipe = attrs["recipe"]
        user = self.context["request"].user
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Рецепт уже добавлен в избранное"
            )
        return attrs

    def to_representation(self, instance):
        return ShortInfoRecipeSerializer(
            instance.recipe, context=self.context
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов в списке покупок"""

    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")
        read_only_fields = ("user",)

    def validate(self, attrs):
        recipe = attrs["recipe"]
        user = self.context["request"].user
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Рецепт уже добавлен в список рецептов"
            )
        return attrs

    def to_representation(self, instance):
        return ShortInfoRecipeSerializer(
            instance.recipe, context=self.context
        ).data


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор модели User для смены пароля."""

    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = User
        write_only = ("new_password", "current_password")

    def validate(self, data):
        if not self.context["request"].user.check_password(
            data.get("current_password")
        ):
            raise ValidationError(
                {"current_password": "Неверный пароль"}
            )
        if data.get("current_password") == data.get("new_password"):
            raise ValidationError(
                {"new_password": "Новый пароль совпадает с предыдущим!"}
            )
        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance
