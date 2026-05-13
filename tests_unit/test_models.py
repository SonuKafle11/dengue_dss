# tests_unit/test_models.py
import re
import pytest
from core.models import User, generate_user_id
from core.views import hash_password


def test_generate_user_id_format():
    """User ID must be 8 uppercase/digit characters."""
    uid = generate_user_id()
    assert len(uid) == 8
    assert re.fullmatch(r"[A-Z0-9]{8}", uid)


def test_hash_password_deterministic():
    """Same input produces same hash; different inputs differ."""
    assert hash_password("mypassword") == hash_password("mypassword")
    assert hash_password("password1") != hash_password("password2")


@pytest.mark.django_db
def test_user_creation():
    """User is saved with auto-generated unique 8-char ID."""
    u = User.objects.create(name="UnitUser", password="hashed", role="patient")
    assert len(u.user_id) == 8
    assert User.objects.filter(user_id=u.user_id).exists()