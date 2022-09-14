from django.shortcuts import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipe


class ListRetriveViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    pass


class CreateFavouriteShoppingCartMixin:
    model_class = None
    create_serializer = None

    def create(self, request, *args, **kwargs):
        if not self.model_class or not self.create_serializer:
            return Response(
                data={
                    "response": "Provide model class"
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.model_class.objects.create(
            user=self.request.user,
            recipe=recipe
        )
        serializer = self.create_serializer(
            recipe,
            many=False
        )
        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )
