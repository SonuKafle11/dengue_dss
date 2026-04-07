# Module 1: views.py is empty at this stage.
# Views will be added in Module 4 (Auth) and Module 5 (Patient/Doctor).
import hashlib
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages

from .models import User, AdminUser, PatientRecord
from ml_model.predictor import is_model_trained


# ── Helpers ──────────────────────────────────────────────────────────────────

def hash_password(raw):
    return hashlib.sha256(raw.encode()).hexdigest()

def current_user(request):
    uid = request.session.get('user_id')
    if uid:
        try:
            return User.objects.get(user_id=uid)
        except User.DoesNotExist:
            pass
    return None

def patient_required(fn):
    def wrap(request, *a, **kw):
        if not request.session.get('user_id') or request.session.get('role') != 'patient':
            return redirect('login')
        return fn(request, *a, **kw)
    wrap.__name__ = fn.__name__
    return wrap

def doctor_required(fn):
    def wrap(request, *a, **kw):
        if not request.session.get('user_id') or request.session.get('role') != 'doctor':
            return redirect('login')
        return fn(request, *a, **kw)
    wrap.__name__ = fn.__name__
    return wrap

def admin_required(fn):
    def wrap(request, *a, **kw):
        if not request.session.get('admin_logged_in'):
            return redirect('admin_login')
        return fn(request, *a, **kw)
    wrap.__name__ = fn.__name__
    return wrap


# ── Index ─────────────────────────────────────────────────────────────────────

def index(request):
    role = request.session.get('role')
    if role == 'patient':   return redirect('patient_dashboard')
    if role == 'doctor':    return redirect('doctor_dashboard')
    if request.session.get('admin_logged_in'): return redirect('admin_dashboard')
    return redirect('login')


# ── Auth ──────────────────────────────────────────────────────────────────────

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
            'registered_id': user.user_id, 'registered_name': name, 'registered_role': role
        })
    return render(request, 'core/register.html')


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


def logout_view(request):
    request.session.flush()
    return redirect('login')


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


def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


# ── Stubs (completed in Module 5 and 6) ──────────────────────────────────────

@patient_required
def patient_dashboard(request):
    return render(request, 'core/login.html')  # stub

@patient_required
def patient_form(request):
    return render(request, 'core/login.html')  # stub

@patient_required
def patient_result(request, record_id):
    return render(request, 'core/login.html')  # stub

@doctor_required
def doctor_dashboard(request):
    return render(request, 'core/login.html')  # stub

@doctor_required
def doctor_patient_detail(request, record_id):
    return render(request, 'core/login.html')  # stub

@doctor_required
def doctor_prediction_result(request, record_id):
    return render(request, 'core/login.html')  # stub

@admin_required
def admin_dashboard(request):
    return render(request, 'core/admin_login.html')  # stub

@admin_required
def admin_delete_user(request, user_id):
    return redirect('admin_login')

@admin_required
def admin_delete_record(request, record_id):
    return redirect('admin_login')

@admin_required
def admin_dataset_json(request):
    return JsonResponse({'status': 'stub - will be completed in Module 6'})