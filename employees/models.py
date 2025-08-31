from django.db import models
from django.utils import timezone


class ContractualEmployee(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return self.name

    # --- Salary/Payment Calculations ---
    @property
    def total_earned(self):
        return sum(wr.quantity * wr.item_price for wr in self.work_records.all())

    @property
    def total_salary_paid(self):
        return sum(p.amount for p in self.salary_payments.all())

    @property
    def balance(self):
        return self.total_earned - self.total_salary_paid

    @property
    def total_advances(self):
        extra = self.total_salary_paid - self.total_earned
        return extra if extra > 0 else 0
    @property
    def balance_abs(self):
        return abs(self.balance)

    
 


class WorkRecord(models.Model):
    employee = models.ForeignKey(
        "ContractualEmployee",
        on_delete=models.CASCADE,
        
        related_name="work_records"
    )
    date = models.DateField(default=timezone.now)
    quantity = models.PositiveIntegerField()

    # New fields
    item_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ✅ safe default
    description = models.TextField(blank=True, null=True)  # ✅ optional

    
    def total_price(self):
        return self.quantity * self.item_price

    def __str__(self):
        return f"{self.employee.name} - {self.date} ({self.quantity} items)"

    @property
    def total(self):
        return self.quantity * self.item_price
    

class SalaryPayment(models.Model):
    employee = models.ForeignKey(
        "employees.ContractualEmployee", 
        on_delete=models.CASCADE, 
        related_name="salary_payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True)  # ✅ new field

    def save(self, *args, **kwargs):
        # Check balance before saving
        available_balance = self.employee.total_earned - self.employee.total_salary_paid

        super().save(*args, **kwargs)  # Save salary first

        # If salary > available balance, record the extra as advance
        overpay = self.amount - available_balance
        if overpay > 0:
            AdvancePayment.objects.create(
                employee=self.employee,
                amount=overpay,
                date=self.date,
                note=f"Auto-created from salary ID {self.id}"
            )

    def __str__(self):
        return f"Salary {self.amount} to {self.employee.name} on {self.date}"

    
# ---------------------- OTHER MODELS ----------------------


class FixedEmployee(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    @property
    def paid_amount(self):
        total = self.fixed_payments.aggregate(models.Sum("amount"))["amount__sum"] or 0
        return total

    @property
    def balance(self):
        return self.monthly_salary - self.paid_amount





class TemporaryWorker(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class TempWorkRecord(models.Model):
    worker = models.ForeignKey(TemporaryWorker, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    item_name = models.CharField(max_length=200, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def total_price(self):
        return self.quantity * (self.unit_price or self.worker.item_price)
class AdvancePayment(models.Model):
    employee = models.ForeignKey(
        ContractualEmployee,
        on_delete=models.CASCADE,
        related_name="advance_payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Advance {self.amount} for {self.employee.name} on {self.date}"



class FixedSalaryPayment(models.Model):
    employee = models.ForeignKey(
        FixedEmployee,
        on_delete=models.CASCADE,
        related_name="fixed_payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, default="")  # ← NEW

    def __str__(self):
        return f"{self.employee.name} - {self.amount} on {self.date}"

class FixedWorkCredit(models.Model):
    """
    Extra work/overtime credited to a fixed employee.
    If both hours and rate are provided, amount is auto-computed.
    Otherwise, you can enter amount directly.
    """
    employee = models.ForeignKey(
        'FixedEmployee',
        on_delete=models.CASCADE,
        related_name='work_credits'
    )
    date = models.DateField(default=timezone.now)
    hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rate  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.employee} • {self.date} • +{self.amount}"

    def clean(self):
        # Compute amount if not set but hours & rate exist
        if (self.amount is None or self.amount == 0) and self.hours and self.rate:
            self.amount = (self.hours * self.rate).quantize(Decimal('0.01'))