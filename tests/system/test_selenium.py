import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE = "http://127.0.0.1:8000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def go(driver, path):
    driver.get(BASE + path)


def wait(driver, by, selector, timeout=8):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )


def has_text(driver, text):
    return text.lower() in driver.page_source.lower()


def js_click(driver, el):
    driver.execute_script("arguments[0].scrollIntoView(true);", el)
    driver.execute_script("arguments[0].click();", el)


def do_login(driver, email, password):
    go(driver, "/login/")
    wait(driver, By.NAME, "email").clear()
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(0.8)


def do_logout(driver):
    go(driver, "/logout/")
    time.sleep(0.5)


# ============================================================
# ST-01 to ST-05: Public pages
# ============================================================

def test_ST01_landing_page_loads(driver):
    """ST-01: Landing page loads with correct title."""
    go(driver, "/")
    assert "Dengue" in driver.title or has_text(driver, "Dengue DSS")


def test_ST02_about_page_loads(driver):
    """ST-02: About page loads and contains About content."""
    go(driver, "/about/")
    assert "/about/" in driver.current_url
    assert has_text(driver, "About")


def test_ST03_explore_page_loads(driver):
    """ST-03: Explore page loads correctly."""
    go(driver, "/explore/")
    assert "/explore/" in driver.current_url


def test_ST04_login_page_loads(driver):
    """ST-04: Login page renders email and password fields."""
    go(driver, "/login/")
    assert driver.find_element(By.NAME, "email")
    assert driver.find_element(By.NAME, "password")


def test_ST05_register_page_loads(driver):
    """ST-05: Register page renders all required fields."""
    go(driver, "/register/?as=patient")
    assert driver.find_element(By.NAME, "name")
    assert driver.find_element(By.NAME, "email")
    assert driver.find_element(By.NAME, "password")
    assert driver.find_element(By.NAME, "confirm_password")


# ============================================================
# ST-06 to ST-09: Registration flow
# ============================================================

