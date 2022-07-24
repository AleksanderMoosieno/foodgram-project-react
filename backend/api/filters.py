from distutils.util import strtobool

import django_filters
from rest_framework import filters

from recipes.models import Recipe

CHOICES = (
    ('0', 'False'),
    ('1', 'True')
)


class RecipeFilter(django_filters.FilterSet):

    author = django_filters.CharFilter(field_name='author__id')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filters.TypedChoiceFilter(
        choices=CHOICES,
        coerce=strtobool,
        method='get_is_favorited'
    )

    is_in_shopping_cart = django_filters.TypedChoiceFilter(
        choices=CHOICES,
        coerce=strtobool,
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):

        if not value:
            return queryset
        return queryset.filter(favoriterecipe__user=self.request.user)

    def get_is_in_shopping_cart(self, queryset, name, value):

        if not value:
            return queryset
        return queryset.filter(carts__user=self.request.user)


class IngredientFilter(filters.SearchFilter):

    search_param = 'name'
