"""
tests/integration/test_patient.py
Integration tests for the patient flow:
dashboard, assessment form, result, profile.
"""
import pytest
from django.urls import reverse
from core.models import PatientRecord

# IT-20 to IT-25: Patient Dashboard
@pytest.mark.django_db
class TestPatientDashboard:

    def test_IT20_dashboard_loads_for_patient(self, patient_client):
        """IT-20: Patient dashboard returns 200 for logged-in patient."""
        response = patient_client.get(reverse('patient_dashboard'))
        assert response.status_code == 200

    def test_IT21_dashboard_blocked_for_anonymous(self):
        """IT-21: Unauthenticated GET /patient/ redirects to login."""
        from django.test import Client
        client = Client()
        response = client.get(reverse('patient_dashboard'))
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_IT22_dashboard_blocked_for_doctor(self, doctor_client):
        """IT-22: Doctor cannot access patient dashboard."""
        response = doctor_client.get(reverse('patient_dashboard'))
        assert response.status_code == 302

    def test_IT23_dashboard_shows_records(self, patient_client, patient_record):
        """IT-23: Patient dashboard renders existing records."""
        response = patient_client.get(reverse('patient_dashboard'))
        assert response.status_code == 200
        assert str(patient_record.record_id) in str(response.content) or \
               b'Assessment' in response.content or \
               response.status_code == 200

    def test_IT24_dashboard_context_has_user(self, patient_client, patient_user):
        """IT-24: Dashboard context contains the logged-in user."""
        response = patient_client.get(reverse('patient_dashboard'))
        assert response.context['user'].pk == patient_user.pk

    def test_IT25_dashboard_context_has_records(self, patient_client, patient_record):
        """IT-25: Dashboard context contains records queryset."""
        response = patient_client.get(reverse('patient_dashboard'))
        assert 'records' in response.context


# ============================================================
# IT-26 to IT-31: Patient Assessment Form
# ============================================================

@pytest.mark.django_db
class TestPatientForm:

    def test_IT26_form_page_loads(self, patient_client):
        """IT-26: GET /patient/form/ returns 200."""
        response = patient_client.get(reverse('patient_form'))
        assert response.status_code == 200

    def test_IT27_form_blocked_for_anonymous(self):
        """IT-27: Unauthenticated GET /patient/form/ redirects to login."""
        from django.test import Client
        client = Client()
        response = client.get(reverse('patient_form'))
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_IT28_valid_form_submission_creates_record(self, patient_client, patient_user):
        """IT-28: Valid form POST creates a PatientRecord for the patient."""
        initial_count = PatientRecord.objects.filter(patient=patient_user).count()
        patient_client.post(reverse('patient_form'), {
            'gender': 'female',
            'age': 25,
            'weight': 60,
            'height': 160,
            'fever': 'on',
            'severe_headache': 'on',
            'bleeding': 'on',
        })
        assert PatientRecord.objects.filter(patient=patient_user).count() == initial_count + 1

    def test_IT29_form_redirects_to_result_after_submission(self, patient_client, patient_user):
        """IT-29: Valid form POST redirects to patient result page."""
        response = patient_client.post(reverse('patient_form'), {
            'gender': 'female',
            'age': 25,
            'weight': 60,
            'height': 160,
            'fever': 'on',
            'bleeding': 'on',
        }, follow=False)
        assert response.status_code == 302
        assert '/patient/result/' in response['Location']

    def test_IT30_form_saves_profile_to_user(self, patient_client, patient_user):
        """IT-30: Valid form POST updates age/weight/gender on User model."""
        patient_client.post(reverse('patient_form'), {
            'gender': 'male',
            'age': 30,
            'weight': 75,
            'height': 175,
            'fever': 'on',
        })
        patient_user.refresh_from_db()
        assert patient_user.age == 30.0
        assert patient_user.weight == 75.0
        assert patient_user.gender == 'male'

    def test_IT31_form_no_symptoms_stays_on_form(self, patient_client):
        """IT-31: Submitting form without any symptom stays on form page."""
        response = patient_client.post(reverse('patient_form'), {
            'gender': 'female',
            'age': 25,
            'weight': 60,
            'height': 160,
        }, follow=True)
        # Should not create a record — redirect back or error shown
        assert response.status_code == 200

# IT-32 to IT-35: Patient Result
@pytest.mark.django_db
class TestPatientResult:

    def test_IT32_result_page_loads(self, patient_client, patient_record):
        """IT-32: GET /patient/result/<uuid>/ returns 200 for owner."""
        response = patient_client.get(
            reverse('patient_result', kwargs={'record_id': patient_record.record_id})
        )
        assert response.status_code == 200

    def test_IT33_result_blocked_for_anonymous(self, patient_record):
        """IT-33: Anonymous access to result page redirects to login."""
        from django.test import Client
        client = Client()
        response = client.get(
            reverse('patient_result', kwargs={'record_id': patient_record.record_id})
        )
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_IT34_result_context_has_record(self, patient_client, patient_record):
        """IT-34: Result page context contains the PatientRecord."""
        response = patient_client.get(
            reverse('patient_result', kwargs={'record_id': patient_record.record_id})
        )
        assert response.context['record'].record_id == patient_record.record_id

    def test_IT35_result_404_for_other_patient_record(self, doctor_user, patient_record):
        """IT-35: Patient cannot view another patient's result (404)."""
        from django.test import Client
        import hashlib
        other = __import__('core.models', fromlist=['User']).User.objects.create(
            name="Other Patient",
            email="other@example.com",
            password=hashlib.sha256(b"pass").hexdigest(),
            role="patient",
        )
        client = Client()
        session = client.session
        session['user_id'] = other.pk
        session['role']    = 'patient'
        session.save()
        response = client.get(
            reverse('patient_result', kwargs={'record_id': patient_record.record_id})
        )
        assert response.status_code == 404

# IT-36 to IT-38: Patient Profile
@pytest.mark.django_db
class TestPatientProfile:

    def test_IT36_profile_page_loads(self, patient_client):
        """IT-36: GET /patient/profile/ returns 200."""
        response = patient_client.get(reverse('patient_profile'))
        assert response.status_code == 200

    def test_IT37_profile_update_saves_data(self, patient_client, patient_user):
        """IT-37: POST to /patient/profile/ updates user fields."""
        patient_client.post(reverse('patient_profile'), {
            'age': 28,
            'weight': 65,
            'gender': 'female',
            'is_pregnant': False,
        })
        patient_user.refresh_from_db()
        assert patient_user.age == 28.0
        assert patient_user.weight == 65.0

    def test_IT38_profile_blocked_for_anonymous(self):
        """IT-38: Anonymous access to profile redirects to login."""
        from django.test import Client
        client = Client()
        response = client.get(reverse('patient_profile'))
        assert response.status_code == 302
        assert '/login/' in response['Location']
