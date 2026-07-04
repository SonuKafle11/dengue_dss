import re
from django import forms
from .models import User

class RegisterForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Full Name', 'autofocus': True}),
        error_messages={'required': 'Full name is required.'},
    )
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'}),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Enter a valid email address.',
        },
    )
    role = forms.ChoiceField(
        choices=[('patient', 'Patient'), ('doctor', 'Doctor')],
        widget=forms.HiddenInput(),
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password (min 8 characters)'}),
        error_messages={
            'required': 'Password is required.',
            'min_length': 'Password must be at least 8 characters.',
        },
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        error_messages={'required': 'Please confirm your password.'},
    )

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Full name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters.')
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm  = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address', 'autofocus': True}),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Enter a valid email address.',
        },
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        error_messages={'required': 'Password is required.'},
    )

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()


class OTPForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': '6-digit code',
            'autofocus': True,
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'maxlength': '6',
        }),
        error_messages={
            'required': 'Please enter the OTP code.',
            'min_length': 'OTP must be exactly 6 digits.',
            'max_length': 'OTP must be exactly 6 digits.',
        },
    )

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code.isdigit():
            raise forms.ValidationError('OTP must contain digits only.')
        return code


class PatientProfileForm(forms.Form):
    GENDER_CHOICES = [
        ('', 'Select gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    age = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Age', 'min': '1', 'max': '120', 'step': '1'}),
    )
    weight = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Weight (kg)', 'min': '1', 'max': '300', 'step': '0.1'}),
    )
    height = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Height (cm)', 'min': '30', 'max': '250', 'step': '0.1'}),
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        widget=forms.Select(),
    )
    is_pregnant = forms.BooleanField(required=False)

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is not None:
            if age <= 0:
                raise forms.ValidationError('Age must be a positive number.')
            if age > 120:
                raise forms.ValidationError('Age must be 120 or below.')
        return age

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None:
            if weight <= 0:
                raise forms.ValidationError('Weight must be a positive number.')
            if weight > 300:
                raise forms.ValidationError('Weight must be 300 kg or below.')
        return weight

    def clean_height(self):
        height = self.cleaned_data.get('height')
        if height is not None:
            if height <= 0:
                raise forms.ValidationError('Height must be a positive number.')
            if height > 250:
                raise forms.ValidationError('Height must be 250 cm or below.')
        return height

    def clean_gender(self):
        gender = self.cleaned_data.get('gender', '')
        if gender and gender not in ('male', 'female', 'other'):
            raise forms.ValidationError('Select a valid gender.')
        return gender
