from http import HTTPStatus

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag, IngredientInRecipe)
from users.models import Subscribe, User
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly, IsAuthenticated
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCartSerializer, RecipeSerializer,
                          RecipeSerializerPost, RecipeShortFieldSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer)
from .mixins import ListRetriveViewSet
from .utils import shooping_card


class UserViewSet(viewsets.ModelViewSet):
    """
    Обработка модели пользователя.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination


class SubscribeViewSet(viewsets.ModelViewSet):
    """
    Обработка модели подписок.
    """
    serializer_class = SubscribeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = CustomPagination

    def subscribe(self, request, id=None):
        """Подписка на пользователей."""

        user = request.user
        author = get_object_or_404(User, id=id)

        if user == author:
            return Response({
                "errors": "Вы не можете подписываться на себя"
            }, status=status.HTTP_400_BAD_REQUEST)
        if Subscribe.objects.filter(user=user, author=author).exists():
            return Response({
                "errors": "Вы уже подписаны на пользователя"
            }, status=status.HTTP_400_BAD_REQUEST)

        follow = Subscribe.objects.create(user=user, author=author)
        serializer = SubscribeSerializer(
            follow, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        """Отписка."""
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response({
                "errors": "Вы не можете отписываться от себя"
            }, status=status.HTTP_400_BAD_REQUEST)
        follow = Subscribe.objects.filter(user=user, author=author)
        if follow.exists():
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response({
            "errors": "Вы уже отписались"
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Список подписок."""
        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages,
            many=True,
            context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Обработка моделей рецептов.
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly, )
    serializer_class = RecipeSerializer
    filter_class = RecipeFilter
    filter_backends = (DjangoFilterBackend, )
    pagination_class = CustomPagination

    def get_serializer_class(self):
        """
        Функция выбора сериализатора при разных запросах.
        """
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeSerializerPost

    def perform_create(self, serializer):
        """
        Передаём данные автора при создании рецепта.
        """
        serializer.save(author=self.request.user)


class IngredientViewSet(ListRetriveViewSet):
    """
    Обработка модели продуктов.
    """
    queryset = Ingredient.objects.all()
    permission_classes = [permissions.AllowAny, ]
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, IngredientFilter)
    search_fields = ['^name', ]


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """
    Обработка модели корзины.
    """
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        ShoppingCart.objects.create(user=self.request.user, recipe=recipe)
        serializer = RecipeCartSerializer(recipe, many=False)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(
            ShoppingCart,
            user=self.request.user,
            recipe=recipe
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('post', 'delete')

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        Favorite.objects.create(user=self.request.user, recipe=recipe)
        serializer = RecipeShortFieldSerializer(recipe, many=False)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=recipe
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    def shopping_cart(self, request):
        final_list = {}
        ingredients = IngredientInRecipe.objects.filter(
            recipe__cart__user=request.user).values_list(
            "ingredient__name", "ingredient__measurement_unit",
            "amount")
        for item in ingredients:
            name = item[0]
            if name not in final_list:
                final_list[name] = {
                    "measurement_unit": item[1],
                    "amount": item[2]
                }
            else:
                final_list[name]["amount"] += item[2]

        return shooping_card(final_list)


class TagViewSet(ListRetriveViewSet):
    """
    Обработка моделей тегов.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny, )
