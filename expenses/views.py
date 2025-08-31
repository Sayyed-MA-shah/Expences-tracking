from django.contrib import messages
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.template.loader import get_template
from xhtml2pdf import pisa
from itertools import zip_longest

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

# expenses/views.py
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import datetime
from .models import Expense
from .forms import ExpenseForm
from decimal import Decimal, InvalidOperation
from itertools import zip_longest
from django.http import HttpResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

# --- Daily expenses list with tabs + date filter ---
def expense_list(request):
    # ---- Read filters ----
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    dropdown_category = request.GET.get("category")  # from <select>, may be ""
    tab = (request.GET.get("tab") or "all").lower()  # tabs: all or category code lower()

    today = timezone.now().date()
    default_start = today.replace(day=1)

    # Parse dates (fallback to current month)
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else default_start
    except ValueError:
        start_date = default_start
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today
    except ValueError:
        end_date = today
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Base window queryset
    window_qs = Expense.objects.filter(date__range=[start_date, end_date]).order_by("-date", "-id")

    # Choices (code, label)
    choices = list(Expense.Category.choices)  # e.g. ("MATERIAL","Material"), ...
    codes = {code for code, _ in choices}
    labels = {code: label for code, label in choices}

    # Build tab definitions from choices
    # Tab key is just the code lowercased (e.g. "material", "rbg", "setup", ...)
    tab_defs = [{"key": code.lower(), "code": code, "label": labels[code]} for code in codes]
    tab_defs_sorted = sorted(tab_defs, key=lambda d: d["label"])  # nice stable order; tweak if needed

    # Which category filter to apply?
    selected_code = None
    # Priority 1: tab (if not 'all')
    if tab != "all":
        selected_code = next((d["code"] for d in tab_defs if d["key"] == tab), None)
    # Priority 2: dropdown category (if provided)
    if not selected_code and dropdown_category in codes:
        selected_code = dropdown_category
        tab = dropdown_category.lower()

    # Visible rows
    qs = window_qs.filter(category=selected_code) if selected_code else window_qs

    # Totals for the window (overall + per category)
    total_all = window_qs.aggregate(total=Sum("amount"))["total"] or 0
    totals_by_cat = {
        code: (window_qs.filter(category=code).aggregate(total=Sum("amount"))["total"] or 0)
        for code in codes
    }
    # Counts for badges
    count_all = window_qs.count()
    counts_by_cat = {code: window_qs.filter(category=code).count() for code in codes}
    visible_total = qs.aggregate(total=Sum("amount"))["total"] or 0

    # Convenience: pull well-known categories if present
    def t(code): return totals_by_cat.get(code, 0)
    total_material = t(getattr(Expense.Category, "MATERIAL", ""))
    total_rbg      = t(getattr(Expense.Category, "RBG", ""))
    total_setup    = t(getattr(Expense.Category, "SETUP", ""))
    total_logistics= t(getattr(Expense.Category, "LOGISTICS", ""))
    total_outsource= t(getattr(Expense.Category, "OUTSOURCE", ""))

    # Summary cards for a clean loop in template (label, value, color)
    # We only include the cards that actually exist in choices.
    color_by_key = {
        "material": "text-green-600",
        "rbg": "text-yellow-600",
        "setup": "text-red-600",
        "logistics": "text-indigo-600",
        "outsource": "text-pink-600",
    }
    summary_cards = []
    for d in tab_defs_sorted:
        key = d["key"]
        code = d["code"]
        summary_cards.append({
            "label": labels[code],
            "value": totals_by_cat[code],
            "color": color_by_key.get(key, "text-blue-600"),
        })

    context = {
        # rows
        "expenses": qs,

        # filters/state
        "start_date": start_date,
        "end_date": end_date,
        "category": selected_code or "",        # keeps <select> in sync
        "active_tab": tab if tab in {d["key"] for d in tab_defs} else "all",
        "tab_defs": tab_defs_sorted,

        # totals & counts
        "visible_total": visible_total,
        "total_all": total_all,
        "total_material": total_material,
        "total_rbg": total_rbg,
        "total_setup": total_setup,
        "total_logistics": total_logistics,
        "total_outsource": total_outsource,
        "count_all": count_all,
        "counts_by_cat": {d["key"]: counts_by_cat[d["code"]] for d in tab_defs_sorted},

        # for dropdown
        "categories": Expense.Category.choices,

        # dynamic cards
        "summary_cards": summary_cards,
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

def expense_report_pdf_all(request):
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
    """
    Bulk add expenses. Accepts multiple rows from a dynamic form.
    Now only uses main category (no sub_type).
    Works with both input names 'date' and 'date[]'.
    """
    if request.method == "POST":
        # helper to capture both name and name[]
        def inputs(name):
            return request.POST.getlist(name) or request.POST.getlist(f"{name}[]")

        dates = inputs("date")
        descriptions = inputs("description")
        categories = inputs("category")
        amounts = inputs("amount")

        if not any([dates, categories, amounts, descriptions]):
            messages.info(request, "No form rows submitted.")
            return redirect("expenses:list")

        to_create = []
        today = timezone.now().date()

        valid_categories = {key for key, _ in Expense.Category.choices}

        # date, category, amount, description
        rows = zip_longest(dates, categories, amounts, descriptions, fillvalue="")

        for date_str, cat_raw, amt_raw, desc_raw in rows:
            # Normalize inputs
            date_str = (date_str or "").strip()
            description = (desc_raw or "").strip()
            category = (cat_raw or "").strip().upper()
            amt_str = (amt_raw or "").strip()

            # Skip completely empty row
            if not any([date_str, category, description, amt_str]):
                continue

            # Validate category
            if category not in valid_categories:
                continue

            # Parse amount: strip currency symbols, commas
            amt_clean = amt_str.replace("£", "").replace(",", "").strip()
            try:
                amount = Decimal(amt_clean)
            except (InvalidOperation, TypeError):
                continue

            # Parse date, fallback to "today" if invalid or blank -> or None to let model default
            if date_str:
                try:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    parsed_date = today
            else:
                parsed_date = None  # let model default apply

            # Build model instance (sub_type always None now)
            kwargs = {
                "description": description,
                "category": category,
                "amount": amount,
                "sub_type": None,  # ensure it's cleared if the model still has the field
            }
            if parsed_date:
                kwargs["date"] = parsed_date

            to_create.append(Expense(**kwargs))

        if to_create:
            Expense.objects.bulk_create(to_create)
            messages.success(request, f"Added {len(to_create)} expense(s).")
        else:
            messages.info(request, "No valid rows to add. Check your inputs.")

        return redirect("expenses:list")

    # GET request - render page
    return render(request, "expenses/bulk_add.html", {"today": timezone.now().date()})

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