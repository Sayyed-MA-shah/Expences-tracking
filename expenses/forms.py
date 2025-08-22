
from django import forms
from .models import Expense


BASE_INPUT = "w-full rounded-xl border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-600 focus:ring focus:ring-blue-200"
SELECT_INPUT = "w-full rounded-xl border border-gray-300 px-3 py-2 shadow-sm bg-white focus:border-blue-600 focus:ring focus:ring-blue-200"


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["date", "category", "sub_type", "description", "amount"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": BASE_INPUT}),
            "category": forms.Select(attrs={"class": SELECT_INPUT, "id": "id_category"}),
            "sub_type": forms.Select(attrs={"class": SELECT_INPUT, "id": "id_sub_type"}),
            "description": forms.TextInput(attrs={"placeholder": "Optional details", "class": BASE_INPUT}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": BASE_INPUT}),
        }

    def clean(self):
        cleaned = super().clean()
        category = cleaned.get("category")
        sub_type = cleaned.get("sub_type")
        if category == Expense.Category.RBG and not sub_type:
            self.add_error("sub_type", "Please choose Rent/Bill/Guest.")
        if category != Expense.Category.RBG:
            cleaned["sub_type"] = None
        return cleaned
