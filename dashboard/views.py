from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

from expenses.models import Expense
from payments.models import Payment
from employees.models import (
    ContractualEmployee,
    FixedEmployee,
    SalaryPayment,
    FixedSalaryPayment,
)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()
        month_start = today.replace(day=1)

        # === Pay-ins (this month) ===
        payins_month = Payment.objects.filter(
            date__range=[month_start, today], type='IN'
        ).aggregate(total=Sum('amount'))['total'] or Decimal("0")

        # === Salaries (this month) ===
        temp_salary_paid_month = (
            SalaryPayment.objects.filter(date__range=[month_start, today])
            .aggregate(total=Sum("amount"))["total"] or Decimal("0")
        )
        fixed_salary_paid_month = (
            FixedSalaryPayment.objects.filter(date__range=[month_start, today])
            .aggregate(total=Sum("amount"))["total"] or Decimal("0")
        )

        # === Payouts (this month) — include expenses + both types of salaries ===
        payouts_month = (
            (Payment.objects.filter(date__range=[month_start, today], type='OUT')
             .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
            + (Expense.objects.filter(date__range=[month_start, today], category=Expense.Category.MATERIAL)
               .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
            + (Expense.objects.filter(date__range=[month_start, today], category=Expense.Category.RBG)
               .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
            + (Expense.objects.filter(date__range=[month_start, today], category=Expense.Category.SETUP)
               .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
            + (Expense.objects.filter(date__range=[month_start, today], category=Expense.Category.LOGISTICS)
               .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
            + (Expense.objects.filter(date__range=[month_start, today], category=Expense.Category.OUTSOURCE)
               .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
            + temp_salary_paid_month
            + fixed_salary_paid_month
        )

        balance_month = payins_month - payouts_month

        # === Employee Counts ===
        total_contractual = ContractualEmployee.objects.count()
        total_fixed = FixedEmployee.objects.count()
        total_employees = total_contractual + total_fixed

        # === Salaries (Lifetime Totals) ===
        temp_salary_total = (
            SalaryPayment.objects.aggregate(
                total=Coalesce(
                    Sum("amount"),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
                )
            )["total"] or Decimal("0")
        )

        fixed_salary_total = (
            FixedSalaryPayment.objects.aggregate(
                total=Coalesce(
                    Sum("amount"),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
                )
            )["total"] or Decimal("0")
        )

        salary_total_all = temp_salary_total + fixed_salary_total

        # === Contractual Employee Totals (using existing model methods) ===
        total_contractual_salary_paid = sum(
            (emp.total_salary_paid or Decimal("0")) for emp in ContractualEmployee.objects.all()
        )
        total_contractual_balance = sum(
            (emp.balance or Decimal("0")) for emp in ContractualEmployee.objects.all()
        )
        total_contractual_advances = sum(
            (emp.total_advances or Decimal("0")) for emp in ContractualEmployee.objects.all()
        )

        # === Fixed Employee "Advances" Logic (treated as overpayment beyond monthly salary) ===
        fixed_paid_by_emp = dict(
            FixedSalaryPayment.objects.values('employee')
            .annotate(
                total=Coalesce(
                    Sum('amount'),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
                )
            )
            .values_list('employee', 'total')
        )

        fixed_advances_total = Decimal('0')
        for fe in FixedEmployee.objects.all():
            paid = fixed_paid_by_emp.get(fe.id, Decimal('0'))
            due = fe.monthly_salary or Decimal('0')
            overpay = paid - due
            if overpay > 0:
                fixed_advances_total += overpay

        # === Combined Advances ===
        total_advances_all = total_contractual_advances + fixed_advances_total

        # === Salary Pending (combined balances) ===
        # NOTE: If your FixedEmployee has a balance property, this will work.
        # If not, we assume balance = monthly_salary - total_paid
        total_fixed_balance = Decimal('0')
        for fe in FixedEmployee.objects.all():
            total_paid = fixed_paid_by_emp.get(fe.id, Decimal('0'))
            due = fe.monthly_salary or Decimal('0')
            total_fixed_balance += (due - total_paid)

        salary_pending = total_contractual_balance + total_fixed_balance

        # === Date Range Filters (also include fixed salaries in payout range) ===
        start_date_str = self.request.GET.get("start_date")
        end_date_str = self.request.GET.get("end_date")

        start_date = end_date = None
        payins_range = payouts_range = balance_range = None
        salary_paid_range = fixed_salary_paid_range = None

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                payins_range = Payment.objects.filter(
                    date__range=[start_date, end_date], type='IN'
                ).aggregate(total=Sum('amount'))['total'] or Decimal("0")

                payouts_range = (
                    (Payment.objects.filter(date__range=[start_date, end_date], type='OUT')
                     .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
                    + (Expense.objects.filter(date__range=[start_date, end_date], category=Expense.Category.MATERIAL)
                       .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
                    + (Expense.objects.filter(date__range=[start_date, end_date], category=Expense.Category.RBG)
                       .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
                    + (Expense.objects.filter(date__range=[start_date, end_date], category=Expense.Category.SETUP)
                       .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
                    +(Expense.objects.filter(date__range=[start_date, end_date], category=Expense.Category.OUTSOURCE)
                       .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
                    +(Expense.objects.filter(date__range=[start_date, end_date], category=Expense.Category.LOGISTICS)
                       .aggregate(total=Sum('amount'))['total'] or Decimal("0"))
                )

                salary_paid_range = SalaryPayment.objects.filter(
                    date__range=[start_date, end_date]
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

                fixed_salary_paid_range = FixedSalaryPayment.objects.filter(
                    date__range=[start_date, end_date]
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

                payouts_range += (salary_paid_range + fixed_salary_paid_range)
                balance_range = payins_range - payouts_range

            except ValueError:
                pass  # ignore invalid dates

        # === Context ===
        context.update({
            # Monthly overview
            "payins_month": payins_month,
            "payouts_month": payouts_month,
            "balance_month": balance_month,
            "salary_paid_month": temp_salary_paid_month,
            "fixed_salary_paid_month": fixed_salary_paid_month,
            "salary_total_month": temp_salary_paid_month + fixed_salary_paid_month,

            # Date range metrics
            "start_date": start_date,
            "end_date": end_date,
            "payins_range": payins_range,
            "payouts_range": payouts_range,
            "balance_range": balance_range,
            "salary_paid_range": salary_paid_range,
            "fixed_salary_paid_range": fixed_salary_paid_range,

            # Summary cards
            "temp_salary_total": temp_salary_total,
            "fixed_salary_total": fixed_salary_total,
            "salary_total_all": salary_total_all,
            "total_advances": total_advances_all,  # <-- Combined advances

            # Employee stats
            "total_salary_paid": total_contractual_salary_paid,
            "total_contractual": total_contractual,
            "total_fixed": total_fixed,
            "total_employees": total_employees,
            "salary_pending": salary_pending,
        })

        return context
