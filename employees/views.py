from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import models
from django.utils.timezone import now
from django.urls import reverse
from datetime import datetime
from .models import ContractualEmployee, WorkRecord, SalaryPayment
from django import forms
from .forms import (
    ContractualEmployeeForm,
    WorkRecordForm,
    FixedEmployeeForm,
)

# Show all employees with totals
def employee_list(request):
    query = request.GET.get("q")  # get search term from URL
    employees = ContractualEmployee.objects.all()

    if query:
        employees = employees.filter(
            models.Q(name__icontains=query) | models.Q(phone__icontains=query)
        )

    return render(request, "employees/employee_list.html", {
        "employees": employees,
        "query": query,
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
class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ["amount"]


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
            return redirect("employees:list")
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
        work_records = employee.work_records.all()
        salary_payments = employee.salary_payments.all()
        advance_payments = employee.advance_payments.all()

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
    record = get_object_or_404(WorkRecord, id=record_id, employee=employee)
    record.delete()
    return redirect(reverse("employees:report", args=[employee.id]))

# DELETE Salary Payment
def delete_salary_payment(request, pk, payment_id):
    employee = get_object_or_404(ContractualEmployee, pk=pk)
    payment = get_object_or_404(SalaryPayment, id=payment_id, employee=employee)
    payment.delete()
    return redirect(reverse("employees:report", args=[employee.id]))

# DELETE Advance Payment
def delete_advance_payment(request, pk, advance_id):
    employee = get_object_or_404(ContractualEmployee, pk=pk)
    advance = get_object_or_404(AdvancePayment, id=advance_id, employee=employee)
    advance.delete()
    return redirect(reverse("employees:report", args=[employee.id]))