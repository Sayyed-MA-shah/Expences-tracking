from django.urls import path
from . import views

app_name = "employees"

urlpatterns = [
    # Employees
    path("", views.employee_list, name="list"),            # all employees
    path("new/", views.employee_create, name="create"),    # add new employee

    # Work records
    path("<int:employee_id>/work/", views.add_work, name="add_work"),

    # Advance payments
    # path("<int:employee_id>/advance/", views.add_advance, name="add_advance"),
    path("<int:employee_id>/", views.employee_detail, name="detail"),
     path("<int:employee_id>/delete/", views.employee_delete, name="delete"),
     path("<int:employee_id>/edit/", views.employee_update, name="update"),
     
    #  path("<int:employee_id>/payslip/", views.employee_payslip, name="payslip"),
     path("<int:employee_id>/payslip/", views.payslip, name="payslip"),
     path("<int:emp_id>/add_salary/", views.add_salary, name="add_salary"),
     path("<int:pk>/report/", views.employee_report, name="report"),

     path("<int:pk>/work/<int:record_id>/delete/", views.delete_work_record, name="delete_work_record"),
    path("<int:pk>/salary/<int:payment_id>/delete/", views.delete_salary_payment, name="delete_salary_payment"),
    path("<int:pk>/advance/<int:advance_id>/delete/", views.delete_advance_payment, name="delete_advance_payment"),





 
]


