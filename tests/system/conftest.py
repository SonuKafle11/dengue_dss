"""
tests/system/conftest.py
Selenium fixtures for system tests.
"""
# ADD at the top:
from django.contrib.auth.hashers import make_password
import pytest

@pytest.fixture(scope="session")
def driver():
    """Headless Chrome WebDriver — shared across all system tests."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--disable-gpu")

    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(6)
    yield drv
    drv.quit()


@pytest.fixture(scope="session")
def sys_patient(django_db_blocker):
    """Creates a patient user in the live DB for system tests."""
    from core.models import User
    email    = "sys_patient@test.com"
    password = "SysPass@123"

    with django_db_blocker.unblock():
        User.objects.filter(email=email).delete()
        User.objects.create(
            name="System Patient",
            email=email,
            password=make_password(password),
            role="patient",
            age=25,
            weight=60,
            gender="female",
        )

    yield email, password

    with django_db_blocker.unblock():
        User.objects.filter(email=email).delete()


@pytest.fixture(scope="session")
def sys_doctor(django_db_blocker):
    """Creates a doctor user in the live DB for system tests."""
    from core.models import User
    email    = "sys_doctor@test.com"
    password = "SysPass@123"

    with django_db_blocker.unblock():
        User.objects.filter(email=email).delete()
        User.objects.create(
            name="System Doctor",
            email=email,
            password=make_password(password),
            role="doctor",
        )

    yield email, password

    with django_db_blocker.unblock():
        User.objects.filter(email=email).delete()
