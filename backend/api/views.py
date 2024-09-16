from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import baseconv
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from djoser import views as djoser_views # type: ignore
from djoser.serializers import SetPasswordSerializer # type: ignore
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import permissions, status, viewsets # type: ignore
from rest_framework.decorators import action # type: ignore
from rest_framework.permissions import AllowAny, IsAuthenticated # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from users.models import Subscription

from api.filters import IngredientFilter
from api.permissions import IsAuthorOrReadOnly

from .filters import RecipeFilter
from .pagination import LimitPagePagination
from .serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                          IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeIngredient, RecipeSerializer,
                          ShortInfoRecipeSerializer, SubscriptionSerializer,
                          TagSerializer)

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
        if self.action == 'subscriptions':
            return Subscription.objects.filter(user=self.request.user)
        return User.objects.all()

    @action(
        methods=("get",),
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        methods=("put",),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path="me/avatar",
        url_name="me-avatar",
    )
    def avatar(self, request):
        if 'avatar' not in request.data:
            return Response(
                'Необходимо добавить фото!',
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = CustomUserSerializer(
            self.get_instance(), data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': serializer.data['avatar']},
            status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar = None
        user.save()
        return Response(
            'Аватар удален.',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        ["POST"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request, *args, **kwargs):
        user = request.user
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.data["new_password"])
        user.save()
        return Response(
            'Пароль успешно изменен.',
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
            paginate_queryset, many=True, context={'request': request}
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
            data={'author': author},
            context={
                'user': request.user,
                'request': request,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        subscription_deleted, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()
        if not subscription_deleted:
            return Response(
                {'errors': 'Вы не подписаны на данного автора!'},
                status=status.HTTP_400_BAD_REQUEST
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
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeSerializer
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
                            user_id=user.id, recipe=OuterRef("pk")
                        )
                    ),
                    is_favorited=Exists(
                        Favorite.objects.filter(
                            user_id=user.id, recipe=OuterRef("pk")
                        )
                    ),
                )
                .all()
            )

        return recipes.order_by("-creation_date").all()

    @action(
        methods=["post"],
        detail=True,
        url_name="shopping-cart",
    )
    def shopping_cart(self, request, pk=None):
        response = self.add_recipe(request, pk, ShoppingCart)
        if not response:
            return Response(
                'Рецепт уже добавлен в списоку покупок!',
                status=status.HTTP_400_BAD_REQUEST
            )
        return response

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        response = self.delete_recipe(request, pk, ShoppingCart)
        if response is False:
            return Response(
                'Рецепт не добавлен в список покупок!',
                status=status.HTTP_400_BAD_REQUEST
            )
        return response

    @action(
        methods=["post"],
        detail=True,
    )
    def favorite(self, request, pk=None):
        response = self.add_recipe(request, pk, Favorite)
        if response is False:
            return Response(
                'Рецепт уже добавлен в избранное',
                status=status.HTTP_400_BAD_REQUEST
            )
        return response

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        response = self.delete_recipe(request, pk, Favorite)
        if response is False:
            return Response(
                'Рецепт не добавлен в избранное!',
                status=status.HTTP_400_BAD_REQUEST
            )
        return response

    def add_recipe(self, request, pk, model):
        """Функция добавления рецепта в избранное/список покупок.

        Передается запрос, откуда получаем текущего пользователя,
        используемую модель (Favorite или ShopingCart), которая определяет,
        в какой список добавляется рецепт, и pk - id рецепта.
        Если рецепт уже есть в целевом списке - возвращает False,
        в противном случае возвращает ответ (Response).

        Args:
            request: объект запроса
            modelуемая модель
            pk: id рецепта

        Returns:
            Response | False: запрос(Response) или False(bool)
        """
        recipe = Recipe.objects.filter(pk=pk)
        if recipe:
            user = request.user
            if model.objects.filter(recipe=recipe, user=user).exists():
                return False
            model.objects.create(recipe=recipe, user=user)
            serializer = ShortInfoRecipeSerializer(recipe)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            "Рецепт не существует. Проверьте id.",
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete_recipe(self, request, pk, model):
        """Функция удаления рецепта из избранного/списка покупок.

        Передается запрос, откуда получаем текущего пользователя,
        используемую модель (Favorite или ShopingCart), которая определяет,
        откуда удаляется рецепт, и pk - id рецепта.
        Если рецепта нет в целевом списке - возвращает False,
        в противном случае возвращает ответ (Response).

        Args:
            request: объект запроса
            model: используемая модель
            pk: id рецепта

        Returns:
            Response | False: запрос(Response) или False(bool)
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        try:
            obj = get_object_or_404(model, recipe=recipe, user=user)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return False

    @action(
        detail=False,
        url_path="download_shopping_cart",
        methods=("get",),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user
            )
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
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    # ШАГ 1: КОПИРОВАТЬ/КОДИРОВАТЬ (ссылку)
    @action(
        methods=["get"],
        detail=True,
        url_path="get-link",
        url_name="get-link",
        permission_classes=[
            AllowAny,
        ],
    )
    # Пример айди ссылки на рецепт http://localhost/recipes/1
    # path("s/<str:encoded_id>/", ShortLinkView.as_view(), name="shortlink")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        # Кодируем "обычную" ссылку -> в "короткую"
        encoded_id = baseconv.base64.encode(str(recipe.id))
        # request.build_absolute_uri - это метод для получения
        # полного/абсолютного URL (с доменом http://localhost/)
        short_link = request.build_absolute_uri(
            # reverse('view_name', args=(obj.pk, ))
            reverse("shortlink", kwargs={"encoded_id": encoded_id})
        )
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)
        # БЫЛО:  http://localhost/recipes/1
        # СТАЛО: http://localhost/s/1/


# ШАГ 2: ВСТАВИТЬ/ДЕКОДИРОВАТЬ (ссылку)
class ShortLinkView(APIView):
    def get(self, request, encoded_id):
        # Метод set.issubset() позволяет проверить находится ли каждый элемент
        # множества set в последовательности other.
        # Метод возвращает True, если множество set является подмножеством
        # итерируемого объекта other, если нет, то вернет False.
        if not set(encoded_id).issubset(set(baseconv.BASE64_ALPHABET)):
            return Response(
                {"error": "Недопустимые символы в ссылке на рецепт"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Декодируем "короткую" ссылку -> в "обычную" айди ссылку на рецепт
        recipe_id = baseconv.base64.decode(encoded_id)
        recipe = get_object_or_404(Recipe, id=recipe_id)
        # request.build_absolute_uri - это метод для получения
        # полного/абсолютного URL (с доменом http://localhost/)
        return HttpResponseRedirect(
            request.build_absolute_uri(f"/recipes/{recipe.id}")
        )
        # БЫЛО:  http://localhost/s/1/
        # СТАЛО: http://localhost/recipes/1
