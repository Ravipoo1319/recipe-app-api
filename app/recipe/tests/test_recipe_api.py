from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
import tempfile
import os
from PIL import Image

from core.models import (
    Recipe,
    Tag,
    Ingradient,
)
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail url."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


# Helper function to create recipe
def create_recipe(user, **kwargs):
    """Create and return a sample recipe."""
    defaults = {
        "title": "Sample recipe test",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "description": "Sample description",
        "link": "http://example.com/recipe.pdf"
    }
    defaults.update(kwargs)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def image_upload_url(recipe_id):
    """Create and return an image upload url."""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test public features of the Recipe API."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is requied to call API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test API requests that required authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="test123")
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        # to get the latest one at top
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        other_user = create_user(
            email="other@example.com",
            password="testpass123"
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe details."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a new recipe."""
        payload = {
            "title": "Sample Recipe",
            "time_minutes": 5,
            "price": Decimal("5.99")
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe."""
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link=original_link,
        )

        payload = {"title": "New recipe title"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Tets full update of a recipe."""
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link="https://exmaple.com/recipe.pdf",
            description="Sample recipe description"
        )

        payload = {
            "title": "New recipe title",
            "link": "https://example.com/newrecipe.pdf",
            "description": "New recipe description",
            "time_minutes": 10,
            "price": Decimal("5.10")
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):
        """Test changing the recipe user results in an error."""
        new_user = create_user(email="user2@example.com", password="test123")
        recipe = create_recipe(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(recipe.id)

        self.client.patch(url, payload)
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        recipe_exists = Recipe.objects.filter(id=recipe.id).exists()
        self.assertFalse(recipe_exists)

    def test_recipe_other_users_recipe_error(self):
        """Test tring to delete another users recipe gies error."""
        new_user = create_user(email="new@example.com", password="testpass123")
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        recipe_exists = Recipe.objects.filter(id=recipe.id).exists()
        self.assertTrue(recipe_exists)

    def test_create_recipe_with_new_tags(self):
        """Test creating recipe with a new tags is successful."""
        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal("2.50"),
            "tags": [{"name": "Thai"}, {"name": "Dinner"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            tag_exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(tag_exists)

    def test_create_tag_with_existing_tag(self):
        """Test creating a recipe with existing tag."""
        tag_indian = Tag.objects.create(user=self.user, name="Indian")
        payload = {
            "title": "Pongal",
            "time_minutes": 60,
            "price": Decimal("4.50"),
            "tags": [{"name": "Indian"}, {"name": "Breakfast"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload["tags"]:
            tag_exist = Tag.objects.filter(
                user=self.user,
                name=tag["name"]
            ).exists()
            self.assertTrue(tag_exist)

    def test_create_tag_on_update(self):
        """Test creating a tag when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {
            "tags": [{"name": "Lunch"}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing recipes tags."""
        tag = Tag.objects.create(user=self.user, name="Non-veg")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingradients(self):
        """Test creating a recipe with new ingradients is successful."""
        payload = {
            "title": "Dum Biryani",
            "time_minutes": 30,
            "price": Decimal("2.25"),
            "ingradients": [{"name": "Biryani Masala"}, {"name": "Dahi"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingradients.count(), 2)
        for ingradient in payload["ingradients"]:
            ing_exists = recipe.ingradients.filter(
                name=ingradient["name"],
                user=self.user
            ).exists()
            self.assertTrue(ing_exists)

    def test_creating_recipe_with_existing_ingradients(self):
        """Test creating a recipe with existing ingradients."""
        ingradient = Ingradient.objects.create(
            name="Fish",
            user=self.user
        )

        payload = {
            "title": "Fish curry",
            "time_minutes": 60,
            "price": Decimal("3.75"),
            "ingradients": [{"name": "Fish"}, {"name": "Pepper"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingradients.count(), 2)
        self.assertIn(ingradient, recipe.ingradients.all())
        for ing in payload["ingradients"]:
            exists = recipe.ingradients.filter(
                name=ing["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingradient_on_update(self):
        """Test creating an ingradient on updating recipe."""
        recipe = create_recipe(user=self.user)

        payload = {
            "ingradients": [{"name": "Limes"}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingradient = Ingradient.objects.get(user=self.user, name="Limes")
        self.assertIn(new_ingradient, recipe.ingradients.all())

    def test_update_recipe_assign_ingradient(self):
        """Test assigning an existing ingradient when updating a recipe."""
        ingradient1 = Ingradient.objects.create(user=self.user, name="Pepper")
        recipe = create_recipe(user=self.user)
        recipe.ingradients.add(ingradient1)

        ingradient2 = Ingradient.objects.create(user=self.user, name="Chilli")
        payload = {"ingradients": [{"name": "Chilli"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingradient2, recipe.ingradients.all())
        self.assertNotIn(ingradient1, recipe.ingradients.all())

    def test_clear_recipe_ingradient(self):
        """Test clearing a recipe's ingradients."""
        ingradient = Ingradient.objects.create(user=self.user, name="Garlic")
        recipe = create_recipe(user=self.user)
        recipe.ingradients.add(ingradient)

        payload = {"ingradients": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingradients.count(), 0)

    def test_filter_recipe_by_tags(self):
        """Test filtering recipes by tags."""
        r1 = create_recipe(user=self.user, title="Dal Tadka")
        r2 = create_recipe(user=self.user, title="Chiken Biryani")
        tag1 = Tag.objects.create(user=self.user, name="Veg")
        tag2 = Tag.objects.create(user=self.user, name="Non-Veg")
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title="Egg Curry")

        params = {"tags": f'{tag1.id}, {tag2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_recipes_by_ingradients(self):
        """Test filtering recipes by ingradients."""
        r1 = create_recipe(user=self.user, title="Dal Tadka")
        r2 = create_recipe(user=self.user, title="Chiken Biryani")
        ing1 = Ingradient.objects.create(user=self.user, name="Garlic")
        ing2 = Ingradient.objects.create(user=self.user, name="Chiken")
        r1.ingradients.add(ing1)
        r2.ingradients.add(ing2)
        r3 = create_recipe(user=self.user, title="Egg Curry")

        params = {"ingradients": f'{ing1.id}, {ing2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Tests for the Image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "password123",
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.recipe.id)
        payload = {"image": "notanimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
