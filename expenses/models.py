
from django.db import models
from django.utils import timezone


class Expense(models.Model):
    class Category(models.TextChoices):
        MATERIAL = "MATERIAL", "Material Expense"
        RBG = "RBG", "Rent / Bill / Guest"
        SETUP = "SETUP", "Setup Purchase"
        OUTSOURCE = "OUTSOURCE", "Outsource"
        LOGISTICS = "LOGISTICS", "Logistics"
    

    class SubType(models.TextChoices):
        RENT = "RENT", "Rent"
        BILL = "BILL", "Bill"
        GUEST = "GUEST", "Guest"
        

    date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=20, choices=Category.choices)
    # Only used when category == RBG
    sub_type = models.CharField(max_length=10, choices=SubType.choices, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.category == self.Category.RBG and not self.sub_type:
            raise ValidationError({"sub_type": "Required for Rent/Bill/Guest expenses."})
        if self.category != self.Category.RBG and self.sub_type:
            # prevent stray data
            self.sub_type = None

    def __str__(self):
        label = self.get_category_display()
        if self.category == self.Category.RBG and self.sub_type:
            label = f"{label} · {self.get_sub_type_display()}"
        return f"{label}: {self.amount} on {self.date}"
