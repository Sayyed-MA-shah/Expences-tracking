from django import forms
from .models import ContractualEmployee, WorkRecord, FixedEmployee, FixedSalaryPayment

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
        fields = ["amount"]