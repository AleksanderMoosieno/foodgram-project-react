from django.http import HttpResponse

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from rest_framework import exceptions


def shooping_card(y):
    """Функция для скачивания карточки покупок."""
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
    for i, (name, data) in enumerate(y.items(), 1):
        page.drawString(75, height, (f"<{i}> {name} - {data['amount']}, "
                                     f"{data['measurement_unit']}"))
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
