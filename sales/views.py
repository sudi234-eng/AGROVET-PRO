# sales/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
from inventory.models import Product
from users.decorators import client_required, driver_required
from .models import ServiceOrder
from logistics.models import ServiceTracking

import json
import requests
import base64
from datetime import datetime
from requests.auth import HTTPBasicAuth

# --- MPESA HELPER FUNCTIONS ---

def get_mpesa_access_token():
    """Fetch the OAuth2 token from Safaricom"""
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    try:
        res = requests.get(url, auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
        return res.json().get('access_token')
    except Exception:
        return None

def initiate_stk_push(order, phone_number, callback_url):
    """Triggers the STK Push popup on the client's phone"""
    token = get_mpesa_access_token()
    if not token:
        return {'success': False, 'message': 'Unable to authenticate with M-Pesa right now.'}

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode()

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(order.service.price),
        "PartyA": phone_number, 
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": f"Order{order.id}",
        "TransactionDesc": f"Payment for {order.service.name}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return {'success': False, 'message': 'M-Pesa request failed before confirmation.'}

    checkout_request_id = data.get('CheckoutRequestID')
    if data.get('ResponseCode') == '0' and checkout_request_id:
        order.transaction_id = checkout_request_id
        order.save(update_fields=['transaction_id', 'updated_at'])
        return {
            'success': True,
            'message': data.get('CustomerMessage', 'M-Pesa prompt sent to your phone.'),
        }

    return {
        'success': False,
        'message': data.get('errorMessage') or data.get('ResponseDescription') or 'M-Pesa request was not accepted.',
    }


def _extract_callback_value(items, key):
    for item in items:
        if item.get('Name') == key:
            return item.get('Value')
    return None

# --- CLIENT VIEWS ---

@client_required
def create_order(request, product_id):
    """Creates order, starts tracking, and triggers M-Pesa payment."""
    product = get_object_or_404(Product, id=product_id)
    
    # 1. Get the user's location safety check
    user_loc = getattr(request.user, 'location', 'Pick up at Store')
    if not user_loc:
        user_loc = 'Pick up at Store'

    # 2. Create the Order
    order = ServiceOrder.objects.create(
        client=request.user,
        service=product,
        quantity=1,
        delivery_location=user_loc,
        client_id_display=getattr(request.user, 'id_number', '000') or '000',
        status='Pending'
    )
    
    # 3. Automatically create the tracking entry
    tracking = ServiceTracking.objects.create(order=order, status='Pending', notes='Awaiting M-Pesa payment confirmation.')
    
    # 4. Trigger M-Pesa Payment
    user_phone = getattr(request.user, 'phone_number', None)
    if user_phone:
        callback_url = request.build_absolute_uri(reverse('mpesa_callback'))
        payment_result = initiate_stk_push(order, user_phone, callback_url)
        if payment_result['success']:
            messages.success(request, payment_result['message'])
        else:
            tracking.notes = payment_result['message']
            tracking.save(update_fields=['notes', 'last_updated'])
            messages.warning(request, payment_result['message'])
    else:
        messages.warning(request, 'Add a phone number to receive the M-Pesa payment prompt for this order.')
    
    return redirect('order_history')

@client_required
def order_history(request):
    """Displays user orders and tracking status"""
    selected_status = request.GET.get('status', '').strip()

    base_orders = ServiceOrder.objects.filter(client=request.user).select_related(
        'service',
        'driver',
        'tracking',
        'tracking__driver',
    )

    all_orders = list(base_orders.order_by('-id'))

    status_labels = {
        key: label for key, label in ServiceOrder.STATUS_CHOICES
    }
    status_labels.update({
        key: label for key, label in ServiceTracking.STATUS_CHOICES
    })
    status_labels['Pending Payment'] = 'Pending Payment'

    analytics = {}
    for order in all_orders:
        status_key = order.display_status
        analytics[status_key] = analytics.get(status_key, 0) + 1

    status_filters = [
        {'value': key, 'label': label, 'count': analytics.get(key, 0)}
        for key, label in status_labels.items()
        if analytics.get(key, 0)
    ]

    filtered_orders = all_orders
    if selected_status:
        filtered_orders = [
            order for order in all_orders
            if order.display_status == selected_status
        ]

    total_orders = len(all_orders)
    recent_status = all_orders[0].display_status if all_orders else 'None'

    context = {
        'orders': filtered_orders,
        'all_order_count': total_orders,
        'recent_status': recent_status,
        'selected_status': selected_status,
        'status_filters': status_filters,
        'status_analytics': sorted(
            analytics.items(),
            key=lambda item: (-item[1], item[0])
        )[:4],
    }
    return render(request, 'sales/order_history.html', context)

@csrf_exempt
def mpesa_callback(request):
    """Safaricom callback to confirm payment"""
    if request.method == 'POST':
        stk_data = json.loads(request.body or '{}')
        callback = stk_data.get('Body', {}).get('stkCallback', {})
        checkout_request_id = callback.get('CheckoutRequestID')
        result_code = callback.get('ResultCode')
        result_desc = callback.get('ResultDesc', '')

        order = ServiceOrder.objects.filter(transaction_id=checkout_request_id).first()
        if order:
            tracking, _ = ServiceTracking.objects.get_or_create(
                order=order,
                defaults={'status': 'Pending'}
            )

            if result_code == 0:
                items = callback.get('CallbackMetadata', {}).get('Item', [])
                receipt_number = _extract_callback_value(items, 'MpesaReceiptNumber')
                order.is_paid = True
                order.status = 'Paid'
                order.transaction_id = receipt_number or checkout_request_id
                order.save(update_fields=['is_paid', 'status', 'transaction_id', 'updated_at'])

                tracking.status = 'Pending'
                tracking.notes = f"Payment confirmed via M-Pesa. Receipt: {receipt_number or checkout_request_id}"
                tracking.save(update_fields=['status', 'notes', 'last_updated'])
            else:
                order.is_paid = False
                order.status = 'Pending'
                order.save(update_fields=['is_paid', 'status', 'updated_at'])

                tracking.status = 'Pending'
                tracking.notes = f"Payment unsuccessful: {result_desc or 'Request cancelled or failed.'}"
                tracking.save(update_fields=['status', 'notes', 'last_updated'])

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    return JsonResponse({"ResultCode": 1, "ResultDesc": "Rejected"})

# --- DRIVER PANEL VIEWS ---

@driver_required
def driver_dashboard(request):
    """Displays orders assigned to the logged-in driver"""
    # Only show orders assigned to this driver that aren't completed yet
    my_deliveries = ServiceOrder.objects.filter(driver=request.user).exclude(
        status__in=['Completed', 'Cancelled']
    ).select_related('service', 'tracking').order_by('-updated_at')

    context = {
        'orders': my_deliveries,
        'delivery_count': my_deliveries.count(),
        'arrived_count': my_deliveries.filter(status='Arrived').count(),
        'transit_count': my_deliveries.filter(status='In Transit').count(),
    }
    return render(request, 'sales/driver_panel.html', context)

@driver_required
def update_order_status(request, order_id, new_status):
    """Allows driver to update order and tracking progress"""
    # Security: Ensure only the assigned driver can update the order
    order = get_object_or_404(ServiceOrder, id=order_id, driver=request.user)
    
    # 1. Update the Order Model
    order.status = new_status
    order.save()
    
    # 2. Update the Tracking Model (so client sees it)
    tracking, created = ServiceTracking.objects.get_or_create(order=order)
    tracking_status_map = {
        'Pending': 'Pending',
        'Paid': 'Pending',
        'In Transit': 'In Transit',
        'Arrived': 'On Site',
        'Picked Up': 'Completed',
        'Completed': 'Completed',
        'Cancelled': 'Pending',
    }
    tracking.status = tracking_status_map.get(new_status, 'Pending')
    if new_status == 'Arrived':
        tracking.notes = 'Driver confirmed the delivery has arrived at destination.'
        messages.success(request, f'Order #{order.id} marked as arrived.')
    elif new_status == 'Completed':
        tracking.notes = 'Driver confirmed the delivery has been completed.'
        messages.success(request, f'Order #{order.id} marked as completed.')
    elif new_status == 'In Transit':
        tracking.notes = 'Driver confirmed the order is now in transit.'
        messages.success(request, f'Order #{order.id} marked as in transit.')
    tracking.save()
    
    return redirect('driver_dashboard')
