from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse, HttpResponseRedirect

from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from django.utils import baseconv
from djoser import views as djoser_views
from rest_framework import permissions, serializers, status, validators, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientFilter
from api.permissions import IsAuthorOrReadOnly
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription

from .filters import RecipeFilter, IngredientFilter
from .pagination import LimitPagePagination
from .serializers import (
    CustomUserCreateSerializer,
    CustomUserSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeIngredient,
    RecipeSerializer,
    SetPasswordSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserRecipeSerializer,
)

User = get_user_model()


class UserViewSet(djoser_views.UserViewSet):
    """Вьюсет для модели пользователей"""

    pagination_class = LimitPagePagination
    permission_classes = (permissions.AllowAny,)


    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomUserCreateSerializer
        if self.request.method == 'GET':
            return CustomUserSerializer

    def get_queryset(self):
        if self.action == "subscriptions":
            return Subscription.objects.filter(subscriber=self.request.user)
        return User.objects.all()

    @action(
        methods=("get",),
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)
    
    @action(
        ['POST'],
        detail=False,
        permission_classes=[IsAuthenticated, ]
    )
    def set_password(self, request, *args, **kwargs):
        user = request.user
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        serializer.update(
            instance=self.request.user,
            validated_data=serializer.validated_data
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.data["new_password"])
        user.save()
        return Response(
            'Пароль успешно изменен',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        methods=("put",),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path="me/avatar",
        url_name="me-avatar",
    )
    def avatar(self, request):
        if "avatar" not in request.data:
            return Response(
                "Необходимо добавить аватар",
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = CustomUserSerializer(
            self.get_instance(), data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar = None
        user.save()
        return Response(
            "Аватар удален",
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        methods=("get",),
        detail=False,
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscriptionSerializer,
    )
    def subscriptions(self, request):
        paginate_queryset = self.paginate_queryset(self.get_queryset())
        serializer = SubscriptionSerializer(
            paginate_queryset, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=("post",),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionSerializer(
            data={"author": author},
            context={
                "user": request.user,
                "request": request
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(author=author, subscriber=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        subscriptions_deleted, _ = Subscription.objects.filter(
            author=author, subscriber=request.user
        ).delete()
        if subscriptions_deleted == 0:
            return Response(
                {"errors": "Отсутствуют подписки на данного автора!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели тегов"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели ингредиентов"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов"""

    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = LimitPagePagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeSerializer
        elif self.action == "favorite":
            return FavoriteSerializer
        elif self.action == "shopping_cart":
            return ShoppingCartSerializer
        return RecipeCreateUpdateSerializer

    def get_permissions(self):
        if self.action == "list":
            return (permissions.AllowAny(),)
        if self.action == "create":
            return (permissions.IsAuthenticated(),)
        if self.action in ("delete", "destroy", "update", "partial_update"):
            return (IsAuthorOrReadOnly(),)
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        recipes = Recipe.objects
        if self.action in (
            "list",
            "retrieve",
        ):
            recipes = (
                recipes.select_related("author")
                .prefetch_related(
                    "recipe_ingredients__ingredient",
                    "recipe_ingredients",
                    "tags",
                    "author__subscribers",
                )
                .annotate(
                    is_in_shopping_cart=Exists(
                        ShoppingCart.objects.filter(
                            author_id=user.id, recipe=OuterRef("pk")
                        )
                    ),
                    is_favorited=Exists(
                        Favorite.objects.filter(
                            author_id=user.id, recipe=OuterRef("pk")
                        )
                    ),
                )
                .all()
            )

        return recipes.order_by("-creation_date").all()

    def _post_recipe(self, request, pk):
        get_object_or_404(Recipe, pk=pk)
        serializer = self.get_serializer(data=dict(recipe=pk))
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_recipe(self, request, pk, model):
        recipe = get_object_or_404(Recipe, pk=pk)
        amount_deleted, _ = model.objects.filter(
            author=self.request.user,
            recipe=recipe,
        ).delete()

        if amount_deleted < 1:
            return Response(
                {"errors": "Такого рецепта не существует."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post"],
        detail=True,
        url_name="shopping-cart",
    )
    def shopping_cart(self, request, pk=None):
        return self._post_recipe(request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self._delete_recipe(request, pk, ShoppingCart)

    @action(
        methods=["post"],
        detail=True,
    )
    def favorite(self, request, pk=None):
        return self._post_recipe(request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self._delete_recipe(request, pk, Favorite)

    @action(
        detail=False,
        url_path="download_shopping_cart",
        methods=("get",),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_cart__author=request.user)
            .values(
                "ingredient__name",
                "ingredient__measurement_unit",
            )
            .order_by("ingredient__name")
            .annotate(total=Sum("amount"))
        )
        shopping_list = ["Список покупок\n"]
        shopping_list += [
            f'{ingredient["ingredient__name"]} - '
            f'{ingredient["total"]} '
            f'({ingredient["ingredient__measurement_unit"]})\n'
            for ingredient in ingredients
        ]
        response = HttpResponse(shopping_list, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        methods=["get"],
        detail=True,
        url_path="get-link",
        url_name="get-link",
        permission_classes=[
            AllowAny,
        ],
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        encoded_id = baseconv.base64.encode(str(recipe.id))
        short_link = request.build_absolute_uri(
            reverse("shortlink", kwargs={"encoded_id": encoded_id})
        )
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)


class ShortLinkView(APIView):
    def get(self, request, encoded_id):
        if not set(encoded_id).issubset(set(baseconv.BASE64_ALPHABET)):
            return Response(
                {"error": "Недопустимые символы в ссылке на рецепт"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe_id = baseconv.base64.decode(encoded_id)
        recipe = get_object_or_404(Recipe, id=recipe_id)
        return HttpResponseRedirect(request.build_absolute_uri(f"/recipes/{recipe.id}"))
