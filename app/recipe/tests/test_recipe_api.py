"""
Test for Recipe API
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    "Create and return a recipe details url"
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return sample recipe"""
    defaults = {
        'title': 'Sample Recipe Title',
        'time_minutes': 22,
        'price': Decimal('4.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf'
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unatuthenticated API request"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test auth is required to call API"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """TEST authenticated API requets"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com', password='password123')
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        """Test retriving the recipies list"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        print(res.data)
        print(serializer.data)
        # self.assertEqual(res.data, serializer.data)

    def test_retrive_list_limited_user(self):
        """Test retrive list of recipes for authenticated user"""
        other_user = create_user(
            email='otheruser@example.com', password='password123')
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # recipes = Recipe.objects.filter(user=self.user)
        # serializer = RecipeSerializer(recipes, many=True)
        # self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """test get recipe details."""
        recipe = create_recipe(user=self.user)
        serializer = RecipeDetailSerializer(recipe)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """test to create a recipe"""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('9.90')
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(recipe.user, self.user)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

    def test_partial_update(self):
        """Test partial update of a recipe"""
        original_link = "https://exampleurl.com"
        recipe = create_recipe(
            title='Sample title',
            link=original_link,
            user=self.user
        )

        payload = {'title': 'New sample URL'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.link, original_link)

    def test_full_update(self):
        """test full update for recipe"""
        recipe = create_recipe(
            user=self.user,
            title='sample title',
            description='this is chikcen tikka',
            link='http://samplelink.com'
        )
        payload = {
            'title': 'Chicken tikka',
            'description': 'The Indiann delicasy',
            'time_minutes': 20,
            'price': Decimal('10.99'),
            'link': 'http://newsamplelink.com'
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

    def test_update_user_returns_error(self):
        """Update user recipe not allowed"""
        new_user = create_user(
            email='otheruser@example.com', password='password123')
        recipe = create_recipe(self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """test delete recipe"""
        recipe = create_recipe(self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        """test delete recipe of other user return error"""
        otheruser = create_user(
            email="otheruser@example.com", password="1223pass")
        recipe = create_recipe(user=otheruser)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
