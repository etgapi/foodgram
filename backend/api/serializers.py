from django.shortcuts import get_object_or_404

from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    CharField,
    EmailField,
    Field,
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    SerializerMethodField,
    ValidationError
)

from recipes.models import (Ingredient, IngredientsAmount, Recipe, Tag)
from users.models import User

MIN_VALUE = 0
MAX_VALUE = 32000


class UserAvatarSerializer(UserSerializer):
    """Сериализатор для аватара пользователя"""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей"""

    username = CharField(max_length=150)
    email = EmailField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {"password": {"write_only": True}}


class UsersSerializer(UserSerializer):
    """Сериализатор пользователz"""

    is_subscribed = SerializerMethodField()

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
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.following.filter(user=user).exists()
        return False


class TagSerializer(ModelSerializer):
    """Сериализатор для тэгов"""

    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(ModelSerializer):
    """Сериализатор для ингредиентов"""

    class Meta:
        model = Ingredient
        fields = "__all__"


class IngredientCreateSerializer(ModelSerializer):
    """Сериализатор для добавления ингредиентов при создании рецепта"""

    id = IntegerField()

    class Meta:
        model = IngredientsAmount
        fields = ("id", "amount",)

    def validate_amount(self, amount):
        if amount <= MIN_VALUE:
            raise ValidationError(
                'Количество ингредиентов должно быть больше 0'
            )
        if amount > MAX_VALUE:
            raise ValidationError(
                'Количество ингредиентов не должно превышать 32000'
            )
        return amount


class ReadIngredientsInRecipeSerializer(ModelSerializer):
    """Сериализатор для чтения ингредиентов в рецепте"""

    id = ReadOnlyField(source="ingredient.id")
    name = ReadOnlyField(source="ingredient.name")
    measurement_unit = ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = IngredientsAmount
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


class RecipeSerializer(ModelSerializer):
    """Сериализатор для рецептов"""

    author = UsersSerializer(read_only=True)
    ingredients = SerializerMethodField()
    tags = TagSerializer(many=True)
    is_favorited = SerializerMethodField()
    image = Base64ImageField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "tags",
            "is_favorited",
            "name",
            "image",
            "text",
            "cooking_time",
            'is_in_shopping_cart',
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.shopping_cart.filter(user=user).exists()
        return False

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.favorite.filter(user=user).exists()
        return False

    def get_ingredients(self, obj):
        ingredients = obj.ingredient_amount.filter(recipe=obj)
        return ReadIngredientsInRecipeSerializer(ingredients, many=True).data


class RecipeCreateSerializer(ModelSerializer):
    """Сериализатор для создания рецептов"""

    ingredients = IngredientCreateSerializer(many=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()
    name = CharField(max_length=200)
    cooking_time = IntegerField()
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
            "author",
        )

    def create_ingredients_amounts(self, recipe, ingredients):
        ingredients_amounts = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, id=ingredient.get("id")
            )
            ingredients_amounts.append(IngredientsAmount(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient.get("amount")
            ))
        IngredientsAmount.objects.bulk_create(ingredients_amounts)

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients_amounts(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        IngredientsAmount.objects.filter(recipe=recipe).delete()
        self.create_ingredients_amounts(recipe, ingredients)
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)

    def to_representation(self, recipe):
        data = RecipeSerializer(
            recipe, context={"request": self.context.get("request")}
        ).data
        return data

    def validate_cooking_time(self, cooking_time):
        if cooking_time <= MIN_VALUE:
            raise ValidationError(
                'Время приготовления должно быть больше 0'
            )
        if cooking_time > MAX_VALUE:
            raise ValidationError(
                'Время приготовления должно быть не больше 32000'
            )
        return cooking_time


class RecipeFollowerSerializer(ModelSerializer):
    """Сериализатор для рецептов в избранном"""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class RecipeFollowUser(Field):
    """Сериализатор для рецептов в подписках"""

    def get_attribute(self, instance):
        return instance.author.recipes.all()

    def to_representation(self, recipes_list):
        recipes_data = []
        for recipe in recipes_list:
            recipes_data.append(
                {
                    "id": recipe.id,
                    "name": recipe.name,
                    "image": recipe.image.url,
                    "cooking_time": recipe.cooking_time,
                }
            )
        return recipes_data


class FollowSerializer(ModelSerializer):
    """Сериализатор для подписок"""

    recipes = RecipeFollowUser()
    recipes_count = SerializerMethodField(read_only=True)
    id = ReadOnlyField(source="author.id")
    email = ReadOnlyField(source="author.email")
    username = ReadOnlyField(source="author.username")
    first_name = ReadOnlyField(source="author.first_name")
    last_name = ReadOnlyField(source="author.last_name")
    is_subscribed = SerializerMethodField()

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
        )

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_is_subscribed(self, obj):
        return obj.author.follower.filter(user=obj.user).exists()
