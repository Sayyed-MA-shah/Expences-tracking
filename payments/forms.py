from django import forms
from .models import Payment
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['date','description','amount','type']
        widgets = {'date': forms.DateInput(attrs={'type':'date'})}
