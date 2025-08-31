from django.urls import path
from .views import PaymentList, PaymentCreate, payment_delete
app_name = 'payments'
urlpatterns = [ 
                    path("", PaymentList.as_view(), name="list"),
                    path("new/", PaymentCreate.as_view(), name="create"),
                    path("<int:pk>/delete/", payment_delete, name="delete"),
               
               ]
