from django.views.decorators.cache import never_cache
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages

from .models import User, AdminUser, PatientRecord
from ml_model.predictor import predict_dengue, is_model_trained, get_dataset_info
from ml_model.dosage_engine import recommend_dosage, format_dosage_text

SYMPTOM_FIELDS = [
    'fever', 'severe_headache', 'joint_back_pain', 'nausea_vomiting',
    'skin_rash', 'vomiting_more_than_3', 'bleeding',
    'extreme_weakness', 'urine_output_low', 'fever_not_improving',
    'drop_in_fever_with_weakness', 'cold_hands_feet', 'restless_drowsy',
]

# Must match weights in PatientRecord.calculate_clinical_score()
SYMPTOM_WEIGHTS = {
    'fever': 2, 'severe_headache': 1, 'joint_back_pain': 1,
    'nausea_vomiting': 1, 'skin_rash': 1, 'vomiting_more_than_3': 2,
    'bleeding': 3, 'extreme_weakness': 2, 'urine_output_low': 2,
    'fever_not_improving': 1, 'drop_in_fever_with_weakness': 3,
    'cold_hands_feet': 2, 'restless_drowsy': 2,
}

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

def landing(request):
    return render(request, 'core/landing.html')

def index(request):
    role = request.session.get('role')
    if role == 'patient':
        return redirect('patient_dashboard')
    if role == 'doctor':
        return redirect('doctor_dashboard')
    if request.session.get('admin_logged_in'):
        return redirect('admin_dashboard')
    return redirect('landing')

def public_symptom_check(request):
    if request.method == 'POST':
        selected = [s for s in SYMPTOM_FIELDS if s in request.POST]

        if not selected:
            messages.error(request, 'Please select at least one symptom.')
            return render(request, 'core/public_symptom_form.html', {
                'symptoms': SYMPTOM_FIELDS, 'selected': [],
            })

        score = sum(SYMPTOM_WEIGHTS.get(s, 0) for s in selected)

        if score <= 4:
            risk_key, risk_label = 'low', 'Low Risk'
        elif score <= 8:
            risk_key, risk_label = 'possible', 'Possible Dengue'
        else:
            risk_key, risk_label = 'high', 'High Risk'

        # Stash so they carry over after login (only useful for High Risk)
        request.session['pending_symptoms'] = selected
        request.session['pending_score']    = score
        request.session['pending_risk']     = risk_key

        return render(request, 'core/public_symptom_result.html', {
            'selected': selected, 'score': score,
            'risk_key': risk_key, 'risk_label': risk_label,
        })

    return render(request, 'core/public_symptom_form.html', {
        'symptoms': SYMPTOM_FIELDS, 'selected': [],
    })

def register(request):
    # Default to patient unless explicitly requested via ?as=doctor
    requested_as = request.GET.get('as', 'patient')
    if requested_as not in ('patient', 'doctor'):
        requested_as = 'patient'

    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        password = request.POST.get('password', '').strip()
        role     = request.POST.get('role', 'patient').strip()

        if role not in ('patient', 'doctor'):
            role = 'patient'

        if not name or not password:
            messages.error(request, 'Name and password are required.')
            return render(request, 'core/register.html', {'as_role': role})

        if User.objects.filter(name=name, role=role).exists():
            messages.error(request, f'A {role} account with this name already exists.')
            return render(request, 'core/register.html', {'as_role': role})

        user = User(name=name, password=hash_password(password), role=role)
        user.save()

        return render(request, 'core/register.html', {
            'registered_id': user.user_id,
            'registered_role': role,
            'as_role': role,
        })

    return render(request, 'core/register.html', {'as_role': requested_as})
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
            # Patient came in via High-Risk public check → send to form directly
            if user.role == 'patient' and request.session.get('pending_symptoms'):
                return redirect('patient_form')
            return redirect('patient_dashboard' if user.role == 'patient' else 'doctor_dashboard')

        messages.error(request, 'Invalid credentials. Check your ID/name and password.')
    return render(request, 'core/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('landing')

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

@never_cache
@patient_required
def patient_dashboard(request):
    user    = current_user(request)
    records = PatientRecord.objects.filter(patient=user).order_by('-created_at')
    return render(request, 'core/patient_dashboard.html', {
        'user': user, 'records': records,
    })

@never_cache
@patient_required
def patient_form(request):
    user = current_user(request)
    pending_symptoms = request.session.get('pending_symptoms', [])

    if request.method == 'POST':
        try:
            gender = request.POST.get("gender")
            age    = float(request.POST.get('age', 0))
            weight = float(request.POST.get('weight', 0))
            height = float(request.POST.get('height', 0))
            if age <= 0 or weight <= 0:
                raise ValueError("Age and weight must be positive.")
            if height <= 0:
                raise ValueError("Height must be positive (in cm).")
            is_pregnant = request.POST.get('is_pregnant') == 'on'
            if is_pregnant:
                if gender != "female":
                    messages.error(request, "Only females can be pregnant.")
                    return redirect('patient_form')
                if age < 10:
                    messages.error(request, "Pregnancy not valid for age below 10.")
                    return redirect('patient_form')

            if not any(symptom in request.POST for symptom in SYMPTOM_FIELDS):
                messages.error(request, "Please select at least one symptom.")
                return redirect('patient_form')

            rec = PatientRecord(
                patient=user, age=age, weight=weight, height=height,
                gender=gender, is_pregnant=is_pregnant,
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
            rec.save()
            user.age         = age
            user.weight      = weight
            user.height      = height
            user.gender      = gender
            user.is_pregnant = is_pregnant
            user.save()
            # Clear stashed symptoms — they've been consumed
            for k in ('pending_symptoms', 'pending_score', 'pending_risk'):
                request.session.pop(k, None)

            return redirect('patient_result', record_id=rec.record_id)
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid input: {e}')

    last_record = PatientRecord.objects.filter(patient=user).order_by('-created_at').first()
    last_symptoms = []
    if last_record:
        for s in SYMPTOM_FIELDS:
            if getattr(last_record, s, False):
                last_symptoms.append(s)
    prefill_symptoms = list(set(last_symptoms) | set(pending_symptoms))
    return render(request, 'core/patient_form.html', {
        'user': user,
        'pending_symptoms': pending_symptoms,
        'prefill_symptoms': prefill_symptoms,
        'has_previous_record': last_record is not None,
        'profile': {                                          
        'age':         user.age or '',
        'weight':      user.weight or '',
        'height':      user.height or '',
        'gender':      user.gender or '',
        'is_pregnant': user.is_pregnant,
    },
    })

@never_cache
@patient_required
def patient_result(request, record_id):
    user = current_user(request)
    rec  = get_object_or_404(PatientRecord, record_id=record_id, patient=user)
    return render(request, 'core/patient_result.html', {'record': rec, 'user': user})

@never_cache
@patient_required
def patient_profile(request):
    user = current_user(request)

    if request.method == 'POST':
        try:
            age_str    = request.POST.get('age', '').strip()
            weight_str = request.POST.get('weight', '').strip()
            height_str = request.POST.get('height', '').strip()
            gender     = request.POST.get('gender', '').strip()
            is_pregnant = request.POST.get('is_pregnant') == 'on'

            user.age    = float(age_str)    if age_str    else None
            user.weight = float(weight_str) if weight_str else None
            user.height = float(height_str) if height_str else None
            user.gender = gender if gender in ('male', 'female', 'other') else ''
            user.is_pregnant = is_pregnant
            user.save()

            messages.success(request, 'Profile updated successfully.')
            return redirect('patient_dashboard')
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid input: {e}')

    return render(request, 'core/patient_profile.html', {'user': user})

@never_cache
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
        'user': user, 'records': records,
        'search': search, 'status_filter': status,
        'total'   : PatientRecord.objects.count(),
        'pending' : PatientRecord.objects.filter(is_reviewed=False).count(),
        'reviewed': PatientRecord.objects.filter(is_reviewed=True).count(),
    })

