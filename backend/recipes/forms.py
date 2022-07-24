from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet


class RecipeFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        not_empty_row_count = 0
        deleted_not_empty_row_count = 0
        for form in self.forms:
            data = form.cleaned_data
            if data:
                not_empty_row_count += 1
                if data.get("DELETE"):
                    deleted_not_empty_row_count += 1
            if (
                not_empty_row_count == deleted_not_empty_row_count
                or not_empty_row_count == 0
            ):
                raise ValidationError(
                    "В рецепте должен быть хотя бы один ингредиент."
                )
