from django.db import models

class Payment(models.Model):
    TYPE_CHOICES = [('IN','Pay-in'), ('OUT','Pay-out')]
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, default='IN')
    class Meta: ordering = ['-date','-id']
    def __str__(self): return f"{self.date} {self.get_type_display()} £{self.amount}"
