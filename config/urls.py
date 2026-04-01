from django.conf import settings # <--- ADD THIS LINE
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Agrovet Pro Admin"
admin.site.site_title = "Agrovet Pro Admin Portal"
admin.site.index_title = "Platform management"

urlpatterns = [
    path('admin/', admin.site.urls),
    # This points the empty '' (homepage) to your inventory app
    path('', include('inventory.urls')), 
    path('sales/', include('sales.urls')),
    # This points to your registration/login logic
    path('users/', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
