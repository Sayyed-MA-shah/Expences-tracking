from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Sum
from .models import Payment
from .forms import PaymentForm

class PaymentList(ListView):
    model = Payment
    template_name = 'payments/list.html'
    context_object_name = 'items'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        payin = Payment.objects.filter(type='IN').aggregate(total=Sum('amount'))['total'] or 0
        payout = Payment.objects.filter(type='OUT').aggregate(total=Sum('amount'))['total'] or 0
        balance = payin - payout
        ctx.update({'total_payin': payin, 'total_payout': payout, 'balance': balance})
        return ctx

class PaymentCreate(CreateView):
    model = Payment
    form_class = PaymentForm
    success_url = reverse_lazy('payments:list')
    template_name = 'payments/create.html'
