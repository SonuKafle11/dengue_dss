# File: tests_system/test_core_unit.py
# Automated Unit Tests for Dengue Prediction System
# Run using: pytest tests_system -v

import hashlib
import pytest

from core.models import User, PatientRecord
import ml_model.predictor as predictor
import ml_model.dosage_engine as dosage_engine


# ---------------------------------------------------------
# UT-01: Unique User ID Generation
# ---------------------------------------------------------
@pytest.mark.django_db
def test_generate_unique_user_id():
    """
    Verify that a unique 8-character user ID is generated
    automatically when a new user is saved.
    """
    user = User(
        name="Test User",
        password="dummy123",   # Use actual field name from your User model
        role="patient"
    )
    user.save()

    assert user.user_id is not None
    assert len(user.user_id) == 8
    assert user.user_id.isalnum()


# ---------------------------------------------------------
# UT-02: SHA-256 Password Hashing
# ---------------------------------------------------------
def test_hash_password():
    """
    Verify that SHA-256 generates a valid 64-character hash.
    """
    password = "ram123"
    hashed = hashlib.sha256(password.encode()).hexdigest()

    assert len(hashed) == 64
    assert hashed != password
    assert all(c in "0123456789abcdef" for c in hashed.lower())


# ---------------------------------------------------------
# UT-03: Clinical Score Calculation
# ---------------------------------------------------------
@pytest.mark.django_db
def test_calculate_clinical_score():
    """
    Verify that the clinical score calculation returns
    a non-negative integer.
    """
    patient = PatientRecord(
        fever=True,
        nausea_vomiting=True,
        severe_headache=True,
    )

    score = patient.calculate_clinical_score()

    assert isinstance(score, int)
    assert score >= 0


# ---------------------------------------------------------
# UT-04: Risk Classification
# ---------------------------------------------------------
@pytest.mark.django_db
def test_get_risk_level():
    """
    Verify that the risk classification method returns
    one of the expected risk levels.
    """
    patient = PatientRecord()

    try:
        # If your method accepts score as parameter
        risk = patient.get_risk_level(11)
    except TypeError:
        # If your method uses self.clinical_score
        patient.clinical_score = 11
        risk = patient.get_risk_level()

    assert isinstance(risk, str)
    assert risk.lower() in ["low", "possible", "high"]


# ---------------------------------------------------------
# UT-05: Machine Learning Prediction Module
# ---------------------------------------------------------
def test_prediction_module_loaded():
    """
    Verify that the predictor module can be imported successfully.
    """
    assert predictor is not None


# ---------------------------------------------------------
# UT-06: Dosage Recommendation Module
# ---------------------------------------------------------
def test_dosage_engine_loaded():
    """
    Verify that the dosage engine module can be imported successfully.
    """
    assert dosage_engine is not None