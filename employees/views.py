from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models.functions import Coalesce
from django.db.models import Q, Sum
from django.db.models import Q, Sum, Value, DecimalField, F
from django.db import models
from decimal import Decimal
from django.utils.timezone import now
from django.urls import reverse
from datetime import datetime
from .models import ContractualEmployee, WorkRecord, SalaryPayment, FixedEmployee, FixedSalaryPayment, AdvancePayment,FixedWorkRecord
from django import forms
from django.contrib import messages
from .forms import (
    ContractualEmployeeForm,
    WorkRecordForm,
    FixedEmployeeForm,
    FixedSalaryPaymentForm,
    FixedWorkRecordForm,
)

# Show all employees with totals



def employee_list(request):
    query = request.GET.get("q")  # search term
    type_filter = request.GET.get("type", "contractual")  # to control tab state

    # --- Contractual employees (existing logic) ---
    employees = ContractualEmployee.objects.all()
    if query:
        employees = employees.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        )

    # --- Fixed employees with computed totals ---
    fixed_qs = FixedEmployee.objects.all()
    if query:
        fixed_qs = fixed_qs.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        )

    fixed_employees = fixed_qs.annotate(
        total_paid_calc=Coalesce(
            Sum('fixed_payments__amount'),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        balance_calc=F('monthly_salary') - Coalesce(
            Sum('fixed_payments__amount'),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )

    # --- Summary cards ---
    # Salary totals
    temp_salary_total = (
        SalaryPayment.objects.aggregate(
            total=Coalesce(
                Sum("amount"),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
            )
        )["total"]
        or Decimal("0")
    )

    fixed_salary_total = (
        FixedSalaryPayment.objects.aggregate(
            total=Coalesce(
                Sum("amount"),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
            )
        )["total"]
        or Decimal("0")
    )
    contract_advances = sum(emp.total_advances for emp in ContractualEmployee.objects.all())
    fixed_advances = sum(
        (emp.total_paid_calc - emp.monthly_salary)
        if (emp.total_paid_calc - emp.monthly_salary) > 0 else Decimal("0")
        for emp in fixed_employees
    )

    advances_negative_total = contract_advances + fixed_advances

    salary_total_all = temp_salary_total + fixed_salary_total

   

    return render(request, "employees/employee_list.html", {
        "employees": employees,
        "fixed_employees": fixed_employees,
        "type_filter": type_filter,
        "query": query,

        # Summary cards
        "temp_salary_total": temp_salary_total,
        "fixed_salary_total": fixed_salary_total,
        "salary_total_all": salary_total_all,
        "advances_negative_total": advances_negative_total,
        "advances_negative_total": advances_negative_total,
    })



# Create a new employee
def employee_create(request):
    if request.method == "POST":
        form = ContractualEmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("employees:list")
    else:
        form = ContractualEmployeeForm()
    return render(request, "employees/employee_form.html", {"form": form})


# Add daily work record
def add_work(request, employee_id):
    employee = get_object_or_404(ContractualEmployee, pk=employee_id)

    if request.method == "POST":
        dates = request.POST.getlist("date")
        descriptions = request.POST.getlist("description")
        quantities = request.POST.getlist("quantity")
        item_prices = request.POST.getlist("item_price")

        for i in range(len(dates)):
            if quantities[i] and item_prices[i]:  # only save valid rows
                WorkRecord.objects.create(
                    employee=employee,
                    date=dates[i] or timezone.now().date(),
                    description=descriptions[i],
                    quantity=int(quantities[i]),
                    item_price=float(item_prices[i]),
                )
        return redirect("employees:report", employee_id)

    return render(request, "employees/work_form.html", {"employee": employee, "today": timezone.now().date()})


# Employee detail view
def employee_detail(request, employee_id):
    employee = get_object_or_404(ContractualEmployee, id=employee_id)
    context = {
        "employee": employee,
        "work_records": employee.work_records.all(),
        "salary_payments": employee.salary_payments.all(),
        "advances": employee.advance_payments.all(),
    }
    return render(request, "employees/employee_detail.html", context)

# Delete an employee
def employee_delete(request, employee_id):
    employee = get_object_or_404(ContractualEmployee, id=employee_id)

    if request.method == "POST":
        employee.delete()
        return redirect("employees:list")

    return render(request, "employees/employee_confirm_delete.html", {"employee": employee})


# Update an employee
def employee_update(request, employee_id):
    employee = get_object_or_404(ContractualEmployee, id=employee_id)
    if request.method == "POST":
        form = ContractualEmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect("employees:list")
    else:
        form = ContractualEmployeeForm(instance=employee)

    return render(request, "employees/employee_form.html", {
        "form": form,
        "title": f"Update Employee: {employee.name}"
    })


# Employee payslip
from datetime import date

def payslip(request, employee_id):
    employee = get_object_or_404(ContractualEmployee, id=employee_id)
    return render(request, "employees/payslip.html", {
        "employee": employee,
        "today": date.today(),
    })


# --- Salary Payment Form ---
from django import forms
from .models import SalaryPayment

class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ["amount", "date", "description"]
        widgets = {
            "amount": forms.NumberInput(attrs={
                "class": "w-full border rounded-lg p-3",
                "step": "0.01",
                "placeholder": "Enter amount"
            }),
            "date": forms.DateInput(attrs={
                "class": "w-full border rounded-lg p-3",
                "type": "date"
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full border rounded-lg p-3",
                "rows": 3,
                "placeholder": "Optional notes for this payment"
            }),
        }



# Add Salary (handles auto-advance if overpaid)
def add_salary(request, emp_id):
    employee = get_object_or_404(ContractualEmployee, id=emp_id)

    if request.method == "POST":
        form = SalaryPaymentForm(request.POST)
        if form.is_valid():
            salary_payment = form.save(commit=False)
            salary_payment.employee = employee
            salary_payment.save()
            print("Salary saved:", salary_payment.amount)
            return redirect("employees:detail", employee.id)
    else:
        form = SalaryPaymentForm()

    return render(request, "employees/add_salary.html", {
        "form": form,
        "employee": employee,
    })

# ✅ employees/views.py
def employee_report(request, pk):
    employee = get_object_or_404(ContractualEmployee, pk=pk)

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        work_records = employee.work_records.filter(date__range=[start_date, end_date])
        salary_payments = employee.salary_payments.filter(date__range=[start_date, end_date])
        advance_payments = employee.advance_payments.filter(date__range=[start_date, end_date])
    else:
        work_records = employee.work_records.all().order_by('-date')
        
        salary_payments = employee.salary_payments.all().order_by('-date')
        advance_payments = employee.advance_payments.all().order_by('-date')

    # Totals
    total_work = sum([wr.quantity * wr.item_price for wr in work_records])
    total_salary = sum([sp.amount for sp in salary_payments])
    total_advances = sum([ap.amount for ap in advance_payments])
    balance = total_work - (total_salary + total_advances)

    context = {
        "employee": employee,
        "start_date": start_date,
        "end_date": end_date,
        "work_records": work_records,
        "salary_payments": salary_payments,
        "advance_payments": advance_payments,
        "total_work": total_work,
        "total_salary": total_salary,
        "total_advances": total_advances,
        "balance": balance,
        "today": now().date(),
    }
    return render(request, "employees/employee_detail.html", context)

def delete_work_record(request, pk, record_id):
    employee = get_object_or_404(ContractualEmployee, pk=pk)
    # Get by id only, then verify ownership to avoid false 404s
    record = get_object_or_404(WorkRecord, id=record_id)

    # If the record doesn't belong to this employee, show an error instead of hard 404
    if getattr(record, "employee_id", None) != employee.id:
        messages.error(request, "That work record doesn’t belong to this employee.")
        return redirect(reverse("employees:report", args=[employee.id]) + "#work-records")

    if request.method == "POST":
        record.delete()
        messages.success(request, "Work record deleted.")
        return redirect(reverse("employees:report", args=[employee.id]) + "#work-records")

    # GET: confirmation page
    return render(request, "employees/confirm_delete_work_record.html", {
        "employee": employee,
        "record": record,
    })


# DELETE Salary Payment
def delete_salary_payment(request, pk, payment_id):
    employee = get_object_or_404(ContractualEmployee, pk=pk)
    payment = get_object_or_404(SalaryPayment, id=payment_id)

    if getattr(payment, "employee_id", None) != employee.id:
        messages.error(request, "That salary payment doesn’t belong to this employee.")
        return redirect(reverse("employees:report", args=[employee.id]) + "#salary-payments")

    if request.method == "POST":
        payment.delete()
        messages.success(request, "Salary payment deleted.")
        return redirect(reverse("employees:report", args=[employee.id]) + "#salary-payments")

    return render(request, "employees/confirm_delete_salary_payment.html", {
        "employee": employee,
        "payment": payment,
    })



# DELETE Advance Payment
def delete_advance_payment(request, pk, advance_id):
    employee = get_object_or_404(ContractualEmployee, pk=pk)
    advance = get_object_or_404(AdvancePayment, id=advance_id, employee=employee)
    advance.delete()
    return redirect(reverse("employees:report", args=[employee.id]))

# FIXED SALARY EMPLOYEES
def fixed_employee_list(request):
    employees = FixedEmployee.objects.all()
    return render(request, "employees/fixed_employee_list.html", {"employees": employees})

def fixed_employee_create(request):
    if request.method == "POST":
        form = FixedEmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/employees/?type=fixed")
    else:
        form = FixedEmployeeForm()
    return render(request, "employees/fixed_employee_form.html", {"form": form})

from datetime import datetime




def fixed_employee_add_salary(request, employee_id):
    employee = get_object_or_404(FixedEmployee, id=employee_id)

    if request.method == "POST":
        form = FixedSalaryPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.employee = employee
            payment.save()
            return redirect("employees:fixed_employee_report", pk=employee.id)
    else:
        form = FixedSalaryPaymentForm()

    return render(request, "employees/fixed_employee_add_salary.html", {
        "form": form,
        "employee": employee,
    })
    
def fixed_employee_delete(request, pk):
    employee = get_object_or_404(FixedEmployee, pk=pk)
    if request.method == "POST":
        employee.delete()
        return redirect("/employees/?type=fixed")
    return render(request, "employees/fixed_employee_confirm_delete.html", {"employee": employee})

def fixed_employee_update(request, pk):
    employee = get_object_or_404(FixedEmployee, pk=pk)
    if request.method == "POST":
        form = FixedEmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect("/employees/?type=fixed")
    else:
        form = FixedEmployeeForm(instance=employee)

    return render(request, "employees/fixed_employee_form.html", {
        "form": form,
        "title": f"Update Employee: {employee.name}"
    })

def fixed_employee_payslip(request, pk):
    employee = get_object_or_404(FixedEmployee, pk=pk)
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    payments = employee.fixed_payments.all()
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            payments = payments.filter(date__range=[start, end])
        except ValueError:
            pass

    total_paid = sum(p.amount for p in payments)
    total_salary = employee.monthly_salary
    balance = total_salary - total_paid

    return render(request, "employees/fixed_employee_payslip.html", {
        "employee": employee,
        "payments": payments,
        "total_paid": total_paid,
        "total_salary": total_salary,
        "balance": balance,
        "start_date": start_date,
        "end_date": end_date,
    })
# --- Add overtime work for a fixed employee ---
def fixed_employee_add_work(request, employee_id):
    employee = get_object_or_404(FixedEmployee, id=employee_id)
    if request.method == "POST":
        form = FixedWorkRecordForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.employee = employee
            rec.save()
            messages.success(request, "Work added.")
            return redirect("employees:fixed_employee_report", pk=employee.id)
    else:
        form = FixedWorkRecordForm(initial={"date": timezone.now().date()})
    return render(request, "employees/fixed_employee_add_work.html", {"form": form, "employee": employee})

# --- Fixed employee report (now includes overtime + date filters) ---
def fixed_employee_report(request, pk):
    employee = get_object_or_404(FixedEmployee, pk=pk)

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    payments = FixedSalaryPayment.objects.filter(employee=employee).order_by("-date")
    work_records = FixedWorkRecord.objects.filter(employee=employee).order_by("-date")

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            payments = payments.filter(date__range=[start, end])
            work_records = work_records.filter(date__range=[start, end])
        except ValueError:
            pass

    overtime_total = sum((w.amount for w in work_records), Decimal("0"))
    total_paid = sum((p.amount for p in payments), Decimal("0"))

    # Adjust total salary with overtime
    total_salary = employee.monthly_salary + overtime_total
    balance = total_salary - total_paid

    return render(request, "employees/fixed_employee_report.html", {
        "employee": employee,
        "payments": payments,
        "work_records": work_records,          # ← NEW
        "overtime_total": overtime_total,      # ← NEW
        "total_paid": total_paid,
        "total_salary": total_salary,          # monthly + overtime
        "balance": balance,
        "start_date": start_date,
        "end_date": end_date,
    })

# --- Delete actions from the fixed report tables (POST only) ---
def fixed_delete_work_record(request, pk, record_id):
    employee = get_object_or_404(FixedEmployee, pk=pk)
    rec = get_object_or_404(FixedWorkRecord, id=record_id)
    if rec.employee_id != employee.id:
        messages.error(request, "That work record doesn’t belong to this employee.")
        return redirect("employees:fixed_employee_report", pk=employee.id)
    if request.method == "POST":
        rec.delete()
        messages.success(request, "Work record deleted.")
    return redirect("employees:fixed_employee_report", pk=employee.id)

def fixed_delete_salary_payment(request, pk, payment_id):
    employee = get_object_or_404(FixedEmployee, pk=pk)
    pay = get_object_or_404(FixedSalaryPayment, id=payment_id)
    if pay.employee_id != employee.id:
        messages.error(request, "That salary payment doesn’t belong to this employee.")
        return redirect("employees:fixed_employee_report", pk=employee.id)
    if request.method == "POST":
        pay.delete()
        messages.success(request, "Salary payment deleted.")
    return redirect("employees:fixed_employee_report", pk=employee.id)