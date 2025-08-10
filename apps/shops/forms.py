from django import forms
from .models import Product
from accounts.models import User, ShopOwnerProfile, CustomerProfile


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image', 'extra_note', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'extra_note': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'



class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'profile_picture']


class EditShopOwnerForm(forms.ModelForm):
    class Meta:
        model = ShopOwnerProfile
        fields = ['shop_name', 'phone', 'address', 'map_address', 'latitude', 'longitude', 'postal_code', 'city']

    def __init__(self, *args, **kwargs):
        super(EditShopOwnerForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Make all fields required except hidden map-related fields
            if field_name not in ['map_address', 'latitude', 'longitude']:
                field.required = True
                field.widget.attrs['class'] = 'form-control'
            else:
                field.required = False
        
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not (phone.startswith('0') and len(phone) == 10) and not (phone.startswith('+233') and len(phone) == 13):
                raise forms.ValidationError("Phone must be in 0XXXXXXXXX or +233XXXXXXXXX format")
        return phone



class EditCustomerForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['phone', 'preferred_location']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not (phone.startswith('0') and len(phone) == 10) and not (phone.startswith('+233') and len(phone) == 13):
                raise forms.ValidationError("Phone must be in 0XXXXXXXXX or +233XXXXXXXXX format")
        return phone