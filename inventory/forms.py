from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from .models import Product, StockMovement, UserRegistration, UserProfile


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
    
    def clean_name(self):
        """Validate product name for duplicates (case-insensitive)."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Product name cannot be empty.")
        
        # Check for existing product with same name (case-insensitive)
        existing_query = Product.objects.filter(name__iexact=name)
        
        # If editing, exclude the current product from the check
        if self.instance and self.instance.pk:
            existing_query = existing_query.exclude(pk=self.instance.pk)
        
        if existing_query.exists():
            existing_product = existing_query.first()
            raise forms.ValidationError(
                f'A product with the name "{existing_product.name}" already exists. '
                f'Product names must be unique (case-insensitive).'
            )
        
        return name


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
        fields = ['username', 'email', 'first_name', 'last_name', 'staff_role', 'phone', 'location', 'password']
        labels = {
            'staff_role': 'Staff Role',
            'location': 'Address',
        }
    
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


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile settings."""
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        help_texts = {
            'email': 'Email can be changed',
            'first_name': 'Read-only',
            'last_name': 'Read-only',
        }


class StaffEditForm(forms.Form):
    """Form for system admins editing staff account details."""
    username = forms.CharField(max_length=150, label='Username')
    first_name = forms.CharField(max_length=150, required=False, label='First Name')
    last_name = forms.CharField(max_length=150, required=False, label='Last Name')
    address = forms.CharField(max_length=255, required=False, label='Address')
    birthday = forms.DateField(
        required=False,
        label='Birthday',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    new_password = forms.CharField(
        required=False,
        label='New Password',
        widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        required=False,
        label='Confirm Password',
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, staff_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.staff_user = staff_user

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise forms.ValidationError("Username is required.")

        existing_users = User.objects.filter(username__iexact=username)
        if self.staff_user:
            existing_users = existing_users.exclude(pk=self.staff_user.pk)
        if existing_users.exists():
            raise forms.ValidationError("This username is already taken.")

        return username

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password or confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
            password_validation.validate_password(new_password, self.staff_user)

        return cleaned_data

    def save(self):
        staff_user = self.staff_user
        staff_user.username = self.cleaned_data['username']
        staff_user.first_name = self.cleaned_data.get('first_name', '').strip()
        staff_user.last_name = self.cleaned_data.get('last_name', '').strip()

        update_fields = ['username', 'first_name', 'last_name']
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            staff_user.set_password(new_password)
            update_fields.append('password')
        staff_user.save(update_fields=update_fields)

        profile = staff_user.profile
        profile.address = self.cleaned_data.get('address', '').strip()
        profile.birthday = self.cleaned_data.get('birthday')
        profile.save(update_fields=['address', 'birthday', 'updated_at'])

        return staff_user


class ThemePreferenceForm(forms.ModelForm):
    """Form for customizing theme preferences."""
    class Meta:
        model = UserProfile
        fields = ['dark_mode', 'primary_color']
        widgets = {
            'dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'primary_color': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'dark_mode': 'Enable Dark Mode',
            'primary_color': 'Primary Color Theme',
        }


class PasswordChangeForm(forms.Form):
    """Form for changing user password."""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Current Password'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='New Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm New Password'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match.")
        
        return cleaned_data
