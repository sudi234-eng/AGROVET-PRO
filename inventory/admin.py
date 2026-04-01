# inventory/admin.py
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    #list_display = ('name', 'category', 'price', 'stock_quantity', 'times_purchased')
    list_filter = ('category',)
    search_fields = ('name',)