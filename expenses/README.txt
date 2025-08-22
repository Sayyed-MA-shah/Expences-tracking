
WINSIDE · expenses app (Daily Expenses)
Generated: 2025-08-18T17:38:54

What you get
------------
- Categories: Material, Rent/Bill/Guest (with sub-type), Setup Purchase
- Clean Tailwind UI for create and list
- Totals per category and filtered range
- Keeps expenses in their own table, BUT designed to be included in Payout on dashboard

Install
-------
1) Copy this 'expenses' folder into your Django project (replace existing app).
2) Add 'expenses' to INSTALLED_APPS if it's not there yet.
3) Include app urls in your project urls.py:
    path('expenses/', include('expenses.urls'))
4) Make migrations:
    python manage.py makemigrations expenses
    python manage.py migrate

Link to Dashboard (include expenses in payout)
---------------------------------------------
In your dashboard view, add the Expense sum to payouts.
Example for monthly and for custom date range:

    from django.utils import timezone
    from django.db.models import Sum
    from payments.models import Payment
    from expenses.models import Expense

    today = timezone.now().date()
    month_start = today.replace(day=1)

    payins_month = Payment.objects.filter(date__range=[month_start, today], type='IN').aggregate(total=Sum('amount'))['total'] or 0
    payouts_month = Payment.objects.filter(date__range=[month_start, today], type='OUT').aggregate(total=Sum('amount'))['total'] or 0
    expenses_month = Expense.objects.filter(date__range=[month_start, today]).aggregate(total=Sum('amount'))['total'] or 0
    payouts_month += expenses_month

    # For a custom range (start_date, end_date):
    payins_range = Payment.objects.filter(date__range=[start_date, end_date], type='IN').aggregate(total=Sum('amount'))['total'] or 0
    payouts_range = Payment.objects.filter(date__range=[start_date, end_date], type='OUT').aggregate(total=Sum('amount'))['total'] or 0
    expenses_range = Expense.objects.filter(date__range=[start_date, end_date]).aggregate(total=Sum('amount'))['total'] or 0
    payouts_range += expenses_range

That's it. The dashboard will show accurate Payout = Payments(OUT) + Daily Expenses.

Notes
-----
- The 'sub_type' field is only required when Category = Rent/Bill/Guest. The form enforces this.
- Tailwind classes are applied via widgets in forms.py.
- The form auto-hides the sub-type dropdown unless category is Rent/Bill/Guest.
