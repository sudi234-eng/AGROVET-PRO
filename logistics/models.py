from django.db import models
from django.conf import settings
from sales.models import ServiceOrder

class ServiceTracking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Order Received'),
        ('Dispatched', 'Vet/Driver Dispatched'),
        ('In Transit', 'In Transit to Location'),
        ('On Site', 'Service being Delivered'),
        ('Completed', 'Completed/Delivered'),
    ]
    
    order = models.OneToOneField(ServiceOrder, on_delete=models.CASCADE, related_name='tracking')
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'role': 'driver'} # This ensures only Mike can be assigned
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True) # e.g., "Arrived at Kiambu gate"

    def __str__(self):
        return f"Tracking for Order {self.order.id}: {self.status}"