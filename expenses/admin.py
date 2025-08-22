
from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("date", "category", "sub_type", "description", "amount")
    list_filter = ("category", "sub_type", "date")
    search_fields = ("description",)
    ordering = ("-date", "-id")
