from http import HTTPStatus

from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCartSerializer, RecipeSerializer,
                          RecipeSerializerPost, RecipeShortFieldSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer)
from .mixins import ListRetriveViewSet


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

    def get_queryset(self):
        return Subscribe.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Создание подписки.
        """
        author_id = self.kwargs.get('author_id')
        author = get_object_or_404(User, id=author_id)
        if author == request.user:
            return Response(
                'Нельзя подписаться на себя',
                status=HTTPStatus.BAD_REQUEST
            )
        try:
            Subscribe.objects.create(author=author, user=self.request.user)
        except IntegrityError:
            return Response(
                'Вы уже подписаны на данного автора',
                status=HTTPStatus.BAD_REQUEST
            )
        subscription = get_object_or_404(
            Subscribe,
            author=author,
            user=self.request.user
        )
        serializer = SubscribeSerializer(subscription, many=False)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        """
        Удаление подписки.
        """
        author_id = self.kwargs.get('author_id')
        author = get_object_or_404(User, id=author_id)
        get_object_or_404(
            Subscribe,
            author=author,
            user=self.request.user
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)


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


class TagViewSet(ListRetriveViewSet):
    """
    Обработка моделей тегов.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny, )


class DownloadShoppingCartViewSet(APIView):
    def get(self, request):
        user = request.user
        shopping_carts = ShoppingCart.objects.filter(user=user)
        recipes = [cart.recipe for cart in shopping_carts]
        cart_dict = {}
        for recipe in recipes:
            for ingredient in recipe.ingredients.all():
                amount = get_object_or_404(IngredientInRecipe,
                                           recipe=recipe,
                                           ingredient=ingredient).amount
                if ingredient.name not in cart_dict:
                    cart_dict[ingredient.name] = amount
                else:
                    cart_dict[ingredient.name] += amount
        content = ''
        for item in cart_dict:
            measurement_unit = get_object_or_404(Ingredient,
                                                 name=item).measurement_unit
            content += f'{item} -- {cart_dict[item]} {measurement_unit}\n'
        response = HttpResponse(content,
                                content_type='text/plain,charset=utf8')
        response['Content-Disposition'] = 'attachment; filename="cart.txt"'
        return response
