from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*allowed_roles, allow_staff_override=True):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if allow_staff_override and (user.is_staff or user.is_superuser):
                return view_func(request, *args, **kwargs)

            if getattr(user, 'role', None) in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.warning(request, "You do not have permission to open that page.")
            if user.is_authenticated:
                return redirect('dashboard')
            return redirect('login')

        return _wrapped_view

    return decorator


client_required = role_required('client')
driver_required = role_required('driver')
admin_required = role_required('admin')
