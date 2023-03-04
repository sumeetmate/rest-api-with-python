"""Tests for Ingredient API"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

ING_URL = reverse('recipe:ingredient-list')


def create_user(email='user@example.com', password='Welcome123'):
    """Create and return a new user"""
    return get_user_model().objects.create_user(email=email, password=password)


def get_detail_url(ingredient_id):
    """Create and return ingredient detail url."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


class PulbicIngredientApiTests(TestCase):
    """Tests unauthorized API tests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test unathenticated request for API."""
        res = self.client.get(ING_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Tests authorized API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retriving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Vanilla')

        res = self.client.get(ING_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited specific user."""
        user2 = create_user(email='user2@example.com', password='Welcome12')
        Ingredient.objects.create(user=user2, name='Chicken')
        Ingredient.objects.create(user=user2, name='Turmeric')

        ingredient = Ingredient.objects.create(user=self.user, name='Meat')

        res = self.client.get(ING_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

        ingredients = Ingredient.objects.filter(user=self.user)
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_update_ingredient(self):
        """Tets updating ingredient"""
        ingredient = Ingredient.objects.create(
            user=self.user, name='red chilli'
            )

        payload = {
            'name': 'green chilli'
        }
        url = get_detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting ingredient"""
        ingredient = Ingredient.objects.create(
            user=self.user, name='red chilli'
            )
        url = get_detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Ingredient.objects.filter(user=self.user)
        self.assertFalse(tags.exists())
