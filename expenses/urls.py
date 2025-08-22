from django.urls import path
from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.expense_list, name="list"),   # ✅ fix here
    path("material/", views.material_list, name="material_list"),
    path("new/", views.expense_new, name="create"),
    path("new/", views.expense_new, name="new"), 
    path("<int:pk>/delete/", views.expense_delete, name="delete"),
    path("report/pdf/", views.expense_report, name="report_pdf"),
    path("bulk-add/", views.expense_bulk_add, name="bulk_add"),
     path("report/", views.expense_report, name="report"),

]
