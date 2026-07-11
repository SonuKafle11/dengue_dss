# Dengue DSS — Dengue Decision Support System

A web-based clinical decision support system for dengue fever risk assessment and case management, built with Django and a custom Naive Bayes machine learning model.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Machine Learning Model](#machine-learning-model)
- [Setup and Installation](#setup-and-installation)
- [Running the Application](#running-the-application)
- [User Roles and Access](#user-roles-and-access)
- [Key URLs](#key-urls)
- [Testing](#testing)
- [Dependencies](#dependencies)

---

## Overview

Dengue DSS is a three-role web application that supports early detection and clinical management of dengue fever. Patients can check their symptoms without creating an account. Registered patients submit formal assessments which doctors review using lab results and ML predictions. Administrators oversee all users and records through a dedicated dashboard.

---

## Features

### Public (No Login Required)
- Symptom-based risk screening using a clinical scoring model
- High-risk and low-risk classification with next-step guidance
- Symptom data carries forward automatically when the user logs in or registers

### Patient
- Register and log in with email and password
- Submit dengue risk assessments (symptoms, age, weight, gender)
- View full assessment history on the dashboard
- Edit personal profile (age, weight, gender, pregnancy status)
- Pre-filled symptoms from previous assessments

### Doctor
- View all patient assessment records in a searchable queue
- Filter records by status (pending / reviewed)
- Enter lab values: NS1 Antigen, IgG, IgM, Platelet Count, WBC Count
- Receive ML-based dengue prediction with confidence score
- View automated dosage and fluid intake recommendations

### Admin
- View and manage all registered users and records
- Delete users and records with instant AJAX updates (no page reload)
- Monitor ML model status, dataset details, and accuracy

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 4.2 |
| Language | Python 3.11 |
| Database | SQLite (via Django ORM) |
| ML Model | Custom Hybrid Naive Bayes (Bernoulli + Gaussian) |
| Frontend | Django Templates, vanilla CSS, vanilla JavaScript |
| Email | Gmail SMTP |
| Session Management | Django sessions (DB-backed) |
| Unit & Integration Testing | pytest + pytest-django |
| System Testing | Selenium 4 + pytest |

---

## Project Structure

```
dengue_dss/
│
├── core/                            # Main Django application
│   ├── migrations/                  # Database migrations (11 total)
│   ├── static/
│   │   ├── css/                     # Page-specific stylesheets
│   │   │   ├── app.css              # Dashboard and app pages
│   │   │   ├── auth.css             # Login and register pages
│   │   │   ├── form.css             # Patient assessment form
│   │   │   ├── landing.css          # Landing, about, explore pages
│   │   │   ├── main.css             # Global base styles
│   │   │   ├── public_check.css     # Public symptom checker
│   │   │   └── result.css           # Public symptom result page
│   │   ├── images/
│   │   │   ├── hero-bg.png          # Hero section background
│   │   │   └── explore-us.png       # Explore page image
│   │   └── js/
│   │       └── main.js              # All client-side JavaScript
│   ├── templates/core/              # HTML templates (17 pages)
│   ├── management/commands/
│   │   └── create_admin.py          # Management command to create admin
│   ├── forms.py                     # Django form classes with validation
│   ├── middleware.py                # Cache-control middleware (back-button fix)
│   ├── models.py                    # User, AdminUser, PatientRecord models
│   ├── urls.py                      # URL routing
│   └── views.py                     # View functions for all pages
│
├── dengue_project/                  # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── ml_model/                        # Machine learning components
│   ├── naive_bayes.py               # Custom Hybrid Naive Bayes implementation
│   ├── train_model.py               # Model training script
│   ├── predictor.py                 # Prediction interface used by views
│   ├── dosage_engine.py             # Dosage and fluid recommendation engine
│   ├── naive_bayes_model.pkl        # Trained model (serialized)
│   ├── feature_names.json           # Feature names used in training
│   └── dataset_info.json            # Dataset statistics and model metadata
│
├── dataset/
│   └── dengue_dataset.csv           # Training dataset (1000 rows)
│
├── tests/                           # Full automated test suite
│   ├── conftest.py                  # Shared fixtures (users, clients, records)
│   ├── unit/
│   │   ├── test_models.py           # 19 model unit tests (UT-01 to UT-19)
│   │   ├── test_forms.py            # 19 form validation tests (UT-20 to UT-38)
│   │   └── test_ml.py               # 25 ML and dosage tests (UT-39 to UT-63)
│   ├── integration/
│   │   ├── test_auth.py             # 19 auth flow tests (IT-01 to IT-19)
│   │   ├── test_patient.py          # 19 patient flow tests (IT-20 to IT-38)
│   │   ├── test_doctor.py           # 16 doctor flow tests (IT-39 to IT-54)
│   │   └── test_admin.py            # 16 admin flow tests (IT-55 to IT-70)
│   └── system/
│       ├── conftest.py              # Selenium fixtures
│       └── test_selenium.py         # 28 end-to-end browser tests (ST-01 to ST-28)
│
├── manage.py
├── pytest.ini                       # pytest configuration
├── requirements.txt
└── db.sqlite3
```

---

## Machine Learning Model

The prediction engine uses a **Hybrid Naive Bayes** classifier:

- **Binary features** (Bernoulli NB): NS1 Antigen, IgG Antibody, IgM Antibody
- **Continuous features** (Gaussian NB): Platelet Count, WBC Count
- **Training dataset**: 1000 patient records, 82% model accuracy
- **Outlier removal**: IQR method applied to continuous features before training
- **Override rule**: If NS1 or IgM is positive, prediction is forced to **Positive Dengue** at 100% confidence — lab-confirmed results take priority over the statistical model

### Dosage Engine

Calculates treatment recommendations based on:
- Patient weight (Holliday-Segar formula for fluid intake)
- Risk level (clinical score from symptoms)
- Platelet count (transfusion and monitoring advice)
- Age and pregnancy status
- ML prediction result

To retrain the model with updated data:
```
python ml_model/train_model.py
```

---

## Setup and Installation

### 1. Clone the repository
```
git clone <repository-url>
cd dengue_dss
```

### 2. Create and activate a virtual environment
```
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Apply database migrations
```
python manage.py migrate
```

### 5. Create an admin account
```
python manage.py create_admin
```

### 6. Configure email (optional for development)

Open `dengue_project/settings.py` and update the email section:
```python
EMAIL_HOST_USER     = 'your@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
```

For development without real email, switch to the console backend:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### 7. Train the ML model (if not already trained)
```
python ml_model/train_model.py
```

---

## Running the Application

```
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

---

## User Roles and Access

| Role | How to Register | Login URL | Dashboard URL |
|---|---|---|---|
| Patient | `/register/?as=patient` | `/login/` | `/patient/` |
| Doctor | `/register/?as=doctor` | `/login/` | `/doctor/` |
| Admin | `python manage.py create_admin` | `/admin-login/` | `/admin-panel/` |

---

## Key URLs

| URL | Description |
|---|---|
| `/` | Landing page |
| `/about/` | About the system |
| `/explore/` | How it works |
| `/check/` | Public symptom checker (no login) |
| `/register/` | Patient / Doctor registration |
| `/login/` | Patient / Doctor login |
| `/logout/` | Logout |
| `/patient/` | Patient dashboard |
| `/patient/form/` | New assessment form |
| `/patient/result/<id>/` | Assessment result |
| `/patient/profile/` | Edit patient profile |
| `/doctor/` | Doctor queue dashboard |
| `/doctor/patient/<id>/` | Review patient record |
| `/doctor/result/<id>/` | View prediction result |
| `/admin-login/` | Admin login |
| `/admin-panel/` | Admin dashboard |

---

## Testing

The project has 161 automated tests across three levels.

### Test structure

| Level | Tool | Tests | What is covered |
|---|---|---|---|
| Unit | pytest + pytest-django | 63 | Models, forms, ML predictor, dosage engine |
| Integration | pytest + pytest-django (Django Client) | 70 | Auth flows, patient flow, doctor flow, admin flow |
| System | Selenium 4 + pytest | 28 | Full browser end-to-end flows |

### Running unit and integration tests

No server required:
```
pytest tests/unit/ tests/integration/ -v
```

### Running system tests

Requires the dev server running in a separate terminal:
```
# Terminal 1 — keep running
python manage.py runserver

# Terminal 2
pytest tests/system/ -v
```

### Running all tests
```
pytest tests/ -v
```

### Useful options
```
# Stop at first failure
pytest tests/unit/ tests/integration/ -v -x

# Run a specific test by ID
pytest tests/ -v -k "UT01"

# Short error summary
pytest tests/ -v --tb=short
```

---

## Dependencies

Key packages:

| Package | Version | Purpose |
|---|---|---|
| Django | 4.2 | Web framework |
| numpy | 2.4.4 | Numerical operations in ML model |
| scikit-learn | 1.8.0 | Used for dataset preprocessing |
| selenium | 4.44.0 | System testing |
| pytest | 9.0.3 | Test runner |
| pytest-django | 4.12.0 | Django integration for pytest |
| python-dotenv | 1.2.2 | Environment variable support |

Full list in `requirements.txt`.

---

## Security Notes

- Passwords are hashed using SHA-256
- Sessions are DB-backed with a 24-hour expiry
- All protected pages have `Cache-Control: no-store` headers via middleware to prevent back-button session leakage
- CSRF protection enabled on all forms
- `DEBUG = True` — set to `False` before deploying to production
- Email credentials are stored in `settings.py` — move to environment variables before production deployment
