"""
tests/integration/test_admin.py
Integration tests for admin flow:
login, dashboard, delete user, delete record.
"""
import hashlib
import pytest
from django.urls import reverse
from django.test import Client
from core.models import User, AdminUser, PatientRecord


def make_password(raw):
    return hashlib.sha256(raw.encode()).hexdigest()

# IT-55 to IT-60: Admin Login
@pytest.mark.django_db
class TestAdminLogin:

    def test_IT55_admin_login_page_loads(self):
        """IT-55: GET /admin-login/ returns 200."""
        client = Client()
        response = client.get(reverse('admin_login'))
        assert response.status_code == 200

    def test_IT56_successful_admin_login(self, admin_user):
        """IT-56: Valid admin credentials set session and redirect."""
        client = Client()
        response = client.post(reverse('admin_login'), {
            'username': admin_user.username,
            'password': 'AdminPass@123',
        }, follow=True)
        assert response.status_code == 200
        assert client.session.get('admin_logged_in') is True
        assert client.session.get('admin_username') == admin_user.username

    def test_IT57_wrong_password_admin_login_fails(self, admin_user):
        """IT-57: Wrong admin password stays on login page."""
        client = Client()
        response = client.post(reverse('admin_login'), {
            'username': admin_user.username,
            'password': 'WrongPass@999',
        })
        assert response.status_code == 200
        assert 'admin_logged_in' not in client.session

    def test_IT58_nonexistent_admin_login_fails(self):
        """IT-58: Non-existent admin username shows error."""
        client = Client()
        response = client.post(reverse('admin_login'), {
            'username': 'nobody',
            'password': 'anypass',
        })
        assert response.status_code == 200
        assert b'not found' in response.content
        assert 'admin_logged_in' not in client.session

    def test_IT59_admin_logout_clears_session(self, admin_client):
        """IT-59: Admin logout clears admin session."""
        admin_client.get(reverse('admin_logout'))
        assert 'admin_logged_in' not in admin_client.session

    def test_IT60_admin_logout_redirects_to_admin_login(self, admin_client):
        """IT-60: Admin logout redirects to /admin-login/."""
        response = admin_client.get(reverse('admin_logout'))
        assert response.status_code == 302
        assert '/admin-login/' in response['Location']


# ============================================================
# IT-61 to IT-65: Admin Dashboard
# ============================================================

@pytest.mark.django_db
class TestAdminDashboard:

    def test_IT61_dashboard_loads_for_admin(self, admin_client):
        """IT-61: Admin dashboard returns 200 for logged-in admin."""
        response = admin_client.get(reverse('admin_dashboard'))
        assert response.status_code == 200

    def test_IT62_dashboard_blocked_for_anonymous(self):
        """IT-62: Anonymous GET /admin-panel/ redirects to admin login."""
        client = Client()
        response = client.get(reverse('admin_dashboard'))
        assert response.status_code == 302
        assert '/admin-login/' in response['Location']

    def test_IT63_dashboard_blocked_for_patient(self, patient_client):
        """IT-63: Patient cannot access admin dashboard."""
        response = patient_client.get(reverse('admin_dashboard'))
        assert response.status_code == 302

    def test_IT64_dashboard_context_has_users(self, admin_client, patient_user):
        """IT-64: Dashboard context contains users queryset."""
        response = admin_client.get(reverse('admin_dashboard'))
        assert 'users' in response.context
        user_ids = [u.user_id for u in response.context['users']]
        assert patient_user.user_id in user_ids

    def test_IT65_dashboard_context_has_records(self, admin_client, patient_record):
        """IT-65: Dashboard context contains records queryset."""
        response = admin_client.get(reverse('admin_dashboard'))
        assert 'records' in response.context


# ============================================================
# IT-66 to IT-70: Admin Delete User / Record
# ============================================================

@pytest.mark.django_db
class TestAdminDelete:

    def test_IT66_delete_user_removes_from_db(self, admin_client):
        """IT-66: POST to delete-user removes user from DB."""
        user = User.objects.create(
            name="To Delete",
            email="todelete@example.com",
            password=make_password("pass"),
            role="patient",
        )
        response = admin_client.post(
            reverse('admin_delete_user', kwargs={'user_id': user.user_id})
        )
        assert response.status_code == 200
        import json
        data = json.loads(response.content)
        assert data['ok'] is True
        assert not User.objects.filter(user_id=user.user_id).exists()

    def test_IT67_delete_user_returns_json(self, admin_client, patient_user):
        """IT-67: Delete user endpoint returns JSON response."""
        response = admin_client.post(
            reverse('admin_delete_user', kwargs={'user_id': patient_user.user_id})
        )
        assert response['Content-Type'] == 'application/json'

    def test_IT68_delete_nonexistent_user_returns_404(self, admin_client):
        """IT-68: Deleting non-existent user returns JSON with ok=False."""
        response = admin_client.post(
            reverse('admin_delete_user', kwargs={'user_id': 'XXXXXXXX'})
        )
        import json
        data = json.loads(response.content)
        assert data['ok'] is False

    def test_IT69_delete_record_removes_from_db(self, admin_client, patient_record):
        """IT-69: POST to delete-record removes record from DB."""
        record_id = patient_record.record_id
        response = admin_client.post(
            reverse('admin_delete_record', kwargs={'record_id': record_id})
        )
        import json
        data = json.loads(response.content)
        assert data['ok'] is True
        assert not PatientRecord.objects.filter(record_id=record_id).exists()

    def test_IT70_delete_blocked_for_anonymous(self, patient_user):
        """IT-70: Anonymous delete request redirects to admin login."""
        client = Client()
        response = client.post(
            reverse('admin_delete_user', kwargs={'user_id': patient_user.user_id})
        )
        assert response.status_code == 302
        assert '/admin-login/' in response['Location']
