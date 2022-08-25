from django.db.models import Sum
from django.http import HttpResponse

from recipes.models.ingredient_amount import IngredientInRecipe
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import exceptions


def shopping_cart(request):
    """Функция для скачивания карточки покупок."""
    ingredients = IngredientInRecipe.objects.all(
            recipe__cart__user=request.user).values_list(
            "ingredient__name", "ingredient__measurement_unit").annotate(sum_amount=Sum("amount"))
    pdfmetrics.registerFont(
        TTFont("Fonts", "Fonts.ttf", "UTF-8"))
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = ("attachment; "
                                       "filename='shopping_list.pdf'")
    page = canvas.Canvas(response)
    page.setFont("Fonts", size=24)
    page.drawString(200, 800, "Список ингредиентов")
    page.setFont("Fonts", size=16)
    height = 750
    for idx, ingr in enumerate(ingredients, start=1):
        page.drawString(75, height, text=(
            f'{idx}. {ingr["ingredient__name"]} - {ingr["sum_amount"]}'
            f'{ingr["ingredient__measurement_unit"]}'
        ))
        height -= 25
    page.showPage()
    page.save()
    return response


def double_checker(item_list):
    """Проверяет элементы на повтор"""
    for item in item_list:
        if len(item) == 0:
            raise exceptions.ValidationError(
                f'{item} должен иметь хотя бы одну позицию!'
            )
        for element in item:
            if item.count(element) > 1:
                raise exceptions.ValidationError(
                    f'{element} уже есть в рецепте!'
                )
