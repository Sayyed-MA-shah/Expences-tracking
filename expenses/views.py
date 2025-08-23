from django.contrib import messages
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.template.loader import get_template
from xhtml2pdf import pisa

import io
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from .models import Expense
from .forms import ExpenseForm
from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from django.utils import timezone
from .models import Expense
from .forms import ExpenseForm
from decimal import Decimal

from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .models import Expense


# expenses/views.py
def material_list(request):
    today = timezone.now().date()
    start_date = today.replace(day=1)
    end_date = today

    qs = Expense.objects.filter(
        date__range=[start_date, end_date],
        category=Expense.Category.MATERIAL
    ).order_by("-date", "-id")

    total_material = qs.aggregate(total=Sum("amount"))["total"] or 0

    context = {
        "expenses": qs,
        "total_material": total_material,
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, "expenses/material_list.html", context)

def expense_list(request):
    # Filters
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    category = request.GET.get("category")  # MATERIAL / RBG / SETUP or ""

    today = timezone.now().date()
    default_start = today.replace(day=1)

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_date, end_date = default_start, today
    else:
        start_date, end_date = default_start, today

    qs = Expense.objects.filter(date__range=[start_date, end_date]).order_by("-date", "-id")
    if category in dict(Expense.Category.choices):
        qs = qs.filter(category=category)

    # Totals
    total_all = qs.aggregate(total=Sum("amount"))["total"] or 0
    total_material = qs.filter(category=Expense.Category.MATERIAL).aggregate(total=Sum("amount"))["total"] or 0
    total_rbg = qs.filter(category=Expense.Category.RBG).aggregate(total=Sum("amount"))["total"] or 0
    total_setup = qs.filter(category=Expense.Category.SETUP).aggregate(total=Sum("amount"))["total"] or 0

    context = {
        "expenses": qs,
        "start_date": start_date,
        "end_date": end_date,
        "category": category or "",
        "total_all": total_all,
        "total_material": total_material,
        "total_rbg": total_rbg,
        "total_setup": total_setup,
        "categories": Expense.Category.choices,
    }
    return render(request, "expenses/list.html", context)


def expense_new(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.date = timezone.now()
            expense.save()
            messages.success(request, f"Expense of £{expense.amount} saved successfully ✅")
            return redirect("expenses:list")
        else:
            messages.error(request, "There was an error saving the expense. Please check the form.")
    else:
        form = ExpenseForm()

    return render(request, "expenses/new.html", {"form": form})


def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted successfully ✅")
        return redirect("expenses:list")

    return render(request, "expenses/confirm_delete.html", {"expense": expense})

def expense_report(request):
    # Get all expenses (you can add filters if needed)
    expenses = Expense.objects.all().order_by("-date")

    # Create PDF buffer
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Expense Report ")

    # Table header
    y = height - 100
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Date")
    p.drawString(150, y, "Category")
    p.drawString(300, y, "Description")
    p.drawString(500, y, "Amount")

    # Table content
    p.setFont("Helvetica", 10)
    y -= 20
    for exp in expenses:
        p.drawString(50, y, str(exp.date))
        p.drawString(150, y, exp.get_category_display())
        p.drawString(300, y, exp.description or "-")
        p.drawRightString(550, y, str(exp.amount))
        y -= 20
        if y < 50:  # new page
            p.showPage()
            y = height - 50

    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type="application/pdf")

# ___________EXPENCES
def expense_bulk_add(request):
    if request.method == "POST":
        dates = request.POST.getlist("date[]")
        categories = request.POST.getlist("category[]")
        amounts = request.POST.getlist("amount[]")
        descriptions = request.POST.getlist("description[]")

        for date, category, amount, description in zip(dates, categories, amounts, descriptions):
            if amount:  # skip empty rows
                Expense.objects.create(
                    date=date,
                    category=category,
                    amount=amount,
                    description=description
                )
        return redirect("expenses:list")

    return render(request, "expenses/bulk_add.html")

# ///////////////////////////////Generate reprot////////////////
def expense_report(request):
    expenses = []
    total_material = total_rbg = total_setup = total_all = 0
    start_date = end_date = selected_category = None

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        selected_category = request.POST.get("category")

        if start_date and end_date:
            expenses = Expense.objects.filter(date__range=[start_date, end_date])

            if selected_category:  # filter by category if chosen
                expenses = expenses.filter(category=selected_category)

        # Totals
        total_material = Expense.objects.filter(date__range=[start_date, end_date], category="MATERIAL").aggregate(total=Sum("amount"))["total"] or 0
        total_rbg = Expense.objects.filter(date__range=[start_date, end_date], category="RBG").aggregate(total=Sum("amount"))["total"] or 0
        total_setup = Expense.objects.filter(date__range=[start_date, end_date], category="SETUP").aggregate(total=Sum("amount"))["total"] or 0
        total_all = Expense.objects.filter(date__range=[start_date, end_date]).aggregate(total=Sum("amount"))["total"] or 0

        # ✅ Generate PDF
        template_path = "expenses/report_pdf.html"
        context = {
            "expenses": expenses,
            "total_material": total_material,
            "total_rbg": total_rbg,
            "total_setup": total_setup,
            "total_all": total_all,
            "start_date": start_date,
            "end_date": end_date,
            "selected_category": selected_category,
        }
        template = get_template(template_path)
        html = template.render(context)

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="expenses_report.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    return render(request, "expenses/report_form.html", {"selected_category": selected_category})
# /////////////////////////////end Generate reprot////////////////






