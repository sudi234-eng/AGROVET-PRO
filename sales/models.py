from django.db import models
from django.conf import settings
from inventory.models import Product

class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('In Transit', 'In Transit'),
        ('Arrived', 'Arrived at Destination'),
        ('Picked Up', 'Picked Up from Store'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    service = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    # Delivery details
    delivery_location = models.CharField(max_length=255, null=True, blank=True) 
    client_id_display = models.CharField(max_length=50, null=True, blank=True) 
    
    # Driver Assignment & Tracking
    # We use a string for the User model reference to avoid circular imports if your User is in another app
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='deliveries',
        help_text="The driver assigned to this delivery"
    )
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    
    order_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_paid = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='Pending'
    )
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} - {self.service.name} (Status: {self.status})"

    @property
    def display_status(self):
        tracking = getattr(self, 'tracking', None)
        tracking_status = getattr(tracking, 'status', None)

        if not self.is_paid:
            return 'Pending Payment'

        if tracking_status == 'Completed':
            return 'Completed'

        if tracking_status and tracking_status != 'Pending':
            return tracking_status

        if self.status == 'Pending':
            return 'Paid'

        return self.status

    class Meta:
        ordering = ['-order_date']
