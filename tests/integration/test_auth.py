"""
tests/integration/test_auth.py
Integration tests for registration, login, and logout flows.
Uses Django test Client to simulate HTTP requests.
"""
import hashlib
import pytest
from django.urls import reverse
from django.test import Client
from core.models import User


def make_password(raw):
    return hashlib.sha256(raw.encode()).hexdigest()

# IT-01 to IT-08: Registration
@pytest.mark.django_db
class TestRegistration:

    def test_IT01_register_page_loads(self):
        """IT-01: GET /register/ returns 200."""
        client = Client()
        response = client.get(reverse('register'))
        assert response.status_code == 200

    def test_IT02_successful_patient_registration(self):
        """IT-02: Valid POST to /register/ creates a patient user and redirects to login."""
        client = Client()
        response = client.post(reverse('register'), {
            'name': 'New Patient',
            'email': 'newpatient@example.com',
            'password': 'ValidPass@123',
            'confirm_password': 'ValidPass@123',
            'role': 'patient',
        }, follow=True)
        assert response.status_code == 200
        assert User.objects.filter(email='newpatient@example.com').exists()
        final_url = response.redirect_chain[-1][0] if response.redirect_chain else ''
        assert '/login/' in final_url or 'login' in str(response.content)

    def test_IT03_successful_doctor_registration(self):
        """IT-03: Valid POST to /register/?as=doctor creates a doctor user."""
        client = Client()
        client.post(reverse('register') + '?as=doctor', {
            'name': 'New Doctor',
            'email': 'newdoctor@example.com',
            'password': 'ValidPass@123',
            'confirm_password': 'ValidPass@123',
            'role': 'doctor',
        })
        user = User.objects.filter(email='newdoctor@example.com').first()
        assert user is not None
        assert user.role == 'doctor'

    def test_IT04_duplicate_email_registration_fails(self):
        """IT-04: Registering with an existing email re-renders form with error."""
        User.objects.create(
            name="Existing",
            email="dup@example.com",
            password=make_password("pass"),
            role="patient",
        )
        client = Client()
        response = client.post(reverse('register'), {
            'name': 'Another',
            'email': 'dup@example.com',
            'password': 'ValidPass@123',
            'confirm_password': 'ValidPass@123',
            'role': 'patient',
        })
        assert response.status_code == 200
        assert b'already exists' in response.content

    def test_IT05_mismatched_passwords_registration_fails(self):
        """IT-05: Mismatched passwords re-renders form with error."""
        client = Client()
        response = client.post(reverse('register'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'ValidPass@123',
            'confirm_password': 'DifferentPass@999',
            'role': 'patient',
        })
        assert response.status_code == 200
        assert b'do not match' in response.content

    def test_IT06_short_password_registration_fails(self):
        """IT-06: Password shorter than 8 chars re-renders form with error."""
        client = Client()
        response = client.post(reverse('register'), {
            'name': 'Test',
            'email': 'short@example.com',
            'password': 'short',
            'confirm_password': 'short',
            'role': 'patient',
        })
        assert response.status_code == 200
        assert not User.objects.filter(email='short@example.com').exists()

    def test_IT07_empty_form_registration_fails(self):
        """IT-07: Empty form submission returns 200 with errors."""
        client = Client()
        response = client.post(reverse('register'), {})
        assert response.status_code == 200

    def test_IT08_registration_does_not_login_user(self):
        """IT-08: After registration session has no user_id (not auto-logged in)."""
        client = Client()
        client.post(reverse('register'), {
            'name': 'No Auto Login',
            'email': 'noautologin@example.com',
            'password': 'ValidPass@123',
            'confirm_password': 'ValidPass@123',
            'role': 'patient',
        })
        assert 'user_id' not in client.session

