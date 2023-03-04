"""
URL mapping for Recipe APIs
"""

from django.urls import path, include
from recipe.views import RecipeViewSet, TagViewSet, IngredientViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
