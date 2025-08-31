# expenses/urls.py
from django.urls import path
from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.expense_list, name="list"),

    # Optional specialized list
    path("material/", views.material_list, name="material_list"),

    # Single create page (keep ONE route)
    path("new/", views.expense_new, name="create"),

    # Bulk add page
    path("bulk-add/", views.expense_bulk_add, name="bulk_add"),

    # Delete (with ?return= to preserve filters from the list page)
    path("<int:pk>/delete/", views.expense_delete, name="delete"),

    # Reports:
    # 1) Form-driven report (GET shows form; POST returns filtered PDF via xhtml2pdf)
    path("report/", views.expense_report, name="report"),

    # 2) Quick "all expenses" PDF generated via ReportLab
    #    >>> Rename your first report function to expense_report_pdf_all <<<
    path("report/pdf/", views.expense_report_pdf_all, name="report_pdf"),
]