@never_cache
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

            ml_input = {
                'fever'                       : int(rec.fever),
                'severe_headache'             : int(rec.severe_headache),
                'joint_back_pain'             : int(rec.joint_back_pain),
                'nausea_vomiting'             : int(rec.nausea_vomiting),
                'skin_rash'                   : int(rec.skin_rash),
                'vomiting_more_than_3'        : int(rec.vomiting_more_than_3),
                'bleeding'                    : int(rec.bleeding),
                'extreme_weakness'            : int(rec.extreme_weakness),
                'urine_output_low'            : int(rec.urine_output_low),
                'fever_not_improving'         : int(rec.fever_not_improving),
                'drop_in_fever_with_weakness' : int(rec.drop_in_fever_with_weakness),
                'cold_hands_feet'             : int(rec.cold_hands_feet),
                'restless_drowsy'             : int(rec.restless_drowsy),
                'platelet_count'              : platelet,
                'wbc_count'                   : wbc,
                'IgM_value'                   : igm, 
                'IgG_value'                   : igg,       
            }
            ml_res = predict_dengue(ml_input)
            rec.ml_prediction = ml_res['prediction']
            rec.ml_confidence = ml_res['confidence']

            dosage_rec = recommend_dosage(
                weight_kg=rec.weight,
                age=rec.age,
                risk_level=rec.clinical_risk_level,
                height_cm=rec.height,
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
        'record': rec, 'doctor': doctor,
        'model_trained': is_model_trained(),
    })

@never_cache
@doctor_required
def doctor_prediction_result(request, record_id):
    doctor = current_user(request)
    rec    = get_object_or_404(PatientRecord, record_id=record_id)

    dosage_rec = None
    if rec.platelet_count is not None:
        dosage_rec = recommend_dosage(
            weight_kg=rec.weight,
            age=rec.age,
            risk_level=rec.clinical_risk_level,
            height_cm=rec.height,
            platelet_count=rec.platelet_count,
            is_pregnant=rec.is_pregnant,
            ml_prediction=rec.ml_prediction,
        )
    return render(request, 'core/doctor_prediction_result.html', {
        'record': rec, 'doctor': doctor, 'dosage': dosage_rec,
    })

@never_cache
@admin_required
def admin_dashboard(request):
    users   = User.objects.all().order_by('-created_at')
    records = PatientRecord.objects.select_related('patient').order_by('-created_at')
    return render(request, 'core/admin_dashboard.html', {
        'users': users, 'records': records,
        'dataset_info' : get_dataset_info(),
        'model_trained': is_model_trained(),
        'total_patients' : User.objects.filter(role='patient').count(),
        'total_doctors'  : User.objects.filter(role='doctor').count(),
        'total_records'  : records.count(),
        'reviewed_records': records.filter(is_reviewed=True).count(),
        'admin_username' : request.session.get('admin_username'),
    })

@never_cache
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

@never_cache
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

@never_cache
@admin_required
def admin_dataset_json(request):
    info = get_dataset_info()
    if info:
        return JsonResponse(info)
    return JsonResponse({'error': 'Model not trained yet.'}, status=404)