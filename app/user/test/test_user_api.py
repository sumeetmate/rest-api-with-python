"""
Tests for user API
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """TEST pulbic features of the User API"""

    def setup(self):
        self.client = APIClient()

    def test_create_new_user_success(self):
        payload = {
            "email": "Test@exmaple.com",
            "password": "password123",
            "name": "Test User"
            }

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_email_exists_error(self):
        """Test error returned if user with email exists"""
        payload = {
            "email": "Test@exmaple.com",
            "password": "password123",
            "name": "Test User"
        }

        create_user(**payload)
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 chars"""
        payload = {
            "email": "Test@exmaple.com",
            "password": "pw",
            "name": "Test User"
        }

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(exists)

    def test_create_token_for_user(self):
        """Test generates token for valid user"""
        details = {
            "email": "Test@exmaple.com",
            "password": "password123",
            "name": "Test User"
        }
        create_user(**details)

        payload = {
            "email": details['email'],
            "password": details['password'],
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_create_token_bad_credentials(self):
        """Test return error if bad credentials"""
        create_user(email='testuser1@example.com', password='goodpass123')

        payload = {
            "email": 'testuser1@example.com',
            "password": 'badpass123',
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)

    def test_create_token_blank_password(self):
        """Test return error if blank password"""
        create_user(email='testuser1@example.com', password='goodpass123')

        payload = {
            "email": 'testuser1@example.com',
            "password": '',
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)


class PrivateUserApiTests(TestCase):
    """TEST API requersts that requires authentication"""

    def setUp(self):
        self.user = create_user(
            email='testuser1@exmaple.com',
            password='password123',
            name='Test User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'name': self.user.name,
            'email': self.user.email
            })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint"""
        response = self.client.post(ME_URL, {})

        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {'name': 'new updated user', 'password': 'newpassword123'}

        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
