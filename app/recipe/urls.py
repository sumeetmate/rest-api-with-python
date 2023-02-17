"""
URL mapping for Recipe APIs
"""

from django.urls import path, include
from recipe.views import RecipeViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('recipes', RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
