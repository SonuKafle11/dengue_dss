# tests_system/test_auth.py
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.models import User
from core.views import hash_password


@pytest.mark.django_db(transaction=True)
def test_register_patient(browser, live_server):
    """Register a new patient via the UI."""
    browser.get(live_server.url + "/register/")

    # Click the patient radio
    browser.find_element(By.CSS_SELECTOR, 'input[value="patient"]').click()

    # Fill the form
    browser.find_element(By.NAME, "name").send_keys("SysNewPatient")
    browser.find_element(By.NAME, "password").send_keys("pw12345")

    # Submit
    browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    # Wait for the success message to appear
    WebDriverWait(browser, 5).until(
        lambda d: "Registration successful" in d.page_source
    )

    assert "Registration successful" in browser.page_source


@pytest.mark.django_db(transaction=True)
def test_login_with_user_id(browser, live_server):
    """Create a user directly in DB, then log in through the UI."""
    # Create the user in the test database
    user = User.objects.create(
        name="SysTestPatient",
        password=hash_password("syspass123"),
        role="patient",
    )

    browser.get(live_server.url + "/login/")
    browser.find_element(By.NAME, "identifier").send_keys(user.user_id)
    browser.find_element(By.NAME, "password").send_keys("syspass123")
    browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    # Wait for redirect away from /login/
    WebDriverWait(browser, 5).until(
        lambda d: "/login/" not in d.current_url
    )

    assert "/patient/" in browser.current_url


@pytest.mark.django_db(transaction=True)
def test_patient_dashboard_requires_login(browser, live_server):
    """Direct access to /patient/ without login should redirect to /login/."""
    browser.get(live_server.url + "/patient/")
    assert "/login/" in browser.current_url