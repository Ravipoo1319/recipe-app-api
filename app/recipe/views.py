from .serializers import RecipeSerializer
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe


class RecipeViewSet(viewsets.ModelViewSet):
    """Views for manage recipe API's."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Rterieves recipes for authenticated users."""
        return self.queryset.filter(user=self.request.user).order_by("-id")
