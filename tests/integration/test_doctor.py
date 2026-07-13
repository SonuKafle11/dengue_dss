import hashlib
import pytest
from django.urls import reverse
from django.test import Client
from core.models import User, PatientRecord


def make_password(raw):
    return hashlib.sha256(raw.encode()).hexdigest()

# IT-39 to IT-44: Doctor Dashboard
@pytest.mark.django_db
class TestDoctorDashboard:

    def test_IT39_dashboard_loads_for_doctor(self, doctor_client):
        """IT-39: Doctor dashboard returns 200 for logged-in doctor."""
        response = doctor_client.get(reverse('doctor_dashboard'))
        assert response.status_code == 200

    def test_IT40_dashboard_blocked_for_anonymous(self):
        """IT-40: Anonymous GET /doctor/ redirects to login."""
        client = Client()
        response = client.get(reverse('doctor_dashboard'))
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_IT41_dashboard_blocked_for_patient(self, patient_client):
        """IT-41: Patient cannot access doctor dashboard."""
        response = patient_client.get(reverse('doctor_dashboard'))
        assert response.status_code == 302

    def test_IT42_dashboard_context_has_records(self, doctor_client, patient_record):
        """IT-42: Doctor dashboard context contains patient records."""
        response = doctor_client.get(reverse('doctor_dashboard'))
        assert 'records' in response.context

    def test_IT43_dashboard_search_filters_by_name(self, doctor_client, patient_record):
        """IT-43: Search by patient name returns filtered results."""
        response = doctor_client.get(
            reverse('doctor_dashboard') + '?search=Test+Patient'
        )
        assert response.status_code == 200

    def test_IT44_dashboard_status_filter_reviewed(self, doctor_client, patient_record):
        """IT-44: Status filter 'reviewed' returns only reviewed records."""
        response = doctor_client.get(
            reverse('doctor_dashboard') + '?status=reviewed'
        )
        assert response.status_code == 200
        for rec in response.context['records']:
            assert rec.is_reviewed is True

# IT-45 to IT-50: Doctor Patient Detail
@pytest.mark.django_db
class TestDoctorPatientDetail:

    def test_IT45_detail_page_loads(self, doctor_client, patient_record):
        """IT-45: GET /doctor/patient/<uuid>/ returns 200 for doctor."""
        response = doctor_client.get(
            reverse('doctor_patient_detail',
                    kwargs={'record_id': patient_record.record_id})
        )
        assert response.status_code == 200

    def test_IT46_detail_blocked_for_anonymous(self, patient_record):
        """IT-46: Anonymous access to detail page redirects to login."""
        client = Client()
        response = client.get(
            reverse('doctor_patient_detail',
                    kwargs={'record_id': patient_record.record_id})
        )
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_IT47_detail_blocked_for_patient(self, patient_client, patient_record):
        """IT-47: Patient cannot access doctor patient detail."""
        response = patient_client.get(
            reverse('doctor_patient_detail',
                    kwargs={'record_id': patient_record.record_id})
        )
        assert response.status_code == 302

    def test_IT48_valid_lab_submission_marks_reviewed(
            self, doctor_client, patient_record):
        """IT-48: Valid lab POST marks record as reviewed."""
        doctor_client.post(
            reverse('doctor_patient_detail',
                    kwargs={'record_id': patient_record.record_id}),
            {
                'ns1_status':    'negative',
                'igg_status':    'negative',
                'igm_status':    'negative',
                'platelet_count': 120000,
                'wbc_count':      5000,
            }
        )
        patient_record.refresh_from_db()
        assert patient_record.is_reviewed is True

    def test_IT49_valid_lab_submission_sets_prediction(
            self, doctor_client, patient_record):
        """IT-49: Valid lab POST sets ml_prediction on record."""
        doctor_client.post(
            reverse('doctor_patient_detail',
                    kwargs={'record_id': patient_record.record_id}),
            {
                'ns1_status':    'positive',
                'igg_status':    'negative',
                'igm_status':    'negative',
                'platelet_count': 80000,
                'wbc_count':      3000,
            }
        )
        patient_record.refresh_from_db()
        assert patient_record.ml_prediction != ''

    def test_IT50_detail_context_has_record(self, doctor_client, patient_record):
        """IT-50: Detail page context contains the correct record."""
        response = doctor_client.get(
            reverse('doctor_patient_detail',
                    kwargs={'record_id': patient_record.record_id})
        )
        assert response.context['record'].record_id == patient_record.record_id

# IT-51 to IT-54: Doctor Prediction Result
@pytest.mark.django_db
class TestDoctorPredictionResult:

    @pytest.fixture
    def reviewed_record(self, doctor_client, patient_record):
        """Submit lab values to create a reviewed record."""
        doctor_client.post(
            reverse('doctor_patient_detail',
                    kwargs={'record_id': patient_record.record_id}),
            {
                'ns1_status':    'negative',
                'igg_status':    'positive',
                'igm_status':    'negative',
                'platelet_count': 100000,
                'wbc_count':      4500,
            }
        )
        patient_record.refresh_from_db()
        return patient_record

    def test_IT51_prediction_result_loads(self, doctor_client, reviewed_record):
        """IT-51: GET /doctor/result/<uuid>/ returns 200."""
        response = doctor_client.get(
            reverse('doctor_prediction_result',
                    kwargs={'record_id': reviewed_record.record_id})
        )
        assert response.status_code == 200

    def test_IT52_prediction_result_blocked_for_anonymous(self, reviewed_record):
        """IT-52: Anonymous access to prediction result redirects to login."""
        client = Client()
        response = client.get(
            reverse('doctor_prediction_result',
                    kwargs={'record_id': reviewed_record.record_id})
        )
        assert response.status_code == 302

    def test_IT53_prediction_result_context_has_record(
            self, doctor_client, reviewed_record):
        """IT-53: Prediction result context contains the record."""
        response = doctor_client.get(
            reverse('doctor_prediction_result',
                    kwargs={'record_id': reviewed_record.record_id})
        )
        assert response.context['record'].record_id == reviewed_record.record_id

    def test_IT54_ns1_positive_forces_positive_prediction(
            self, doctor_client, patient_record):
        """IT-54: NS1=positive forces ml_prediction to Positive Dengue."""
        doctor_client.post(
            reverse('doctor_patient_detail',
                    kwargs={'record_id': patient_record.record_id}),
            {
                'ns1_status':    'positive',
                'igg_status':    'negative',
                'igm_status':    'negative',
                'platelet_count': 80000,
                'wbc_count':      3000,
            }
        )
        patient_record.refresh_from_db()
        assert 'Positive' in patient_record.ml_prediction
        assert patient_record.ml_confidence >= 95.0
