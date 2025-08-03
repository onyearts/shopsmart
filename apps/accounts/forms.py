from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, ShopOwnerProfile, CustomerProfile
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


def validate_email_domain(value):
    """Prevent obvious typos in email domain."""
    common_typos = ['.con', '.ocm', '.cmo', '.cim']
    if any(value.endswith(typo) for typo in common_typos):
        raise ValidationError("Please enter a valid email address (e.g., example@gmail.com).")


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        validators=[validate_email_domain],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'id': 'password', 'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'id': 'confirm_password', 'class': 'form-control', 'placeholder': 'Confirm Password'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'First Name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Last Name'})


class ShopOwnerRegistrationForm(forms.ModelForm):
    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'pattern': r'\d{10}',
            'title': '10 digit phone number required',
            'placeholder': '1234567890',
            'maxlength': '10',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = ShopOwnerProfile
        fields = ['shop_name', 'address', 'phone']

    def __init__(self, *args, **kwargs):
        super(ShopOwnerRegistrationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label,
                'id': f'shop_{field_name}'
            })


class CustomerRegistrationForm(forms.ModelForm):
    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'pattern': '\d{10}',
            'title': '10 digit phone number required',
            'placeholder': '1234567890',
            'maxlength': '10',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = CustomerProfile
        fields = ['phone', 'preferred_location']

    def __init__(self, *args, **kwargs):
        super(CustomerRegistrationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label,
                'id': f'customer_{field_name}'
            })


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        from django.contrib.auth import authenticate
        user = authenticate(email=email, password=password)
        if not user:
            raise forms.ValidationError("Invalid email or password.")
        cleaned_data['user'] = user
        return cleaned_data