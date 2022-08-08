from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User
from fields import Base64ImageField


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password',
                  'first_name', 'last_name', 'is_subscribed')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = (
            make_password(validated_data.pop('password')))
        return super().create(validated_data)

    def get_is_subscribed(self, obj):
        """
        Функция обработки параметра подписчиков.
        """
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return(
            Subscribe.objects.filter(
                user=request.user,
                author__id=obj.id
            ).exists()
        )


class ShoppingCartFavoriteRecipes(metaclass=serializers.SerializerMetaclass):
    """
    Класс определения избранных рецептов
    и продуктов корзины.
    """
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        """
        Функция обработки параметра избранного.
        """
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return (
            Favorite.objects.filter(user=request.user,
                                    recipe__id=obj.id).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return (
            ShoppingCart.objects.filter(user=request.user,
                                        recipe__id=obj.id).exists()
        )


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор избранных рецептов.
    """
    class Meta:
        model = Favorite
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели продукта в рецепте. Чтение.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeShortSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer,
                       ShoppingCartFavoriteRecipes):
    """
    Сериализатор модели рецептов. Чтение.
    """
    author = UserSerializer(many=False)
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(many=True,
                                               source='recipe_ingredient')
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'ingredients', 'text',
                  'cooking_time', 'pub_date', 'image', 'tags',
                  'is_favorited', 'is_in_shopping_cart')


class RecipeShortFieldSerializer(serializers.ModelSerializer):
    """
    Сериализатор короткой версии отображения модели рецептов.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class RecipeSerializerPost(serializers.ModelSerializer,
                           ShoppingCartFavoriteRecipes):
    """
    Сериализатор модели рецептов. Запись.
    """
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    ingredients = IngredientInRecipeShortSerializer(source='recipe_ingredient',
                                                    many=True)
    image = Base64ImageField(max_length=None, use_url=False,)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'text',
                  'ingredients', 'is_in_shopping_cart', 'tags',
                  'cooking_time', 'is_favorited')

    def get_is_in_shopping_cart(self, obj):
        """Получение информации о нахождении рецепта."""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(cart__user=user, id=obj.id).exists()

    def get_is_favorited(self, obj):
        """Получение списка изранного."""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(favorites__user=user, id=obj.id).exists()

    def create_ingredients(self, ingredients, recipe):
        """Получение ингредиентов для рецепта."""

        for ingredient in ingredients:
            IngredientInRecipe.objects.get_or_create(
                recipe=recipe,
                ingredient_id=ingredient.get("id"),
                amount=ingredient.get("amount"),
            )

    def create(self, validated_data):
        """Создание рецепта."""
        image = validated_data.pop("image")
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(image=image, **validated_data)
        tags_data = self.initial_data.get("tags")
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, recipe, validated_data):
        """Функция редактирования рецепта."""
        ingredients = validated_data.pop("ingredients")
        recipe.ingredients.clear()
        tags = self.initial_data.get("tags")
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)

    def validate(self, data):
        """Валидация."""
        ingredients = self.initial_data.get("ingredients")
        if not ingredients:
            raise serializers.ValidationError(
                {
                    "ingredients": "Один ингридиент"
                }
            )
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_item["id"])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    "Ингридиенты должны " "быть уникальными"
                )
            ingredient_list.append(ingredient)
            if int(ingredient_item["amount"]) < 0:
                raise serializers.ValidationError(
                    {
                        "ingredients": (
                            "Убедитесь, что значение количества ингр. > 0."
                        )
                    }
                )
        data["ingredients"] = ingredients
        return data

    def validate_cooking_time(self, cooking_time):
        """Валидация приготовления."""
        if int(cooking_time) <= 1:
            raise serializers.ValidationError(
                "Минимальное время приготовления - 1 мин.")
        return cooking_time


class SubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор списка подписок.
    """
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    is_subscribed = serializers.SerializerMethodField()
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipe_author.count',
        read_only=True
    )

    class Meta:
        model = Subscribe
        fields = ('id', 'username', 'email', 'is_subscribed',
                  'first_name', 'last_name', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        """
        Функция обработки параметра подписчиков.
        """
        request = self.context.get('request')
        if not request:
            return True
        return(
            Subscribe.objects.filter(
                user=request.user,
                author__id=obj.id
            ).exists()
        )

    def get_recipes(self, obj):
        """
        Функция получения рецептов
        автора.
        """
        try:
            recipes_limit = int(
                self.context.get('request').query_params['recipes_limit']
            )
            recipes = Recipe.objects.filter(author=obj.author)[:recipes_limit]
        except Exception:
            recipes = Recipe.objects.filter(author=obj.author)
        serializer = RecipeShortFieldSerializer(recipes, many=True,)
        return serializer.data


class ShoppingCartSerializer(serializers.Serializer):
    """
    Сериализатор корзины.
    """
    class Meta:
        model = ShoppingCart
        fields = '__all__'


class RecipeCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
