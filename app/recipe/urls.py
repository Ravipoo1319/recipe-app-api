from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register("recipes", views.RecipeViewSet)
router.register("tag", views.TagViewSet)
router.register("ingradient", views.IngradientViewSet)

app_name = "recipe"


urlpatterns = [
    path("", include(router.urls))
]
