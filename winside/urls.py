from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('login/', RedirectView.as_view(url='/accounts/login/')),
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('payments/', include(('payments.urls', 'payments'), namespace='payments')),
    path('expenses/', include(('expenses.urls', 'expenses'), namespace='expenses')),
    path('employees/', include(('employees.urls', 'employees'), namespace='employees')),
    path('', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
]
