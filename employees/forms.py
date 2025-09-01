from django import forms
from .models import ContractualEmployee, WorkRecord, FixedEmployee, FixedSalaryPayment, FixedWorkRecord

class ContractualEmployeeForm(forms.ModelForm):
    class Meta:
        model = ContractualEmployee
        fields = ["name", "phone", "role"]

class WorkRecordForm(forms.ModelForm):
    class Meta:
        model = WorkRecord
        fields = ["date", "quantity", "item_price", "description"]  # ✅ new fields here

class FixedEmployeeForm(forms.ModelForm):
    class Meta:
        model = FixedEmployee
        fields = ["name", "phone", "role", "monthly_salary"]

class FixedSalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = FixedSalaryPayment
        fields = ["date", "amount", "description"]
        labels = {
            "amount": "Amount (£)",
            "description": "Description (optional)",
        }
        widgets = {
            "date": forms.DateInput(attrs={
                "type": "date",
                "class": "w-full border rounded-lg px-3 py-2 focus:outline-none "
                         "focus:ring-2 focus:ring-green-500 focus:border-green-500"
            }),
            "amount": forms.NumberInput(attrs={
                "step": "0.01",
                "min": "0",
                # left padding so the £ prefix in the template doesn't overlap
                "class": "w-full border rounded-lg pl-8 pr-3 py-2 focus:outline-none "
                         "focus:ring-2 focus:ring-green-500 focus:border-green-500"
            }),
            "description": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Optional notes (e.g. month covered, bonus, deduction)",
                "class": "w-full border rounded-lg px-3 py-2 focus:outline-none "
                         "focus:ring-2 focus:ring-green-500 focus:border-green-500"
            }),
        }
class FixedWorkRecordForm(forms.ModelForm):
    class Meta:
        model = FixedWorkRecord
        fields = ["date", "hours", "rate", "amount", "description"]
        labels = {
            "hours": "Hours",
            "rate": "Rate",
            "amount": "Amount (optional — auto if blank)",
            "description": "Description (optional)",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "w-full border rounded-lg px-3 py-2"}),
            "hours": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": "w-full border rounded-lg px-3 py-2"}),
            "rate": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": "w-full border rounded-lg px-3 py-2"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": "w-full border rounded-lg px-3 py-2"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "w-full border rounded-lg px-3 py-2"}),
        }

    def clean(self):
        cleaned = super().clean()
        hours = cleaned.get("hours") or 0
        rate = cleaned.get("rate") or 0
        amount = cleaned.get("amount") or 0
        if (not amount or amount == 0) and (hours == 0 or rate == 0):
            raise forms.ValidationError("Provide either an Amount, or Hours and Rate to calculate it.")
        return cleaned