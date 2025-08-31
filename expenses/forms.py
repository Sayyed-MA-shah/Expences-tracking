from django import forms
from .models import Expense

BASE_INPUT = "w-full rounded-xl border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-600 focus:ring focus:ring-blue-200"
SELECT_INPUT = "w-full rounded-xl border border-gray-300 px-3 py-2 shadow-sm bg-white focus:border-blue-600 focus:ring focus:ring-blue-200"

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["date", "category", "description", "amount"]  # sub_type removed
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": BASE_INPUT}),
            "category": forms.Select(attrs={"class": SELECT_INPUT, "id": "id_category"}),
            "description": forms.TextInput(attrs={"placeholder": "Optional details", "class": BASE_INPUT}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": BASE_INPUT}),
        }

    # no special cleaning needed now
    def clean(self):
        return super().clean()
