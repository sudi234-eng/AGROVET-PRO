# inventory/views.py
from django.shortcuts import render
from .models import Product

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ProductSerializer

@api_view(['GET'])
def api_products(request):
    """
    API endpoint that returns all vet meds for the mobile app.
    """
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)
def product_catalog(request):
    # Only show items that are currently in stock
    products = Product.objects.filter(stock_quantity__gt=0)
    return render(request, 'inventory/catalog.html', {'products': products})

def index(request):
    # Fetch all products to show on the landing page
    products = Product.objects.all()
    return render(request, 'inventory/index.html', {'products': products})



