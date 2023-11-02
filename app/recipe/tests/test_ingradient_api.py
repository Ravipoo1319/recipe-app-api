from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Ingradient
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from recipe.serializers import IngradientSerializer


INGREADIENT_URLS = reverse("recipe:ingradient-list")


def create_user(email="user@example.com", password="userpass123"):
    """Create and return a user."""
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class PublicIngradientsApiTests(TestCase):
    """Test unathenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required for retrieving ingradients."""
        res = self.client.get(INGREADIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieving_ingradients(self):
        """Test retrieving a list of ingradients."""
        Ingradient.objects.create(user=self.user, name="Ingrad1")
        Ingradient.objects.create(user=self.user, name="Ingrad2")

        res = self.client.get(INGREADIENT_URLS)

        ingradients = Ingradient.objects.all().order_by("-name")
        serializer = IngradientSerializer(ingradients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingradinet_limited_user(self):
        """Test retrieving ingradients limited to user."""
        new_user = create_user(email="new@example.com", password="testpass123")
        Ingradient.objects.create(user=new_user, name="Salt")
        ing = Ingradient.objects.create(user=self.user, name="Pepper")

        res = self.client.get(INGREADIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ing.name)
        self.assertEqual(res.data[0]["id"], ing.id)
