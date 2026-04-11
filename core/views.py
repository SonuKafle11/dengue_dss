import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages

from .models import User, AdminUser, PatientRecord
from ml_model.predictor import predict_dengue, is_model_trained, get_dataset_info
from ml_model.dosage_engine import recommend_dosage, format_dosage_text


# ═══════════════════════════════════════════════════════════════
# HELPERS — used by all views below
# ═══════════════════════════════════════════════════════════════

def hash_password(raw):
    """Convert plain text password to SHA-256 hash before saving."""
    return hashlib.sha256(raw.encode()).hexdigest()


def current_user(request):
    """Return the logged-in User object from session, or None."""
    uid = request.session.get('user_id')
    if uid:
        try:
            return User.objects.get(user_id=uid)
        except User.DoesNotExist:
            pass
    return None


def patient_required(fn):
    """Decorator — blocks access if user is not logged in as patient."""
    def wrap(request, *a, **kw):
        if not request.session.get('user_id') or request.session.get('role') != 'patient':
            return redirect('login')
        return fn(request, *a, **kw)
    wrap.__name__ = fn.__name__
    return wrap


def doctor_required(fn):
    """Decorator — blocks access if user is not logged in as doctor."""
    def wrap(request, *a, **kw):
        if not request.session.get('user_id') or request.session.get('role') != 'doctor':
            return redirect('login')
        return fn(request, *a, **kw)
    wrap.__name__ = fn.__name__
    return wrap


def admin_required(fn):
    """Decorator — blocks access if admin is not logged in."""
    def wrap(request, *a, **kw):
        if not request.session.get('admin_logged_in'):
            return redirect('admin_login')
        return fn(request, *a, **kw)
    wrap.__name__ = fn.__name__
    return wrap


# ═══════════════════════════════════════════════════════════════
# INDEX
# Template: none (pure redirect)
# URL: /
# ═══════════════════════════════════════════════════════════════

def index(request):
    role = request.session.get('role')
    if role == 'patient':   return redirect('patient_dashboard')
    if role == 'doctor':    return redirect('doctor_dashboard')
    if request.session.get('admin_logged_in'): return redirect('admin_dashboard')
    return redirect('login')


# ═══════════════════════════════════════════════════════════════
# AUTH VIEWS
# ═══════════════════════════════════════════════════════════════

# Template: core/templates/core/register.html
# URL: /register/
# What it does: shows registration form, creates User with hashed
#               password, returns unique 8-char ID on success
def register(request):
    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        password = request.POST.get('password', '').strip()
        role     = request.POST.get('role', '').strip()

        if not name or not password or role not in ('patient', 'doctor'):
            messages.error(request, 'All fields are required.')
            return render(request, 'core/register.html')

        if User.objects.filter(name__iexact=name, role=role).exists():
            messages.error(request, f'A {role} with the name "{name}" already exists.')
            return render(request, 'core/register.html')

        user = User(name=name, password=hash_password(password), role=role)
        user.save()
        return render(request, 'core/register.html', {
            'registered_id'  : user.user_id,
            'registered_name': name,
            'registered_role': role
        })
    return render(request, 'core/register.html')


# Template: core/templates/core/login.html
# URL: /login/
# What it does: accepts user_id or name + password, stores role
#               in session, redirects to correct dashboard
def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password   = request.POST.get('password', '').strip()
        user = None

        try:
            user = User.objects.get(user_id=identifier)
        except User.DoesNotExist:
            qs = User.objects.filter(name__iexact=identifier)
            if qs.count() == 1:
                user = qs.first()
            elif qs.count() > 1:
                messages.error(request, 'Multiple accounts share that name. Please log in using your unique ID.')
                return render(request, 'core/login.html')

        if user and user.password == hash_password(password):
            request.session['user_id']   = user.user_id
            request.session['role']      = user.role
            request.session['user_name'] = user.name
            return redirect('patient_dashboard' if user.role == 'patient' else 'doctor_dashboard')

        messages.error(request, 'Invalid credentials. Check your ID/name and password.')
    return render(request, 'core/login.html')


# Template: none (pure redirect)
# URL: /logout/
# What it does: clears entire session and redirects to login
def logout_view(request):
    request.session.flush()
    return redirect('login')


# Template: core/templates/core/admin_login.html
# URL: /admin-login/
# What it does: separate login for admin, stores admin_logged_in
#               in session
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            admin = AdminUser.objects.get(username=username)
            if admin.password == hash_password(password):
                request.session['admin_logged_in'] = True
                request.session['admin_username']  = username
                return redirect('admin_dashboard')
            messages.error(request, 'Wrong password.')
        except AdminUser.DoesNotExist:
            messages.error(request, 'Admin account not found.')
    return render(request, 'core/admin_login.html')


