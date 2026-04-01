from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from .models import User

INPUT_CLASS = (
    "form-control agro-input"
)


class StyledFieldsMixin:
    field_placeholders = {}

    def apply_widget_styles(self):
        for name, field in self.fields.items():
            widget = field.widget
            css_class = widget.attrs.get('class', '').strip()
            widget.attrs['class'] = f"{css_class} {INPUT_CLASS}".strip()
            if name in self.field_placeholders:
                widget.attrs.setdefault('placeholder', self.field_placeholders[name])


class CustomUserCreationForm(UserCreationForm):
    field_placeholders = {
        'username': 'Choose a username',
        'email': 'Enter email address',
        'id_number': 'National ID or farmer ID',
        'location': 'Town, area, or delivery location',
        'phone_number': '07XXXXXXXX',
        'password1': 'Create password',
        'password2': 'Confirm password',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        StyledFieldsMixin.apply_widget_styles(self)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'id_number', 'location', 'phone_number')

class CustomUserChangeForm(UserChangeForm):
    field_placeholders = {
        'username': 'Username',
        'email': 'Email address',
        'id_number': 'ID number',
        'location': 'Location',
        'phone_number': 'Phone number',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        StyledFieldsMixin.apply_widget_styles(self)

    class Meta:
        model = User
        fields = ('username', 'email', 'id_number', 'location', 'phone_number')


class CustomAuthenticationForm(AuthenticationForm, StyledFieldsMixin):
    field_placeholders = {
        'username': 'Enter your username',
        'password': 'Enter your password',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_widget_styles()
