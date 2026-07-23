import pytest
from django.test import Client
from django.contrib.auth.hashers import make_password

# Shared DB fixtures
@pytest.fixture
def patient_user(db):
    from core.models import User
    user = User.objects.create(
        name="Test Patient",
        email="testpatient@example.com",
        password=make_password("TestPass@123"),
        role="patient",
        age=25,
        weight=60,
        gender="female",
        is_pregnant=False,
    )
    return user


@pytest.fixture
def doctor_user(db):
    from core.models import User
    user = User.objects.create(
        name="Test Doctor",
        email="testdoctor@example.com",
        password=make_password("TestPass@123"),
        role="doctor",
    )
    return user


@pytest.fixture
def admin_user(db):
    from core.models import AdminUser
    admin = AdminUser.objects.create(
        username="testadmin",
        password=make_password("AdminPass@123"),
    )
    return admin


@pytest.fixture
def patient_record(db, patient_user):
    from core.models import PatientRecord
    rec = PatientRecord(
        patient=patient_user,
        age=25,
        weight=60,
        gender="female",
        is_pregnant=False,
        fever=True,
        severe_headache=True,
        bleeding=True,
        extreme_weakness=True,
    )
    rec.save()
    return rec

# Authenticated client fixtures
@pytest.fixture
def patient_client(patient_user):
    client = Client()
    session = client.session
    session['user_id']   = patient_user.pk
    session['role']      = 'patient'
    session['user_name'] = patient_user.name
    session.save()
    return client


@pytest.fixture
def doctor_client(doctor_user):
    client = Client()
    session = client.session
    session['user_id']   = doctor_user.pk
    session['role']      = 'doctor'
    session['user_name'] = doctor_user.name
    session.save()
    return client


@pytest.fixture
def admin_client(admin_user):
    client = Client()
    session = client.session
    session['admin_logged_in'] = True
    session['admin_username']  = admin_user.username
    session.save()
    return client
