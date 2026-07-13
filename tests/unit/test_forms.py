"""
tests/unit/test_forms.py
Unit tests for RegisterForm, LoginForm, PatientProfileForm.
"""
import hashlib
import pytest
from core.forms import RegisterForm, LoginForm, PatientProfileForm

# UT-20 to UT-29: RegisterForm
@pytest.mark.django_db
class TestRegisterForm:

    def _valid_data(self, email="newuser@example.com"):
        return {
            'name': 'Test User',
            'email': email,
            'role': 'patient',
            'password': 'ValidPass@123',
            'confirm_password': 'ValidPass@123',
        }

    def test_UT20_valid_registration_form(self):
        """UT-20: Valid data passes form validation."""
        form = RegisterForm(data=self._valid_data())
        assert form.is_valid(), form.errors

    def test_UT21_missing_name(self):
        """UT-21: Missing name raises validation error."""
        data = self._valid_data()
        data['name'] = ''
        form = RegisterForm(data=data)
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_UT22_missing_email(self):
        """UT-22: Missing email raises validation error."""
        data = self._valid_data()
        data['email'] = ''
        form = RegisterForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_UT23_invalid_email_format(self):
        """UT-23: Invalid email format raises validation error."""
        data = self._valid_data()
        data['email'] = 'notanemail'
        form = RegisterForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_UT24_password_too_short(self):
        """UT-24: Password shorter than 8 chars raises error."""
        data = self._valid_data()
        data['password'] = 'short'
        data['confirm_password'] = 'short'
        form = RegisterForm(data=data)
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_UT25_passwords_do_not_match(self):
        """UT-25: Mismatched passwords raises confirm_password error."""
        data = self._valid_data()
        data['confirm_password'] = 'DifferentPass@999'
        form = RegisterForm(data=data)
        assert not form.is_valid()
        assert 'confirm_password' in form.errors

    def test_UT26_duplicate_email(self):
        """UT-26: Email already in use raises validation error."""
        from core.models import User
        User.objects.create(
            name="Existing",
            email="existing@example.com",
            password=hashlib.sha256(b"pass").hexdigest(),
            role="patient",
        )
        data = self._valid_data(email="existing@example.com")
        form = RegisterForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_UT27_name_too_short(self):
        """UT-27: Single character name raises validation error."""
        data = self._valid_data()
        data['name'] = 'X'
        form = RegisterForm(data=data)
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_UT28_email_lowercased(self):
        """UT-28: Email is lowercased during clean."""
        data = self._valid_data(email="UPPER@EXAMPLE.COM")
        form = RegisterForm(data=data)
        if form.is_valid():
            assert form.cleaned_data['email'] == "upper@example.com"

    def test_UT29_doctor_role_valid(self):
        """UT-29: Doctor role is accepted as valid choice."""
        data = self._valid_data()
        data['role'] = 'doctor'
        form = RegisterForm(data=data)
        assert form.is_valid(), form.errors

# UT-30 to UT-33: LoginForm
class TestLoginForm:

    def test_UT30_valid_login_form(self):
        """UT-30: Valid email and password passes."""
        form = LoginForm(data={'email': 'user@example.com', 'password': 'anypass'})
        assert form.is_valid()

    def test_UT31_missing_email(self):
        """UT-31: Missing email fails validation."""
        form = LoginForm(data={'email': '', 'password': 'anypass'})
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_UT32_missing_password(self):
        """UT-32: Missing password fails validation."""
        form = LoginForm(data={'email': 'user@example.com', 'password': ''})
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_UT33_invalid_email_format(self):
        """UT-33: Non-email string fails email field validation."""
        form = LoginForm(data={'email': 'notanemail', 'password': 'anypass'})
        assert not form.is_valid()
        assert 'email' in form.errors

# UT-34 to UT-38: PatientProfileForm
class TestPatientProfileForm:

    def test_UT34_valid_profile_form(self):
        """UT-34: Valid age, weight, gender passes."""
        form = PatientProfileForm(data={
            'age': 25, 'weight': 60, 'gender': 'female', 'is_pregnant': False
        })
        assert form.is_valid(), form.errors

    def test_UT35_age_zero_invalid(self):
        """UT-35: Age of 0 raises validation error."""
        form = PatientProfileForm(data={
            'age': 0, 'weight': 60, 'gender': 'male', 'is_pregnant': False
        })
        assert not form.is_valid()
        assert 'age' in form.errors

    def test_UT36_age_over_120_invalid(self):
        """UT-36: Age over 120 raises validation error."""
        form = PatientProfileForm(data={
            'age': 130, 'weight': 60, 'gender': 'male', 'is_pregnant': False
        })
        assert not form.is_valid()
        assert 'age' in form.errors

    def test_UT37_weight_zero_invalid(self):
        """UT-37: Weight of 0 raises validation error."""
        form = PatientProfileForm(data={
            'age': 25, 'weight': 0, 'gender': 'female', 'is_pregnant': False
        })
        assert not form.is_valid()
        assert 'weight' in form.errors

    def test_UT38_blank_fields_valid(self):
        """UT-38: All optional fields blank is valid (all fields are optional)."""
        form = PatientProfileForm(data={
            'age': '', 'weight': '', 'gender': '', 'is_pregnant': False
        })
        assert form.is_valid(), form.errors
