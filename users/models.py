from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    # Defining roles so you can distinguish between John (Client) and Mike (Driver)
    IS_CLIENT = 'client'
    IS_DRIVER = 'driver'
    IS_ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (IS_CLIENT, 'Client'),
        (IS_DRIVER, 'Driver'),
        (IS_ADMIN, 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=IS_CLIENT)
    
    # Fields John needs for remote delivery tracking
    id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True) # e.g., Kiambu
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    # These "related_name" arguments are MANDATORY to stop the 
    # (fields.E304) errors you saw earlier.
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def save(self, *args, **kwargs):
        if self.is_superuser or self.is_staff:
            self.role = self.IS_ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
