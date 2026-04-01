from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), # This links the homepage to the view above
    path('catalog/', views.product_catalog, name='product_catalog'),
    path('api/products/', views.api_products, name='api_products'),
]
