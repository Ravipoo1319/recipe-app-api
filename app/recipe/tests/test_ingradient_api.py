from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Ingradient, Recipe
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from recipe.serializers import IngradientSerializer
from decimal import Decimal


INGREADIENT_URLS = reverse("recipe:ingradient-list")


def detail_url(ingradient_id):
    """Create and return an ingradient detail url."""
    return reverse("recipe:ingradient-detail", args=[ingradient_id])


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

    def test_update_ingradient(self):
        """Test updating an existing ingradient."""
        ingradient = Ingradient.objects.create(
            user=self.user,
            name="ingradient test",
        )

        payload = {"name": "Updated ingradient"}
        url = detail_url(ingradient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingradient.refresh_from_db()
        self.assertEqual(ingradient.name, payload["name"])

    def test_delete_ingradient(self):
        """Test deleting the ingradinet is successful."""
        ingradient = Ingradient.objects.create(
            user=self.user,
            name="Lettuce",
        )

        url = detail_url(ingradient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingradient_exists = Ingradient.objects.filter(user=self.user).exists()
        self.assertFalse(ingradient_exists)

    def test_filter_ingradients_assigned_to_recipes(self):
        """Test filtering ingradients assigned to the recipes."""
        ing1 = Ingradient.objects.create(user=self.user, name="Pepper")
        ing2 = Ingradient.objects.create(user=self.user, name="Turmeric")
        recipe = Recipe.objects.create(
            title="Egg curry",
            time_minutes=30,
            price=Decimal("4.25"),
            user=self.user,
        )
        recipe.ingradients.add(ing1)

        res = self.client.get(INGREADIENT_URLS, {"assigned_only": 1})

        s1 = IngradientSerializer(ing1)
        s2 = IngradientSerializer(ing2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingradients_unique(self):
        """Test filtered ingradients returned a unique list."""
        ing = Ingradient.objects.create(user=self.user, name="Eggs")
        Ingradient.objects.create(user=self.user, name="Chilli Powder")
        recipe1 = Recipe.objects.create(
            title="Eggs Biryani",
            time_minutes=30,
            price=Decimal("3.75"),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title="Eggs Curry",
            time_minutes=60,
            price=Decimal("5.75"),
            user=self.user,
        )
        recipe1.ingradients.add(ing)
        recipe2.ingradients.add(ing)

        res = self.client.get(INGREADIENT_URLS, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
