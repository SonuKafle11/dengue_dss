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
        widget=forms.NumberInput(attrs={'placeholder': 'Weight (kg)', 'min': '2', 'max': '200', 'step': '0.1'}),
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
        weight = self.cleaned_data.get("weight")
        age = self.cleaned_data.get("age")

        if weight is None or age is None:
            return weight

        if age >= 18:
            if weight < 30 or weight > 200:
                raise forms.ValidationError(
                "For adults (18 years and above), weight must be between 30 kg and 200 kg."
                )
        else:
            if weight < 2 or weight > 100:
                raise forms.ValidationError(
                "For children, weight must be between 2 kg and 100 kg."
            )

        return weight

    def clean_gender(self):
        gender = self.cleaned_data.get('gender', '')
        if gender and gender not in ('male', 'female', 'other'):
            raise forms.ValidationError('Select a valid gender.')
        return gender
