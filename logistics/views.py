# logistics/views.py
from django.shortcuts import render, get_object_or_404, redirect
from sales.models import ServiceOrder
from users.decorators import driver_required

@driver_required
def driver_dashboard(request):
    # Only show orders assigned to this driver that aren't finished
    active_orders = ServiceOrder.objects.filter(
        driver=request.user
    ).exclude(status='Completed').order_by('estimated_delivery')
    
    return render(request, 'logistics/driver_panel.html', {'orders': active_orders})

@driver_required
def update_delivery_status(request, order_id, new_status):
    order = get_object_or_404(ServiceOrder, id=order_id, driver=request.user)
    order.status = new_status
    order.save()
    return redirect('driver_dashboard')
