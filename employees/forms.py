from django import forms
from .models import ContractualEmployee, WorkRecord, FixedEmployee, FixedSalaryPayment, FixedWorkCredit

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

class FixedWorkCreditForm(forms.ModelForm):
    class Meta:
        model = FixedWorkCredit
        fields = ["date", "hours", "rate", "amount", "description"]
        labels = {
            "date": "Work Date",
            "hours": "Hours (optional)",
            "rate": "Rate (£/hr, optional)",
            "amount": "Credit Amount (£)",
            "description": "Description (optional)",
        }
        widgets = {
            "date": forms.DateInput(attrs={
                "type": "date",
                "class": "w-full border rounded-lg px-3 py-2 focus:outline-none "
                         "focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            }),
            "hours": forms.NumberInput(attrs={
                "step": "0.01", "min": "0",
                "placeholder": "e.g. 3.5",
                "class": "w-full border rounded-lg px-3 py-2 focus:outline-none "
                         "focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            }),
            "rate": forms.NumberInput(attrs={
                "step": "0.01", "min": "0",
                "placeholder": "e.g. 500",
                "class": "w-full border rounded-lg px-3 py-2 focus:outline-none "
                         "focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            }),
            "amount": forms.NumberInput(attrs={
                "step": "0.01", "min": "0",
                "placeholder": "Auto-calculated or enter directly",
                "class": "w-full border rounded-lg px-3 py-2 focus:outline-none "
                         "focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            }),
            "description": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "e.g. Overtime on weekend, project delivery, etc.",
                "class": "w-full border rounded-lg px-3 py-2 focus:outline-none "
                         "focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            }),
        }