# Template: none (pure redirect)
# URL: /admin-logout/
# What it does: clears session and redirects to admin login
def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


# ═══════════════════════════════════════════════════════════════
# PATIENT VIEWS
# ═══════════════════════════════════════════════════════════════

# Template: core/templates/core/patient_dashboard.html
# URL: /patient/
# What it does: fetches all records for logged-in patient,
#               shows them as cards with risk badges and review status
@patient_required
def patient_dashboard(request):
    user    = current_user(request)
    records = PatientRecord.objects.filter(patient=user).order_by('-created_at')
    return render(request, 'core/patient_dashboard.html', {
        'user'   : user,
        'records': records
    })


# Template: core/templates/core/patient_form.html
# URL: /patient/form/
# What it does: shows 13 symptom checkboxes with live JS score,
#               on POST creates PatientRecord and calls rec.save()
#               which auto-calculates clinical_score and risk_level
@patient_required
def patient_form(request):
    user = current_user(request)
    if request.method == 'POST':
        try:
            age    = float(request.POST.get('age', 0))
            weight = float(request.POST.get('weight', 0))
            if age <= 0 or weight <= 0:
                raise ValueError("Age and weight must be positive.")
            is_pregnant = request.POST.get('is_pregnant') == 'on'

            rec = PatientRecord(
                patient=user, age=age, weight=weight, is_pregnant=is_pregnant,
                fever                       = 'fever' in request.POST,
                severe_headache             = 'severe_headache' in request.POST,
                joint_back_pain             = 'joint_back_pain' in request.POST,
                nausea_vomiting             = 'nausea_vomiting' in request.POST,
                skin_rash                   = 'skin_rash' in request.POST,
                vomiting_more_than_3        = 'vomiting_more_than_3' in request.POST,
                bleeding                    = 'bleeding' in request.POST,
                extreme_weakness            = 'extreme_weakness' in request.POST,
                urine_output_low            = 'urine_output_low' in request.POST,
                fever_not_improving         = 'fever_not_improving' in request.POST,
                drop_in_fever_with_weakness = 'drop_in_fever_with_weakness' in request.POST,
                cold_hands_feet             = 'cold_hands_feet' in request.POST,
                restless_drowsy             = 'restless_drowsy' in request.POST,
            )
            rec.save()  # triggers calculate_clinical_score() and get_risk_level()
            return redirect('patient_result', record_id=rec.record_id)
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid input: {e}')
    return render(request, 'core/patient_form.html', {'user': user})


# Template: core/templates/core/patient_result.html
# URL: /patient/result/<uuid>/
# What it does: fetches a single record by UUID, shows clinical
#               score, reported symptoms, and review status
@patient_required
def patient_result(request, record_id):
    user = current_user(request)
    rec  = get_object_or_404(PatientRecord, record_id=record_id, patient=user)
    return render(request, 'core/patient_result.html', {
        'record': rec,
        'user'  : user
    })


# ═══════════════════════════════════════════════════════════════
# DOCTOR VIEWS
# ═══════════════════════════════════════════════════════════════

# Template: core/templates/core/doctor_dashboard.html
# URL: /doctor/
# What it does: fetches ALL patient records, supports search by
#               name and filter by pending/reviewed, shows stats
@doctor_required
def doctor_dashboard(request):
    user    = current_user(request)
    records = PatientRecord.objects.select_related('patient', 'reviewed_by').order_by('-created_at')
    search  = request.GET.get('search', '').strip()
    status  = request.GET.get('status', '')

    if search:
        records = records.filter(patient__name__icontains=search)
    if status == 'reviewed':
        records = records.filter(is_reviewed=True)
    elif status == 'pending':
        records = records.filter(is_reviewed=False)

    return render(request, 'core/doctor_dashboard.html', {
        'user'         : user,
        'records'      : records,
        'search'       : search,
        'status_filter': status,
        'total'        : PatientRecord.objects.count(),
        'pending'      : PatientRecord.objects.filter(is_reviewed=False).count(),
        'reviewed'     : PatientRecord.objects.filter(is_reviewed=True).count(),
    })


