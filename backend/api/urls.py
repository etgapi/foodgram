from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet, RecipeViewSet, TagViewSet, UsersViewSet
)

router = DefaultRouter()

app_name = "api"

router.register("users", UsersViewSet, basename="users")
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")


urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
