from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from .serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer,
    IngradientSerializer,
    RecipeImageSerializer
)
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import (
    Recipe,
    Tag,
    Ingradient,
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description="comma separated list of IDs to filter."
            ),
            OpenApiParameter(
                "ingradients",
                OpenApiTypes.STR,
                description="comma separated list of IDs to filter."
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """Views for manage recipe API's."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert list of strings to integers."""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Rterieves recipes for authenticated users."""
        tags = self.request.query_params.get("tags")
        ings = self.request.query_params.get("ingradients")
        queryset = self.queryset

        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)

        if ings:
            ing_ids = self._params_to_ints(ings)
            queryset = queryset.filter(ingradients__id__in=ing_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by("-id").distinct()

    def get_serializer_class(self):
        """Returns the serializer class for request."""
        if self.action == "list":
            return RecipeSerializer
        elif self.action == "upload_image":
            return RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseRecipeAttrViewSet(
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet
):
    """Base viewset for recipe attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by("-name")


class TagViewSet(BaseRecipeAttrViewSet, viewsets.GenericViewSet):
    """Manage tags in the database."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngradientViewSet(BaseRecipeAttrViewSet, viewsets.GenericViewSet):
    """Manage ingradients in the database."""
    queryset = Ingradient.objects.all()
    serializer_class = IngradientSerializer
