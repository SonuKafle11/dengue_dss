"""
tests/unit/test_models.py
Unit tests for core models: User, AdminUser, PatientRecord.
"""
import hashlib
import pytest
from core.models import User, AdminUser, PatientRecord, generate_user_id


# ============================================================
# Helpers
# ============================================================

def make_password(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


# ============================================================
# UT-01 to UT-06: User model
# ============================================================

@pytest.mark.django_db
class TestUserModel:

    def test_UT01_patient_user_created(self):
        """UT-01: Patient user is created with correct fields."""
        user = User.objects.create(
            name="Sita Thapa",
            email="sita@example.com",
            password=make_password("pass1234"),
            role="patient",
        )
        assert user.name == "Sita Thapa"
        assert user.role == "patient"
        assert user.email == "sita@example.com"
        assert user.is_pregnant is False
        assert user.email_verified is False

    def test_UT02_doctor_user_created(self):
        """UT-02: Doctor user is created with correct role."""
        user = User.objects.create(
            name="Dr. Ram Shrestha",
            email="ram@example.com",
            password=make_password("pass1234"),
            role="doctor",
        )
        assert user.role == "doctor"

    def test_UT03_user_id_auto_generated(self):
        """UT-03: user_id is auto-generated, 8 characters, alphanumeric."""
        user = User.objects.create(
            name="Auto ID User",
            email="autoid@example.com",
            password=make_password("pass1234"),
            role="patient",
        )
        assert user.user_id is not None
        assert len(user.user_id) == 8
        assert user.user_id.isalnum()

    def test_UT04_user_id_unique(self):
        """UT-04: Two users get different user_ids."""
        u1 = User.objects.create(name="A", email="a@example.com",
                                  password=make_password("p"), role="patient")
        u2 = User.objects.create(name="B", email="b@example.com",
                                  password=make_password("p"), role="patient")
        assert u1.user_id != u2.user_id

    def test_UT05_email_unique_constraint(self):
        """UT-05: Duplicate email raises IntegrityError."""
        from django.db import IntegrityError
        User.objects.create(name="X", email="dup@example.com",
                             password=make_password("p"), role="patient")
        with pytest.raises(IntegrityError):
            User.objects.create(name="Y", email="dup@example.com",
                                 password=make_password("p"), role="patient")

    def test_UT06_user_str(self):
        """UT-06: __str__ returns name, role, and user_id."""
        user = User.objects.create(
            name="Ram",
            email="ram2@example.com",
            password=make_password("pass1234"),
            role="patient",
        )
        assert "Ram" in str(user)
        assert "patient" in str(user)


# ============================================================
# UT-07 to UT-08: AdminUser model
# ============================================================

@pytest.mark.django_db
class TestAdminUserModel:

    def test_UT07_admin_user_created(self):
        """UT-07: AdminUser is created with correct username."""
        admin = AdminUser.objects.create(
            username="admin_test",
            password=make_password("adminpass"),
        )
        assert admin.username == "admin_test"
        assert admin.password == make_password("adminpass")

    def test_UT08_admin_username_unique(self):
        """UT-08: Duplicate admin username raises IntegrityError."""
        from django.db import IntegrityError
        AdminUser.objects.create(username="dupAdmin",
                                  password=make_password("p"))
        with pytest.raises(IntegrityError):
            AdminUser.objects.create(username="dupAdmin",
                                      password=make_password("p"))


# ============================================================
# UT-09 to UT-18: PatientRecord model
# ============================================================

@pytest.mark.django_db
class TestPatientRecordModel:

    def _make_user(self, email="rec@example.com"):
        return User.objects.create(
            name="Record User",
            email=email,
            password=make_password("pass1234"),
            role="patient",
            age=30,
            weight=60,
            gender="female",
        )

    def test_UT09_record_created_with_symptoms(self):
        """UT-09: PatientRecord is created and linked to patient."""
        user = self._make_user()
        rec = PatientRecord(
            patient=user, age=30, weight=60, gender="female",
            fever=True, severe_headache=True,
        )
        rec.save()
        assert rec.patient == user
        assert rec.fever is True
        assert rec.severe_headache is True

    def test_UT10_clinical_score_calculated_on_save(self):
        """UT-10: clinical_score is auto-calculated on save."""
        user = self._make_user("score@example.com")
        rec = PatientRecord(
            patient=user, age=30, weight=60, gender="female",
            fever=True,           # +1
            severe_headache=True, # +2
            bleeding=True,        # +3
        )
        rec.save()
        assert rec.clinical_score == 6

    def test_UT11_low_risk_level(self):
        """UT-11: Score < 4 gives low risk level."""
        user = self._make_user("low@example.com")
        rec = PatientRecord(
            patient=user, age=30, weight=60, gender="female",
            fever=True,  # +1
        )
        rec.save()
        assert rec.clinical_risk_level == "low"

    def test_UT12_high_risk_level(self):
        """UT-12: Score >= 4 gives high risk level."""
        user = self._make_user("high@example.com")
        rec = PatientRecord(
            patient=user, age=30, weight=60, gender="female",
            bleeding=True,          # +3
            extreme_weakness=True,  # +3
        )
        rec.save()
        assert rec.clinical_risk_level == "high"

    def test_UT13_age_bonus_over_70(self):
        """UT-13: Age > 70 adds +1 to clinical score."""
        user = self._make_user("elder@example.com")
        rec = PatientRecord(
            patient=user, age=75, weight=60, gender="male",
            fever=True,  # +1
        )
        rec.save()
        assert rec.clinical_score == 2  # 1 (fever) + 1 (age bonus)

    def test_UT14_pregnancy_bonus(self):
        """UT-14: is_pregnant adds +1 to clinical score."""
        user = self._make_user("preg@example.com")
        rec = PatientRecord(
            patient=user, age=25, weight=55, gender="female",
            is_pregnant=True,
            fever=True,  # +1
        )
        rec.save()
        assert rec.clinical_score == 2  # 1 (fever) + 1 (pregnant)

    def test_UT15_record_uuid_unique(self):
        """UT-15: Two records get different UUIDs."""
        user = self._make_user("uuid@example.com")
        rec1 = PatientRecord(patient=user, age=25, weight=60, gender="male")
        rec1.save()
        rec2 = PatientRecord(patient=user, age=25, weight=60, gender="male")
        rec2.save()
        assert rec1.record_id != rec2.record_id

    def test_UT16_record_str(self):
        """UT-16: __str__ contains record_id and patient name."""
        user = self._make_user("str@example.com")
        rec = PatientRecord(patient=user, age=25, weight=60, gender="male")
        rec.save()
        assert str(rec.record_id) in str(rec)
        assert "Record User" in str(rec)

    def test_UT17_no_symptoms_score_zero(self):
        """UT-17: No symptoms selected gives score of 0."""
        user = self._make_user("zero@example.com")
        rec = PatientRecord(patient=user, age=25, weight=60, gender="male")
        rec.save()
        assert rec.clinical_score == 0
        assert rec.clinical_risk_level == "low"

    def test_UT18_all_severe_symptoms_high_risk(self):
        """UT-18: All severe symptoms selected gives high risk."""
        user = self._make_user("allsym@example.com")
        rec = PatientRecord(
            patient=user, age=25, weight=60, gender="female",
            bleeding=True, extreme_weakness=True,
            urine_output_low=True, restless_drowsy=True,
            drop_in_fever_with_weakness=True,
        )
        rec.save()
        assert rec.clinical_risk_level == "high"
        assert rec.clinical_score >= 10


# ============================================================
# UT-19: generate_user_id helper
# ============================================================

def test_UT19_generate_user_id_format():
    """UT-19: generate_user_id returns 8-char alphanumeric string."""
    uid = generate_user_id()
    assert len(uid) == 8
    assert uid.isalnum()
    assert uid == uid.upper()