# Template: core/templates/core/doctor_patient_detail.html
# URL: /doctor/patient/<uuid>/
# What it does: shows patient info + symptoms (read-only left side),
#               on POST takes lab values, calls predict_dengue()
#               from ml_model/predictor.py, calls recommend_dosage()
#               from ml_model/dosage_engine.py, saves to database
@doctor_required
def doctor_patient_detail(request, record_id):
    doctor = current_user(request)
    rec    = get_object_or_404(PatientRecord, record_id=record_id)

    if request.method == 'POST':
        try:
            platelet = float(request.POST.get('platelet_count', 0))
            wbc      = float(request.POST.get('wbc_count', 0))
            igg      = float(request.POST.get('igg', 0))
            igm      = float(request.POST.get('igm', 0))

            rec.platelet_count = platelet
            rec.wbc_count      = wbc
            rec.igg            = igg
            rec.igm            = igm
            rec.reviewed_by    = doctor
            rec.is_reviewed    = True

            # build feature dict and run Naive Bayes prediction
            ml_input = {
                'fever'               : int(rec.fever),
                'severe_headache'     : int(rec.severe_headache),
                'joint_back_pain'     : int(rec.joint_back_pain),
                'nausea_vomiting'     : int(rec.nausea_vomiting),
                'skin_rash'           : int(rec.skin_rash),
                'vomiting_more_than_3': int(rec.vomiting_more_than_3),
                'platelet_count'      : platelet,
                'wbc_count'           : wbc,
            }
            ml_res = predict_dengue(ml_input)
            rec.ml_prediction = ml_res['prediction']
            rec.ml_confidence = ml_res['confidence']

            # generate dosage using if-then rules
            dosage_rec = recommend_dosage(
                weight_kg=rec.weight,
                age=rec.age,
                risk_level=rec.clinical_risk_level,
                platelet_count=platelet,
                is_pregnant=rec.is_pregnant,
                ml_prediction=ml_res['prediction'],
            )
            rec.dosage_recommendation = format_dosage_text(dosage_rec)
            rec.save()
            return redirect('doctor_prediction_result', record_id=rec.record_id)

        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid input: {e}')

    return render(request, 'core/doctor_patient_detail.html', {
        'record'       : rec,
        'doctor'       : doctor,
        'model_trained': is_model_trained()
    })


# Template: core/templates/core/doctor_prediction_result.html
# URL: /doctor/result/<uuid>/
# What it does: shows ML prediction banner, confidence %,
#               lab results, clinical score, full dosage section
@doctor_required
def doctor_prediction_result(request, record_id):
    doctor = current_user(request)
    rec    = get_object_or_404(PatientRecord, record_id=record_id)

    # rebuild dosage dict from saved record for template display
    dosage_rec = None
    if rec.platelet_count is not None:
        dosage_rec = recommend_dosage(
            weight_kg=rec.weight,
            age=rec.age,
            risk_level=rec.clinical_risk_level,
            platelet_count=rec.platelet_count,
            is_pregnant=rec.is_pregnant,
            ml_prediction=rec.ml_prediction,
        )
    return render(request, 'core/doctor_prediction_result.html', {
        'record': rec,
        'doctor': doctor,
        'dosage': dosage_rec
    })


# ═══════════════════════════════════════════════════════════════
# ADMIN VIEWS
# ═══════════════════════════════════════════════════════════════

# Template: core/templates/core/admin_dashboard.html
# URL: /admin-panel/
# What it does: shows all users, all records, ML model status,
#               dataset info, stat counts
@admin_required
def admin_dashboard(request):
    users   = User.objects.all().order_by('-created_at')
    records = PatientRecord.objects.select_related('patient').order_by('-created_at')
    return render(request, 'core/admin_dashboard.html', {
        'users'           : users,
        'records'         : records,
        'dataset_info'    : get_dataset_info(),
        'model_trained'   : is_model_trained(),
        'total_patients'  : User.objects.filter(role='patient').count(),
        'total_doctors'   : User.objects.filter(role='doctor').count(),
        'total_records'   : records.count(),
        'reviewed_records': records.filter(is_reviewed=True).count(),
        'admin_username'  : request.session.get('admin_username'),
    })


# Template: none (redirects back to admin_dashboard)
# URL: /admin-panel/delete-user/<user_id>/
# What it does: deletes a User and all their records via CASCADE
@admin_required
def admin_delete_user(request, user_id):
    if request.method == 'POST':
        try:
            u = User.objects.get(user_id=user_id)
            name = u.name
            u.delete()
            messages.success(request, f'User "{name}" deleted.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return redirect('admin_dashboard')


# Template: none (redirects back to admin_dashboard)
# URL: /admin-panel/delete-record/<uuid>/
# What it does: deletes a single PatientRecord
@admin_required
def admin_delete_record(request, record_id):
    if request.method == 'POST':
        try:
            r = PatientRecord.objects.get(record_id=record_id)
            r.delete()
            messages.success(request, 'Record deleted.')
        except PatientRecord.DoesNotExist:
            messages.error(request, 'Record not found.')
    return redirect('admin_dashboard')


# Template: none (returns JSON response)
# URL: /admin-panel/dataset-json/
# What it does: returns dataset_info.json as JSON API response
@admin_required
def admin_dataset_json(request):
    info = get_dataset_info()
    if info:
        return JsonResponse(info)
    return JsonResponse({'error': 'Model not trained yet.'}, status=404)