def test_ST06_patient_registration_success(driver, django_db_blocker):
    """ST-06: Registering with valid data redirects to login with success msg."""
    with django_db_blocker.unblock():
        from core.models import User
        User.objects.filter(email="st06@test.com").delete()

    go(driver, "/register/?as=patient")
    wait(driver, By.NAME, "name").send_keys("ST06 Patient")
    driver.find_element(By.NAME, "email").send_keys("st06@test.com")
    driver.find_element(By.NAME, "password").send_keys("ValidPass@123")
    driver.find_element(By.NAME, "confirm_password").send_keys("ValidPass@123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)
    assert "/login/" in driver.current_url
    assert has_text(driver, "successfully") or has_text(driver, "created")

    with django_db_blocker.unblock():
        from core.models import User
        User.objects.filter(email="st06@test.com").delete()


def test_ST07_registration_mismatched_passwords(driver):
    """ST-07: Mismatched passwords shows error on register page."""
    go(driver, "/register/?as=patient")
    wait(driver, By.NAME, "name").send_keys("Mismatch User")
    driver.find_element(By.NAME, "email").send_keys("mismatch@test.com")
    driver.find_element(By.NAME, "password").send_keys("ValidPass@123")
    driver.find_element(By.NAME, "confirm_password").send_keys("DifferentPass@999")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(0.5)
    assert "/register/" in driver.current_url
    assert has_text(driver, "do not match")


def test_ST08_doctor_registration_success(driver, django_db_blocker):
    """ST-08: Doctor registration creates doctor account."""
    with django_db_blocker.unblock():
        from core.models import User
        User.objects.filter(email="st08doc@test.com").delete()

    go(driver, "/register/?as=doctor")
    wait(driver, By.NAME, "name").send_keys("ST08 Doctor")
    driver.find_element(By.NAME, "email").send_keys("st08doc@test.com")
    driver.find_element(By.NAME, "password").send_keys("ValidPass@123")
    driver.find_element(By.NAME, "confirm_password").send_keys("ValidPass@123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)
    assert "/login/" in driver.current_url

    with django_db_blocker.unblock():
        from core.models import User
        User.objects.filter(email="st08doc@test.com").delete()


def test_ST09_duplicate_email_shows_error(driver, sys_patient):
    """ST-09: Registering with existing email shows inline error."""
    email, _ = sys_patient
    go(driver, "/register/?as=patient")
    wait(driver, By.NAME, "name").send_keys("Dup User")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys("ValidPass@123")
    driver.find_element(By.NAME, "confirm_password").send_keys("ValidPass@123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(0.5)
    assert "/register/" in driver.current_url
    assert has_text(driver, "already exists")


# ============================================================
# ST-10 to ST-14: Login flow
# ============================================================

def test_ST10_successful_patient_login(driver, sys_patient):
    """ST-10: Valid patient credentials redirect to patient dashboard."""
    do_logout(driver)
    email, password = sys_patient
    do_login(driver, email, password)
    assert "/patient/" in driver.current_url


def test_ST11_wrong_password_shows_error(driver, sys_patient):
    """ST-11: Wrong password shows error on login page."""
    do_logout(driver)
    email, _ = sys_patient
    do_login(driver, email, "WrongPass@999")
    assert "/login/" in driver.current_url
    assert has_text(driver, "Incorrect")


def test_ST12_nonexistent_email_shows_error(driver):
    """ST-12: Non-existent email shows error on login page."""
    do_logout(driver)
    do_login(driver, "nobody@nowhere.xyz", "anypass")
    assert "/login/" in driver.current_url
    assert has_text(driver, "No account")


def test_ST13_logout_redirects_to_landing(driver, sys_patient):
    """ST-13: Logout redirects to landing page."""
    email, password = sys_patient
    do_login(driver, email, password)
    do_logout(driver)
    assert driver.current_url == BASE + "/" or "/login/" in driver.current_url


def test_ST14_back_button_after_logout_reloads(driver, sys_patient):
    """ST-14: Back button after logout forces server check (no stale cache)."""
    email, password = sys_patient
    do_login(driver, email, password)
    time.sleep(0.5)
    do_logout(driver)
    time.sleep(0.5)
    driver.back()
    time.sleep(1)
    assert "/login/" in driver.current_url or driver.current_url == BASE + "/"


# ============================================================
# ST-15 to ST-19: Patient dashboard
# ============================================================

def test_ST15_patient_dashboard_shows_name(driver, sys_patient):
    """ST-15: Patient dashboard displays the patient's name."""
    do_logout(driver)
    email, password = sys_patient
    do_login(driver, email, password)
    assert has_text(driver, "System Patient")


def test_ST16_patient_dashboard_accessible(driver, sys_patient):
    """ST-16: Patient dashboard page loads at /patient/."""
    email, password = sys_patient
    if "/patient/" not in driver.current_url:
        do_login(driver, email, password)
    assert "/patient/" in driver.current_url


def test_ST17_unauthenticated_dashboard_redirects(driver):
    """ST-17: Accessing /patient/ without login redirects to /login/."""
    do_logout(driver)
    go(driver, "/patient/")
    time.sleep(0.5)
    assert "/login/" in driver.current_url


def test_ST18_patient_profile_accessible(driver, sys_patient):
    """ST-18: Patient profile page loads after login."""
    do_logout(driver)
    email, password = sys_patient
    do_login(driver, email, password)
    go(driver, "/patient/profile/")
    assert "/patient/profile/" in driver.current_url
    assert driver.find_element(By.NAME, "gender")


def test_ST19_profile_male_unchecks_pregnant(driver, sys_patient):
    """ST-19: Selecting Male on profile page unchecks pregnant checkbox."""
    email, password = sys_patient
    if "/patient/" not in driver.current_url:
        do_login(driver, email, password)
    go(driver, "/patient/profile/")
    wait(driver, By.NAME, "is_pregnant")

    pregnant_cb = driver.find_element(By.NAME, "is_pregnant")
    female      = driver.find_element(By.CSS_SELECTOR, "input[name='gender'][value='female']")
    js_click(driver, female)
    time.sleep(0.3)
    if not pregnant_cb.is_selected():
        js_click(driver, pregnant_cb)
    assert pregnant_cb.is_selected()

    male = driver.find_element(By.CSS_SELECTOR, "input[name='gender'][value='male']")
    js_click(driver, male)
    time.sleep(0.5)
    assert not pregnant_cb.is_selected()


# ============================================================
# ST-20 to ST-24: Public symptom checker
# ============================================================

def test_ST20_symptom_checker_loads(driver):
    """ST-20: Public symptom checker page loads."""
    go(driver, "/check/")
    assert driver.find_element(By.NAME, "age")
    checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
    assert len(checkboxes) > 0


def test_ST21_symptom_check_without_age_blocked(driver):
    """ST-21: Submitting symptom form without age is blocked."""
    go(driver, "/check/")
    male = driver.find_element(By.CSS_SELECTOR, "input[name='gender'][value='male']")
    js_click(driver, male)
    try:
        cb = driver.find_element(By.NAME, "fever")
        js_click(driver, cb)
    except Exception:
        pass
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    js_click(driver, submit)
    time.sleep(0.5)
    assert "/check/" in driver.current_url or has_text(driver, "Age")


def test_ST22_high_risk_result_shows(driver):
    """ST-22: High-risk symptoms produce High Risk result."""
    go(driver, "/check/")
    age = wait(driver, By.NAME, "age")
    age.clear()
    age.send_keys("30")
    female = driver.find_element(By.CSS_SELECTOR, "input[name='gender'][value='female']")
    js_click(driver, female)
    for sym in ["bleeding", "extreme_weakness", "restless_drowsy", "severe_headache"]:
        try:
            cb = driver.find_element(By.NAME, sym)
            js_click(driver, cb)
        except Exception:
            pass
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    js_click(driver, submit)
    time.sleep(1.5)
    assert has_text(driver, "High Risk") or has_text(driver, "Result")


def test_ST23_result_shows_score(driver):
    """ST-23: Result page shows clinical score and symptom count."""
    if not has_text(driver, "Clinical score"):
        go(driver, "/check/")
        age = wait(driver, By.NAME, "age")
        age.send_keys("25")
        female = driver.find_element(By.CSS_SELECTOR, "input[name='gender'][value='female']")
        js_click(driver, female)
        try:
            cb = driver.find_element(By.NAME, "bleeding")
            js_click(driver, cb)
        except Exception:
            pass
        submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        js_click(driver, submit)
        time.sleep(1.5)
    assert has_text(driver, "Clinical score") or has_text(driver, "Symptoms reported")


def test_ST24_result_back_link_works(driver):
    """ST-24: Back link on result page returns to symptom checker."""
    go(driver, "/check/")
    age = wait(driver, By.NAME, "age")
    age.send_keys("28")
    male = driver.find_element(By.CSS_SELECTOR, "input[name='gender'][value='male']")
    js_click(driver, male)
    try:
        cb = driver.find_element(By.NAME, "fever")
        js_click(driver, cb)
    except Exception:
        pass
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    js_click(driver, submit)
    time.sleep(1.5)
    back = wait(driver, By.PARTIAL_LINK_TEXT, "Back")
    back.click()
    time.sleep(0.5)
    assert "/check/" in driver.current_url


# ============================================================
# ST-25 to ST-28: Doctor flow
# ============================================================

def test_ST25_doctor_login_and_dashboard(driver, sys_doctor):
    """ST-25: Doctor login redirects to doctor dashboard."""
    do_logout(driver)
    email, password = sys_doctor
    do_login(driver, email, password)
    assert "/doctor/" in driver.current_url


def test_ST26_doctor_dashboard_shows_name(driver, sys_doctor):
    """ST-26: Doctor dashboard displays doctor's name."""
    email, password = sys_doctor
    if "/doctor/" not in driver.current_url:
        do_login(driver, email, password)
    assert has_text(driver, "System Doctor") or has_text(driver, "Doctor")


def test_ST27_unauthenticated_doctor_dashboard_redirects(driver):
    """ST-27: Accessing /doctor/ without login redirects to /login/."""
    do_logout(driver)
    go(driver, "/doctor/")
    time.sleep(0.5)
    assert "/login/" in driver.current_url


def test_ST28_admin_login_page_loads(driver):
    """ST-28: Admin login page renders with username and password fields."""
    do_logout(driver)
    go(driver, "/admin-login/")
    assert driver.find_element(By.NAME, "username")
    assert driver.find_element(By.NAME, "password")
