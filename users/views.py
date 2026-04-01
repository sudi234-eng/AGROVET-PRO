from django.shortcuts import render, redirect
from django.contrib.auth import login
from inventory.models import Product
from sales.models import ServiceOrder
from .decorators import role_required
from .forms import CustomUserCreationForm
from .models import User


@role_required('client', 'driver', 'admin')
def dashboard(request):
    user_order_count = 0
    paid_order_count = 0
    completed_order_count = 0
    recent_orders = []
    payment_items = []
    delivery_items = []

    if request.user.is_authenticated:
        user_orders = ServiceOrder.objects.filter(client=request.user).select_related('tracking')
        user_order_count = user_orders.count()
        paid_order_count = user_orders.filter(is_paid=True).count()
        completed_order_count = sum(1 for order in user_orders if order.display_status == 'Completed')
        recent_orders = list(user_orders.order_by('-order_date')[:5])
        payment_items = list(user_orders.order_by('-updated_at')[:5])
        delivery_items = list(user_orders.order_by('-updated_at')[:5])

    context = {
        'product_count': Product.objects.count(),
        'order_count': ServiceOrder.objects.count(),
        'driver_count': User.objects.filter(role=User.IS_DRIVER).count(),
        'client_count': User.objects.filter(role=User.IS_CLIENT).count(),
        'user_order_count': user_order_count,
        'paid_order_count': paid_order_count,
        'completed_order_count': completed_order_count,
        'recent_orders': recent_orders,
        'payment_items': payment_items,
        'delivery_items': delivery_items,
        'stock_items': list(Product.objects.order_by('stock_quantity', 'name')[:5]),
    }
    return render(request, 'dashboard.html', context)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})
