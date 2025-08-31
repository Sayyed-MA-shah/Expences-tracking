from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Sum
from .models import Payment
from .forms import PaymentForm
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

# payments/views.py
from django.views.generic import ListView
from django.db.models import Sum
from datetime import datetime

class PaymentList(ListView):
    model = Payment
    template_name = 'payments/list.html'
    context_object_name = 'items'
    paginate_by = 50  # optional

    def _parse_date(self, s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None

    def get_queryset(self):
        tab = self.request.GET.get('tab', 'all').lower()
        start_str = self.request.GET.get('start')
        end_str = self.request.GET.get('end')

        start = self._parse_date(start_str)
        end = self._parse_date(end_str)
        if start and end and start > end:
            start, end = end, start  # swap if user reversed

        base_qs = super().get_queryset().order_by('-date', '-id')

        # Apply date window
        if start:
            base_qs = base_qs.filter(date__gte=start)
        if end:
            base_qs = base_qs.filter(date__lte=end)

        # Counts within the date window
        self._count_all = base_qs.count()
        self._count_in = base_qs.filter(type='IN').count()
        self._count_out = base_qs.filter(type='OUT').count()

        # Totals within the date window (cards)
        payin = base_qs.filter(type='IN').aggregate(total=Sum('amount'))['total'] or 0
        payout = base_qs.filter(type='OUT').aggregate(total=Sum('amount'))['total'] or 0
        self._total_payin = payin
        self._total_payout = payout
        self._balance = payin - payout

        # Tab filter
        qs = base_qs
        if tab == 'in':
            qs = qs.filter(type='IN')
        elif tab == 'out':
            qs = qs.filter(type='OUT')

        self._active_tab = tab
        self._visible_total = qs.aggregate(total=Sum('amount'))['total'] or 0

        # Keep the raw strings to prefill the form + preserve in links
        self._start_str = start_str or ''
        self._end_str = end_str or ''

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'active_tab': self._active_tab,
            'visible_total': self._visible_total,
            'count_all': self._count_all,
            'count_in': self._count_in,
            'count_out': self._count_out,
            'total_payin': self._total_payin,
            'total_payout': self._total_payout,
            'balance': self._balance,
            'start_date': self._start_str,
            'end_date': self._end_str,
        })
        return ctx

class PaymentCreate(CreateView):
    model = Payment
    form_class = PaymentForm
    success_url = reverse_lazy('payments:list')
    template_name = 'payments/create.html'

def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    # we keep where the user came from (tab/date filters/pagination)
    return_url = request.GET.get("return") or request.POST.get("return") or ""

    if request.method == "POST":
        payment.delete()
        messages.success(request, "Payment deleted.")

        # If we got a safe return URL, go back there and drop the user at the table
        if return_url and url_has_allowed_host_and_scheme(
            url=return_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure()
        ):
            # ensure we land back on the table area
            if "#payments-table" not in return_url:
                return redirect(f"{return_url}#payments-table")
            return redirect(return_url)

        # fallback: go to list with anchor
        return redirect(reverse("payments:list") + "#payments-table")

    # GET -> confirmation page
    context = {
        "payment": payment,
        "return_url": return_url,  # pass through so Cancel keeps filters too
    }
    return render(request, "payments/confirm_delete.html", context)
