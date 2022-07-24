from rest_framework.pagination import PageNumberPagination
from foodgram.settings import PAGES


class CustomPagination(PageNumberPagination):
    """
    Пагинатор проекта.
    """
    page_size = PAGES
    page_size_query_param = 'limit'


class RecipesLimitPagination(PageNumberPagination):
    page_size_query_param = 'recipes_limit'
