from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect

from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from django.utils import baseconv
from djoser import views as djoser_views
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (
    Favorite, Ingredient, IngredientsAmount, Recipe, ShoppingCart, Tag
)
from users.models import Follow, User

from .filters import RecipeFilter, IngredientFilter
from .pagination import LimitPagePagination
from .permissions import AdminOrAuthor, AdminOrReadOnly
from .serializers import (
    FollowSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeFollowerSerializer,
    RecipeSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UsersSerializer
)


class UsersViewSet(djoser_views.UserViewSet):
    """Вьюсет для модели пользователей"""

    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = LimitPagePagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username", "email")
    permission_classes = (AllowAny,)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    def subscribed(self, request, id=None):
        follower = get_object_or_404(User, id=id)
        follow, _ = Follow.objects.get_or_create(
            user=request.user, author=follower
        )
        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def unsubscribed(self, request, id=None):
        follower = get_object_or_404(User, id=id)
        Follow.objects.filter(user=request.user, author=follower).delete()
        return Response({"message": "Вы успешно отписаны"},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"],
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id):
        if request.method == "POST":
            return self.subscribed(request, id)
        return self.unsubscribed(request, id)

    @action(detail=False, methods=["get"],
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        following = request.user.follower.all()
        pages = self.paginate_queryset(following)
        serializer = FollowSerializer(pages, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['put'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='me-avatar',
    )
    def avatar(self, request):
        serializer = self._change_avatar(request.data)
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        data = request.data
        if 'avatar' not in data:
            data = {'avatar': None}
        self._change_avatar(data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _change_avatar(self, data):
        instance = self.get_instance()
        serializer = UserAvatarSerializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели тегов"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели ингредиентов"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None
    filter_backends = (IngredientFilter,)
    search_fields = ("^name",)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов"""

    queryset = Recipe.objects.all()
    permission_classes = (AdminOrAuthor,)
    pagination_class = LimitPagePagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        recipes = Recipe.objects.prefetch_related(
            "ingredient_amount__ingredient", "tags").all()
        return recipes

    def get_serializer_class(self):
        if self.action == "list":
            return RecipeSerializer
        if self.action == "retrieve":
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True, methods=["post", "delete"],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeFollowerSerializer(recipe)
            return Response(data=serializer.data,
                            status=status.HTTP_201_CREATED)
        deleted = get_object_or_404(Favorite, user=request.user,
                                    recipe=recipe)
        deleted.delete()
        return Response(
            {"message": "Рецепт успешно удален из избранного"},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True, methods=["post", "delete"],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeFollowerSerializer(recipe)
            return Response(data=serializer.data,
                            status=status.HTTP_201_CREATED)
        delete = get_object_or_404(ShoppingCart, user=request.user,
                                   recipe=recipe)
        delete.delete()
        return Response(
            {"message": "Рецепт успешно удален из списка покупок"},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=False, methods=["get"],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            IngredientsAmount.objects.filter(recipe__shopping_cart__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
        )
        data_list = ingredients.values_list(
            "ingredient__name", "ingredient__measurement_unit", "amount"
        )
        shopping_cart = "\n".join(
            [f"{name} {amount} {measure}"
             for name, measure, amount in data_list]
        )
        response = HttpResponse(shopping_cart, content_type="text/plain")
        return response
    
    @action(
        methods=['get'],
        detail=True,
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        encoded_id = baseconv.base64.encode(str(recipe.id))
        short_link = request.build_absolute_uri(
            reverse('shortlink', kwargs={'encoded_id': encoded_id})
        )
        return Response({'short-link': short_link},
                        status=status.HTTP_200_OK)


class ShortLinkView(APIView):
    def get(self, request, encoded_id):
        if not set(encoded_id).issubset(set(baseconv.BASE64_ALPHABET)):
            return Response(
                {'error': 'Недопустимые символы в короткой ссылке.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe_id = baseconv.base64.decode(encoded_id)
        recipe = get_object_or_404(Recipe, id=recipe_id)
        return HttpResponseRedirect(
            request.build_absolute_uri(
                f'/recipes/{recipe.id}'
            )
        )
