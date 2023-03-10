"""
Test for Recipe API
"""
import tempfile
import os
from PIL import Image
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Create and return image upload URL."""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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
        # recipes = Recipe.objects.all().order_by('-id')
        # serializer = RecipeSerializer(recipes, many=True)
        # print(res.data)
        # print(serializer.data)
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

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            'title': 'Chicken Curry',
            'time_minutes': '30',
            'price': Decimal('2.5'),
            'tags': [{'name': 'Indian'}, {'name': 'Dinner'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test creating a recipe with existing tag."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': '60',
            'price': Decimal('5.5'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                user=self.user,
                name=tag['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        newTag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(newTag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipes tags."""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        self.assertNotIn(tag, recipe.tags.all())

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""
        payload = {
            'title': 'Chicken Curry',
            'time_minutes': '30',
            'price': Decimal('2.5'),
            'ingredients': [{'name': 'chicken'},
                            {'name': 'masala'},
                            {'name': 'garlic'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a recipe with existing ingredients."""
        ingredient_pepper = Ingredient.objects.create(
            user=self.user, name='red pepper'
            )
        payload = {
            'title': 'Pongal',
            'time_minutes': '60',
            'price': Decimal('5.5'),
            'ingredients': [{'name': 'red pepper'}, {'name': 'cilantro'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient_pepper, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating ingredient when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'brocolli'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        newIngd = Ingredient.objects.get(user=self.user, name='brocolli')
        self.assertIn(newIngd, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe."""
        ing_bread = Ingredient.objects.create(user=self.user, name='bread')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ing_bread)

        ing_paneer = Ingredient.objects.create(user=self.user, name='paneer')
        payload = {'ingredients': [{'name': 'bread'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ing_bread, recipe.ingredients.all())
        self.assertNotIn(ing_paneer, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipes ingredients."""
        ingredient = Ingredient.objects.create(user=self.user, name='Potato')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
        self.assertNotIn(ingredient, recipe.ingredients.all())


class ImageUploadTests(TestCase):
    """Tests for image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com', 'password123')
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_uplaod_image(self):
        """Test uploading an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_ipload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
