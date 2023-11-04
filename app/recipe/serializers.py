from rest_framework import serializers
from core.models import (
    Recipe,
    Tag,
    Ingradient
)


class IngradientSerializer(serializers.ModelSerializer):
    """Serializer for ingradient objects."""

    class Meta:
        model = Ingradient
        fields = ["id", "name"]
        read_only_fields = ["id"]


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer of recipe object."""
    tags = TagSerializer(many=True, required=False)
    ingradients = IngradientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "time_minutes",
            "price",
            "link",
            "tags",
            "ingradients"
        ]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        auth_user = self.context["request"].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)

    def _get_or_create_ingradients(self, ingradients, recipe):
        """Handle getting or creating ingradients as needed."""
        auth_user = self.context["request"].user
        for ing in ingradients:
            ing_obj, createted = Ingradient.objects.get_or_create(
                user=auth_user,
                **ing
            )
            recipe.ingradients.add(ing_obj)

    def create(self, validated_data):
        """Create and return a recipe."""
        tags = validated_data.pop("tags", [])
        ings = validated_data.pop("ingradients", [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingradients(ings, recipe)

        return recipe

    def update(self, instance, validated_data):
        """Update and return a recipe."""
        tags = validated_data.pop("tags", None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]
