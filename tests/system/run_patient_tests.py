import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = "http://127.0.0.1:8000"
driver = webdriver.Chrome()
driver.implicitly_wait(5)

wait = WebDriverWait(driver, 10)

def login(email, password):
    driver.get(BASE + "/login/")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)

try:
    # ST-01 Patient Registration
    driver.get(BASE + "/register/?as=patient")
    wait.until(EC.presence_of_element_located((By.NAME, "name"))).send_keys("ST Patient")
    driver.find_element(By.NAME, "email").send_keys("patient@test.com")
    driver.find_element(By.NAME, "password").send_keys("patient1234")
    driver.find_element(By.NAME, "confirm_password").send_keys("patient1234")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)

    # ST-02 Patient Login
    login("patient@test.com", "patient1234")

    # ST-03 Update Profile
    driver.get(BASE + "/patient/profile/")
    wait.until(EC.presence_of_element_located((By.NAME, "age"))).clear()
    driver.find_element(By.NAME, "age").send_keys("28")
    driver.find_element(By.NAME, "weight").clear()
    driver.find_element(By.NAME, "weight").send_keys("65")
    driver.find_element(By.CSS_SELECTOR, "input[name='gender'][value='female']").click()
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)

    # ST-04 Submit Assessment
    driver.get(BASE + "/patient/form/")
    wait.until(EC.presence_of_element_located((By.NAME, "age"))).clear()
    driver.find_element(By.NAME, "age").send_keys("28")
    driver.find_element(By.NAME, "weight").clear()
    driver.find_element(By.NAME, "weight").send_keys("65")
    driver.find_element(By.CSS_SELECTOR, "input[name='gender'][value='female']").click()
    for symptom in ["fever", "bleeding", "severe_headache"]:
        try:
            driver.find_element(By.NAME, symptom).click()
        except:
            pass
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)

    # ST-05 View Result
    assert "/patient/result/" in driver.current_url

    # ST-06 Doctor Login
    driver.get(BASE + "/logout/")
    login("doctor@test.com", "doctor1234")

finally:
    driver.quit()