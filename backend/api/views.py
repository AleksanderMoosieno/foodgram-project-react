from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .mixins import ListRetriveViewSet
from .pagination import CustomPagination
from .permissions import IsAuthenticated, IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeSerializer,
                          RecipeSerializerPost, SubscribeSerializer,
                          TagSerializer, UserSerializer, TagSerializer)
from .utils import shooping_card
from users.models import (Subscribe, User, Tag, IngredientInRecipe,
                          Recipe, Ingredient, ShoppingCart, Favorite)


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


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для Recipe."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializerPost
    pagination_class = CustomPagination
    filter_class = IngredientFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def perform_create(self, serializer):
        """Создание рецепта."""
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=("delete", "post"),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        """Добавить/убрать обьект в избранное или из него."""
        if request.method == "POST":
            return self.add_obj(Favorite, request.user, pk)
        elif request.method == "DELETE":
            return self.delete_obj(Favorite, request.user, pk)
        return None

    @action(
        detail=True,
        methods=("delete", "post"),
        permission_classes=(IsAuthenticated,)
    )
    def shop_cart(self, request, pk=None):
        """Добавление/удаление рецепта корзины"""
        if request.method == "POST":
            return self.add_obj(ShoppingCart, request.user, pk)
        elif request.method == "DELETE":
            return self.delete_obj(ShoppingCart, request.user, pk)
        return None

    def add_obj(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response(
                {"errors": "Рецепт уже добавлен в список"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeSerializerPost(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"errors": "Рецепт уже удален"}, status=status.HTTP_400_BAD_REQUEST
        )

    def shopping_cart(self, request):
        final_list = {}
        ingredients = IngredientInRecipe.objects.all(
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
