from django import forms
from django.contrib.auth.models import User
from .models import Product, StockMovement, UserRegistration


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "product_type",
            "quantity",
            "purchase_price",
            "unit_price",
            "expiration_date",
            "reorder_level",
        ]
        labels = {
            "product_type": "Product Type",
            "purchase_price": "Original/Purchase Price",
            "unit_price": "Selling Price",
            "expiration_date": "Expiration Date",
        }
        widgets = {
            "expiration_date": forms.DateInput(attrs={"type": "date"}),
        }


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ["movement_type", "quantity", "note"]
        widgets = {
            'movement_type': forms.RadioSelect(),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    
    class Meta:
        model = UserRegistration
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        if UserRegistration.objects.filter(username=username, is_approved=False).exists():
            raise forms.ValidationError("This username is already pending approval.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        if UserRegistration.objects.filter(email=email, is_approved=False).exists():
            raise forms.ValidationError("This email is already pending approval.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data
    
    def save(self, commit=True):
        registration = super().save(commit=False)
        from django.contrib.auth.hashers import make_password
        registration.password = make_password(registration.password)
        if commit:
            registration.save()
        return registration
