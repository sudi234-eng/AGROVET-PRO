from django.urls import path
from . import views

urlpatterns = [
    # This 'name' MUST match the one in your index.html
    path('order/<int:product_id>/', views.create_order, name='create_order'),
    path('history/', views.order_history, name='order_history'), # <--- Add this!
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('driver/order/<int:order_id>/update/<str:new_status>/', 
         views.update_order_status, name='update_order_status'),
    
]
                   