# IT-09 to IT-16: Login
@pytest.mark.django_db
class TestLogin:

    def setup_method(self):
        self.email    = 'logintest@example.com'
        self.password = 'ValidPass@123'
        User.objects.filter(email=self.email).delete()
        self.user = User.objects.create(
            name="Login Test",
            email=self.email,
            password=make_password(self.password),
            role='patient',
        )

    def test_IT09_login_page_loads(self):
        """IT-09: GET /login/ returns 200."""
        client = Client()
        response = client.get(reverse('login'))
        assert response.status_code == 200

    def test_IT10_successful_patient_login(self):
        """IT-10: Valid credentials log in patient and redirect to patient dashboard."""
        client = Client()
        response = client.post(reverse('login'), {
            'email': self.email,
            'password': self.password,
        }, follow=True)
        assert response.status_code == 200
        assert client.session.get('user_id') == self.user.user_id
        assert client.session.get('role') == 'patient'

    def test_IT11_wrong_password_login_fails(self):
        """IT-11: Wrong password stays on login page with error."""
        client = Client()
        response = client.post(reverse('login'), {
            'email': self.email,
            'password': 'WrongPass@999',
        })
        assert response.status_code == 200
        assert b'Incorrect' in response.content
        assert 'user_id' not in client.session

    def test_IT12_nonexistent_email_login_fails(self):
        """IT-12: Non-existent email stays on login page with error."""
        client = Client()
        response = client.post(reverse('login'), {
            'email': 'nobody@nowhere.com',
            'password': 'anypass',
        })
        assert response.status_code == 200
        assert b'No account' in response.content
        assert 'user_id' not in client.session

    def test_IT13_session_set_after_login(self):
        """IT-13: Session contains user_id, role, user_name after login."""
        client = Client()
        client.post(reverse('login'), {
            'email': self.email,
            'password': self.password,
        })
        assert client.session['user_id'] == self.user.user_id
        assert client.session['role'] == 'patient'
        assert client.session['user_name'] == self.user.name

    def test_IT14_doctor_login_redirects_to_doctor_dashboard(self):
        """IT-14: Doctor login redirects to /doctor/."""
        doctor = User.objects.create(
            name="Test Doctor",
            email="doc@example.com",
            password=make_password(self.password),
            role='doctor',
        )
        client = Client()
        response = client.post(reverse('login'), {
            'email': 'doc@example.com',
            'password': self.password,
        }, follow=True)
        assert '/doctor/' in response.redirect_chain[-1][0]

    def test_IT15_already_logged_in_redirects_to_index(self):
        """IT-15: Accessing /login/ while already logged in redirects away."""
        client = Client()
        session = client.session
        session['user_id'] = self.user.user_id
        session['role'] = 'patient'
        session.save()
        response = client.get(reverse('login'))
        assert response.status_code == 302

    def test_IT16_empty_login_form_fails(self):
        """IT-16: Empty POST to login returns 200 with validation errors."""
        client = Client()
        response = client.post(reverse('login'), {})
        assert response.status_code == 200
        assert 'user_id' not in client.session

# IT-17 to IT-19: Logout
@pytest.mark.django_db
class TestLogout:

    def test_IT17_logout_clears_session(self):
        """IT-17: Logout flushes the session."""
        user = User.objects.create(
            name="Logout User",
            email="logout@example.com",
            password=make_password("pass"),
            role='patient',
        )
        client = Client()
        session = client.session
        session['user_id']   = user.user_id
        session['role']      = 'patient'
        session['user_name'] = user.name
        session.save()
        client.get(reverse('logout'))
        assert 'user_id' not in client.session

    def test_IT18_logout_redirects_to_landing(self):
        """IT-18: Logout redirects to landing page."""
        client = Client()
        response = client.get(reverse('logout'))
        assert response.status_code == 302
        assert '/' in response['Location']

    def test_IT19_dashboard_inaccessible_after_logout(self):
        """IT-19: Accessing /patient/ after logout redirects to login."""
        user = User.objects.create(
            name="Post Logout",
            email="postlogout@example.com",
            password=make_password("pass"),
            role='patient',
        )
        client = Client()
        session = client.session
        session['user_id'] = user.user_id
        session['role']    = 'patient'
        session.save()
        client.get(reverse('logout'))
        response = client.get(reverse('patient_dashboard'))
        assert response.status_code == 302
        assert '/login/' in response['Location']
