from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Tag, Recipe
from recipe.serializers import TagSerializer
from decimal import Decimal

TAGS_URL = reverse("recipe:tag-list")


def tag_detail(tag_id):
    """create and return a Tag detail URL."""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="test@example.com", password="testpass123"):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name="Pabloo")
        Tag.objects.create(user=self.user, name="Gonzalo")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test retrieving tags limited to user."""
        self.new_user = create_user(
            email="user@example.com",
            password="userpass123"
        )
        Tag.objects.create(user=self.new_user, name="Tag1")
        tag = Tag.objects.create(user=self.user, name="Pabloo")

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating the tags."""
        tag = Tag.objects.create(user=self.user, name="Lunch desert")

        payload = {"name": "Dinner desert"}
        url = tag_detail(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting the tag."""
        tag = Tag.objects.create(user=self.user, name="Snack")

        url = tag_detail(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tag_exists = Tag.objects.filter(user=self.user)
        self.assertFalse(tag_exists)

    def test_filter_tags_assigned_to_recipes(self):
        """Test filtering tags that are assigned to the recipes."""
        tag1 = Tag.objects.create(user=self.user, name="South Indian")
        tag2 = Tag.objects.create(user=self.user, name="North Indian")
        recipe = Recipe.objects.create(
            title="Egg Omlete",
            time_minutes=15,
            price=Decimal("10.25"),
            user=self.user
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_list_unique(self):
        """Test filtered tag returned a unique list."""
        tag = Tag.objects.create(user=self.user, name="South Indian")
        Tag.objects.create(user=self.user, name="North Indian")
        recipe1 = Recipe.objects.create(
            title="Egg omelete",
            time_minutes=20,
            price=Decimal("8.25"),
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title="Butter Chiken",
            time_minutes=35,
            price=Decimal("4.99"),
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
