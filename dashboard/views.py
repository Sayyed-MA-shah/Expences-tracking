from django.db.models import Sum
from django.views.generic import TemplateView
from expenses.models import Expense
from employees.models import ContractualEmployee, TemporaryWorker, FixedEmployee, AdvancePayment, SalaryPayment
from django.contrib.auth.mixins import LoginRequiredMixin
from payments.models import Payment



from django.utils import timezone
from datetime import datetime


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"
    login_url = "/accounts/login/"
    redirect_field_name = "next"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()
        month_start = today.replace(day=1)

        


        payins_month = Payment.objects.filter(date__range=[month_start, today], type='IN') \
            .aggregate(total=Sum('amount'))['total'] or 0
        
        salary_paid_month = (
            SalaryPayment.objects.filter(date__range=[month_start, today])
            .aggregate(total=Sum("amount"))["total"]
        or 0
        )
       
      

        payouts_month = (
            (Payment.objects.filter(date__range=[month_start, today], type='OUT')
             .aggregate(total=Sum('amount'))['total'] or 0)
            + (Expense.objects.filter(date__range=[month_start, today],
                              category=Expense.Category.MATERIAL)
             .aggregate(total=Sum('amount'))['total'] or 0)
            + (Expense.objects.filter(date__range=[month_start, today],
                              category=Expense.Category.RBG)
             .aggregate(total=Sum('amount'))['total'] or 0)
            + (Expense.objects.filter(date__range=[month_start, today],
                              category=Expense.Category.SETUP)
             .aggregate(total=Sum('amount'))['total'] or 0)
            + salary_paid_month   # ✅ only once
            )
  
        

        balance_month = payins_month - payouts_month

       
        # --- Employee Stats ---
        total_contractual = ContractualEmployee.objects.count()
        total_fixed = FixedEmployee.objects.count()
        total_employees = total_contractual + total_fixed

# total advances and salaries (calculated from employees)
        total_advances = sum(emp.total_advances for emp in ContractualEmployee.objects.all())
        total_salary_paid = sum(emp.total_salary_paid for emp in ContractualEmployee.objects.all())
        total_salary_due = FixedEmployee.objects.aggregate(total=Sum("monthly_salary"))["total"] or 0

# total balances
        total_contractual_balance = sum(emp.balance for emp in ContractualEmployee.objects.all())
        total_fixed_balance = sum(emp.balance for emp in FixedEmployee.objects.all())
        salary_pending = total_contractual_balance + total_fixed_balance
        

        # --- Date Range Stats (from filter form) ---
        start_date_str = self.request.GET.get("start_date")
        end_date_str = self.request.GET.get("end_date")

        start_date, end_date = None, None
        payins_range = payouts_range = balance_range = salary_paid_range = None  # 👈 include salary_paid_range

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                payins_range = Payment.objects.filter(
                    date__range=[start_date, end_date], type='IN'
                ).aggregate(total=Sum('amount'))['total'] or 0

                payouts_range = (
                    (Payment.objects.filter(date__range=[start_date, end_date], type='OUT')
                     .aggregate(total=Sum('amount'))['total'] or 0)
                    + (Expense.objects.filter(date__range=[start_date, end_date], category=Expense.Category.MATERIAL)
                       .aggregate(total=Sum('amount'))['total'] or 0)
                    + (Expense.objects.filter(date__range=[start_date, end_date], category=Expense.Category.RBG)
                       .aggregate(total=Sum('amount'))['total'] or 0)
                    + (Expense.objects.filter(date__range=[start_date, end_date], category=Expense.Category.SETUP)
                       .aggregate(total=Sum('amount'))['total'] or 0)
                )

                salary_paid_range = SalaryPayment.objects.filter(
                    date__range=[start_date, end_date]
                ).aggregate(total=Sum("amount"))["total"] or 0   # 👈 now tracked

                balance_range = payins_range - payouts_range

            except ValueError:
                pass

        
        # Add to context
        context.update({
            "payins_month": payins_month,
            "payouts_month": payouts_month,
            "balance_month": balance_month,
            "salary_paid_month": salary_paid_month,
            " total_advances" : total_advances,
            

            "start_date": start_date,
            "end_date": end_date,
            "payins_range": payins_range,
            "payouts_range": payouts_range,
            "balance_range": balance_range,
            "salary_paid_range": salary_paid_range,

            # new employee stats
            "total_advances": total_advances,
            "total_salary_paid": total_salary_paid,
            "total_contractual": total_contractual,
            "total_fixed": total_fixed,
            "total_employees": total_employees,
            "salary_pending": salary_pending,
         

            # NEW
            "total_salary_paid": total_salary_paid,
            
        })
        print("DEBUG salary_paid_range =>", salary_paid_range)


        return context
