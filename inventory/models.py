# inventory/models.py
from django.db import models

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Meds', 'Medication/Physical Goods'),
        ('Service', 'Professional Vet Service'),
    ]
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # New Fields
    stock_quantity = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"