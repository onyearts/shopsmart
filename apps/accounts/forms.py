from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, ShopOwnerProfile, CustomerProfile, format_ghana_phone_number
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, RegexValidator

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

# Define phone validator for form (9 digits, no +233)
phone_form_validator = RegexValidator(
    regex=r'^\d{9}$',
    message="Enter 9 digits after +233 (e.g., 241234567)"
)

class ShopOwnerRegistrationForm(forms.ModelForm):
    phone = forms.CharField(
        validators=[phone_form_validator],
        widget=forms.TextInput(attrs={
            'pattern': '[0-9]{9}',
            'title': 'Enter 9 digits after +233 (e.g., 241234567)',
            'placeholder': '241234567',
            'maxlength': '9',
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

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Use the fixed formatting function
            formatted_phone = format_ghana_phone_number(phone)
            if not formatted_phone:
                raise ValidationError("Invalid phone number format")
            return formatted_phone
        return phone

class CustomerRegistrationForm(forms.ModelForm):
    phone = forms.CharField(
        validators=[phone_form_validator],
        widget=forms.TextInput(attrs={
            'pattern': '[0-9]{9}',
            'title': 'Enter 9 digits after +233 (e.g., 241234567)',
            'placeholder': '241234567',
            'maxlength': '9',
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

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Use the fixed formatting function
            formatted_phone = format_ghana_phone_number(phone)
            if not formatted_phone:
                raise ValidationError("Invalid phone number format")
            return formatted_phone
        raise ValidationError("Phone number is required")
    

# customers profile forms
# Add these at the bottom of your accounts/forms.py file

class EditUserForm(forms.ModelForm):
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

class EditCustomerForm(forms.ModelForm):
    phone = forms.CharField(
        validators=[RegexValidator(
            regex=r'^\+233\d{9}$',
            message="Phone must be in format: +233XXXXXXXXX"
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+233XXXXXXXXX',
            'pattern': r'\+233\d{9}',
            'title': 'Enter phone in format +233XXXXXXXXX'
        }),
        required=True
    )
    
    preferred_location = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Accra, Kumasi',
            'required': 'required'
        }),
        required=True
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': timezone.now().date().isoformat()
        }),
        required=False,
        help_text="Format: YYYY-MM-DD"
    )
    
    gender = forms.ChoiceField(
        choices=CustomerProfile.GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=False,
        help_text="Optional"
    )

    class Meta:
        model = CustomerProfile
        fields = ['phone', 'preferred_location', 'date_of_birth', 'gender']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not phone.startswith('+233'):
                raise forms.ValidationError("Phone must start with +233")
            if len(phone) != 13:
                raise forms.ValidationError("Phone must be 13 characters including +233")
            return phone
        raise forms.ValidationError("Phone number is required")
    

    
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