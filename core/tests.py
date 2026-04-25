from django.test import TestCase, Client
from django.urls import reverse
from .models import User, AdminUser, PatientRecord
import hashlib

def hash_password(raw):
    return hashlib.sha256(raw.encode()).hexdigest()

class UserModelTest(TestCase):
    """Test Case 1: User model creation and ID generation"""

    def test_patient_creation(self):
        """TC-01: Patient user created with unique 8-char ID"""
        user = User.objects.create(
            name='Sumitra Kafle',
            password=hash_password('test123'),
            role='patient'
        )
        self.assertEqual(user.role, 'patient')
        self.assertEqual(len(user.user_id), 8)

    def test_doctor_creation(self):
        """TC-02: Doctor user created successfully"""
        user = User.objects.create(
            name='Dr. Gyanendra Lekhak',
            password=hash_password('doc123'),
            role='doctor'
        )
        self.assertEqual(user.role, 'doctor')

    def test_password_is_hashed(self):
        """TC-03: Password stored as SHA-256 hash not plain text"""
        user = User.objects.create(
            name='Test User',
            password=hash_password('mypassword'),
            role='patient'
        )
        self.assertNotEqual(user.password, 'mypassword')
        self.assertEqual(len(user.password), 64)


class ClinicalScoringTest(TestCase):
    """Test Case 2: Clinical scoring system"""

    def setUp(self):
        self.patient = User.objects.create(
            name='Score Test Patient',
            password=hash_password('test'),
            role='patient'
        )

    def test_low_risk_score(self):
        """TC-04: Score 0-3 gives Low Risk"""
        rec = PatientRecord.objects.create(
            patient=self.patient, age=25, weight=60,
            fever=True  # 2 points
        )
        self.assertEqual(rec.clinical_score, 2)
        self.assertEqual(rec.clinical_risk_level, 'low')

    def test_possible_dengue_score(self):
        """TC-05: Score 4-6 gives Possible Dengue"""
        rec = PatientRecord.objects.create(
            patient=self.patient, age=25, weight=60,
            fever=True,            # 2
            extreme_weakness=True  # 2
        )
        self.assertEqual(rec.clinical_score, 4)
        self.assertEqual(rec.clinical_risk_level, 'possible')

    def test_high_risk_score(self):
        """TC-06: Score >= 10 gives High Risk"""
        rec = PatientRecord.objects.create(
            patient=self.patient, age=25, weight=60,
            fever=True,                        # 2
            bleeding=True,                     # 3
            drop_in_fever_with_weakness=True,  # 3
            extreme_weakness=True,             # 2
            cold_hands_feet=True,              # 2
        )
        self.assertGreaterEqual(rec.clinical_score, 10)
        self.assertEqual(rec.clinical_risk_level, 'high')

    def test_score_auto_calculated_on_save(self):
        """TC-07: clinical_score auto-calculated when saving"""
        rec = PatientRecord(
            patient=self.patient, age=30, weight=55,
            fever=True, severe_headache=True  # 2 + 1 = 3
        )
        rec.save()
        self.assertEqual(rec.clinical_score, 3)


class RegistrationTest(TestCase):
    """Test Case 3: User registration flow"""

    def setUp(self):
        self.client = Client()

    def test_registration_page_loads(self):
        """TC-08: Registration page returns 200"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_successful_patient_registration(self):
        """TC-09: Patient can register and gets unique ID"""
        response = self.client.post(reverse('register'), {
            'name': 'Bikash Thapa',
            'password': 'password123',
            'role': 'patient'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('registered_id', response.context)
        self.assertTrue(
            User.objects.filter(name='Bikash Thapa', role='patient').exists()
        )

    def test_duplicate_registration_blocked(self):
        """TC-10: Same name + role cannot register twice"""
        User.objects.create(
            name='Duplicate User',
            password=hash_password('pass'),
            role='patient'
        )
        response = self.client.post(reverse('register'), {
            'name': 'Duplicate User',
            'password': 'newpass',
            'role': 'patient'
        })
        self.assertNotIn('registered_id', response.context)

class LoginTest(TestCase):
    """Test Case 4: Login and session"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            name='Login Test Patient',
            password=hash_password('mypass'),
            role='patient'
        )

    def test_login_with_user_id(self):
        """TC-11: User can login using their unique ID"""
        response = self.client.post(reverse('login'), {
            'identifier': self.user.user_id,
            'password': 'mypass'
        })
        self.assertRedirects(response, reverse('patient_dashboard'))

    def test_login_with_name(self):
        """TC-12: User can login using their full name"""
        response = self.client.post(reverse('login'), {
            'identifier': 'Login Test Patient',
            'password': 'mypass'
        })
        self.assertRedirects(response, reverse('patient_dashboard'))

    def test_wrong_password_rejected(self):
        """TC-13: Wrong password does not log in"""
        response = self.client.post(reverse('login'), {
            'identifier': self.user.user_id,
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('user_id', self.client.session)

    def test_patient_cannot_access_doctor_pages(self):
        """TC-14: Patient session cannot access /doctor/"""
        self.client.post(reverse('login'), {
            'identifier': self.user.user_id,
            'password': 'mypass'
        })
        response = self.client.get(reverse('doctor_dashboard'))
        self.assertRedirects(response, reverse('login'))