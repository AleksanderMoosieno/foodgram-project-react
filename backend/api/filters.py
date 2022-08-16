from distutils.util import strtobool
from django_filters import rest_framework as filters

from recipes.models import Recipe


CHOICES = (
    ('0', 'False'),
    ('1', 'True')
)


class RecipeFilter(filters.FilterSet):

    author = filters.CharFilter(field_name='author__id')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.TypedChoiceFilter(
        choices=CHOICES,
        coerce=strtobool,
        method='get_is_favorited'
    )

    is_in_shopping_cart = filters.TypedChoiceFilter(
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
