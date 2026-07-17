from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import User, AdminUser, PatientRecord
from .forms import RegisterForm, LoginForm, PatientProfileForm
from ml_model.predictor import predict_dengue, is_model_trained, get_dataset_info
from ml_model.dosage_engine import recommend_dosage, format_dosage_text

SYMPTOM_FIELDS = [
    'fever', 'severe_headache', 'joint_back_pain', 'nausea_vomiting',
    'skin_rash', 'vomiting_more_than_3', 'bleeding',
    'extreme_weakness', 'urine_output_low', 'fever_not_improving',
    'drop_in_fever_with_weakness', 'cold_hands_feet', 'restless_drowsy', 'abdominal_pain',
]

SYMPTOM_WEIGHTS = {
    'fever': 1, 'severe_headache': 2, 'joint_back_pain': 2,
    'nausea_vomiting': 1, 'skin_rash': 0.5, 'vomiting_more_than_3': 2,
    'bleeding': 3, 'extreme_weakness': 3, 'urine_output_low': 3,
    'fever_not_improving': 2, 'drop_in_fever_with_weakness': 3,
    'cold_hands_feet': 1, 'restless_drowsy': 3, 'abdominal_pain': 1,
}

# Helpers

def current_user(request):
    uid = request.session.get('user_id')
    if uid:
        try:
            return User.objects.get(user_id=uid)
        except User.DoesNotExist:
            pass
    return None

# Access-control decorators
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

# Public pages
def landing(request):
    return render(request, 'core/landing.html')


def about(request):
    return render(request, 'core/about.html')


def explore(request):
    return render(request, 'core/explore.html')


def index(request):
    role = request.session.get('role')
    if role == 'patient':
        return redirect('patient_dashboard')
    if role == 'doctor':
        return redirect('doctor_dashboard')
    if request.session.get('admin_logged_in'):
        return redirect('admin_dashboard')
    return redirect('landing')

# Public symptom checker
def public_symptom_check(request):
    if request.method == 'POST':
        selected = [s for s in SYMPTOM_FIELDS if s in request.POST]

        age_str  = request.POST.get('age', '').strip()
        gender   = request.POST.get('gender', '')
        pregnant = 'pregnant' in request.POST

        if not age_str:
            messages.error(request, 'Age is required for risk assessment.')
            return render(request, 'core/public_symptom_form.html', {
                'symptoms': SYMPTOM_FIELDS, 'selected': selected,
            })
        try:
            age = float(age_str)
        except ValueError:
            messages.error(request, 'Age must be a valid number.')
            return render(request, 'core/public_symptom_form.html', {
                'symptoms': SYMPTOM_FIELDS, 'selected': selected,
            })
        if age <= 0:
            messages.error(request, 'Age must be a positive number.')
            return render(request, 'core/public_symptom_form.html', {
                'symptoms': SYMPTOM_FIELDS, 'selected': selected,
            })
        if gender not in ('male', 'female', 'other'):
            messages.error(request, 'Please select your sex/gender.')
            return render(request, 'core/public_symptom_form.html', {
                'symptoms': SYMPTOM_FIELDS, 'selected': selected,
            })

        score = sum(SYMPTOM_WEIGHTS.get(s, 0) for s in selected)
        if age >= 70:
            score += 1
        if pregnant:
            score += 1

        risk_key   = 'high' if score > 4 else 'low'
        risk_label = 'High Risk' if score > 4 else 'Low Risk'

        request.session['pending_symptoms'] = selected
        request.session['pending_score']    = score
        request.session['pending_risk']     = risk_key
        request.session['pending_age']      = age_str
        request.session['pending_gender']   = gender
        request.session['pending_pregnant'] = pregnant

        return render(request, 'core/public_symptom_result.html', {
            'selected': selected, 'score': score,
            'risk_key': risk_key, 'risk_label': risk_label,
        })

    return render(request, 'core/public_symptom_form.html', {
        'symptoms': SYMPTOM_FIELDS, 'selected': [],
        'age_value': '', 'gender_value': '', 'pregnant_value': False,
    })

def register(request):
    requested_as = request.GET.get('as', 'patient')
    if requested_as not in ('patient', 'doctor'):
        requested_as = 'patient'

    if request.method == 'POST':
        role = request.POST.get('role', 'patient')
        if role not in ('patient', 'doctor'):
            role = 'patient'

        form = RegisterForm(request.POST)
        if form.is_valid():
            name     = form.cleaned_data['name']
            email    = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Only clear stale auth keys — do NOT flush the whole session
            # because pending_symptoms/age/gender from the public check must survive
            request.session.pop('user_id', None)
            request.session.pop('role', None)
            request.session.pop('user_name', None)

            User(
                name=name,
                email=email,
                password=make_password(password),
                role=role,
            ).save()

            # set a one-time session flag so the login page can show a popup
            request.session['account_created_msg'] = 'Account created successfully! Please log in.'
            return redirect('login')

        return render(request, 'core/register.html', {
            'form': form,
            'as_role': role,
        })

    form = RegisterForm(initial={'role': requested_as})
    return render(request, 'core/register.html', {
        'form': form,
        'as_role': requested_as,
    })

# Login
def login_view(request):
    if request.session.get('user_id'):
        return redirect('index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email    = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'No account found with that email address.')
                return render(request, 'core/login.html', {'form': form})

            if not check_password(password, user.password):
                messages.error(request, 'Incorrect password. Please try again.')
                return render(request, 'core/login.html', {'form': form})

            # Credentials valid — create session
            request.session['user_id']   = user.user_id
            request.session['role']      = user.role
            request.session['user_name'] = user.name

            if user.role == 'patient' and request.session.get('pending_symptoms'):
                return redirect('patient_form')

            return redirect('patient_dashboard' if user.role == 'patient' else 'doctor_dashboard')

        return render(request, 'core/login.html', {'form': form})

    form = LoginForm()
    # pop one-time account-created message if present and pass to template
    acct_msg = request.session.pop('account_created_msg', None)
    return render(request, 'core/login.html', {'form': form, 'account_created_msg': acct_msg})

# Logout
def logout_view(request):
    request.session.flush()
    return redirect('landing')

# Admin auth — unchanged
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            admin = AdminUser.objects.get(username=username)
            if check_password(password, admin.password):
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

# Patient views
@never_cache
@patient_required
def patient_dashboard(request):
    user    = current_user(request)
    records = PatientRecord.objects.filter(patient=user).order_by('-created_at')
    reviewed = records.filter(is_reviewed=True).count()
    pending  = records.filter(is_reviewed=False).count()
    return render(request, 'core/patient_dashboard.html', {
        'user': user, 'records': records,
        'reviewed': reviewed, 'pending': pending,
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

# Basic validation
            if age <= 0 or weight <= 0:
                raise ValueError("Age and weight must be positive.")

# Adult weight validation
            if age >= 18:
                if weight < 30 or weight > 200:
                    raise ValueError(
                    "For adults (18 years and above), weight must be between 30 kg and 200 kg."
                    )

# Child weight validation
            else:
                if weight < 2 or weight > 100:
                    raise ValueError(
                    "For children, weight must be between 2 kg and 100 kg."
                    )
            is_pregnant = request.POST.get('is_pregnant') == 'on'
            if is_pregnant:
                if gender not in ("female", "other"):
                    messages.error(request, "Only females or non-binary/other patients can be marked as pregnant.")
                    return redirect('patient_form')
                if age < 13 or age > 55:
                    messages.error(request, "Pregnancy is only allowed for patiets aged 12 to 55 years.")
                    return redirect('patient_form')

            if not any(symptom in request.POST for symptom in SYMPTOM_FIELDS):
                messages.error(request, "Please select at least one symptom.")
                return redirect('patient_form')

            rec = PatientRecord(
                patient=user, age=age, weight=weight,
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
                abdominal_pain              = 'abdominal_pain' in request.POST,
            )
            rec.save()
            user.age         = age
            user.weight      = weight
            user.gender      = gender
            user.is_pregnant = is_pregnant
            user.save()
            for k in ('pending_symptoms', 'pending_score', 'pending_risk',
                      'pending_age', 'pending_gender', 'pending_pregnant'):
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
            'age':         request.session.get('pending_age') or user.age or '',
            'weight': request.POST.get('weight') or user.weight or '',
            'gender':      request.session.get('pending_gender') or user.gender or '',
            'is_pregnant': request.session.get('pending_pregnant', user.is_pregnant),
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
        form = PatientProfileForm(request.POST)

        if form.is_valid():

            age = form.cleaned_data.get('age')
            weight = form.cleaned_data.get('weight')
            gender = form.cleaned_data.get('gender') or ''
            is_pregnant = form.cleaned_data.get('is_pregnant', False)

            # Validate pregnancy
            if gender not in ("female", "other") or age < 13 or age > 55:
                is_pregnant = False

            user.age = age
            user.weight = weight
            user.gender = gender
            user.is_pregnant = is_pregnant

            user.save()

            messages.success(request, "Profile updated successfully.")
            return redirect('patient_dashboard')
        return render(request, 'core/patient_profile.html', {
            'user': user,
            'form': form,
        })

    form = PatientProfileForm(initial={
        'age': user.age,
        'weight': user.weight,
        'gender': user.gender,
        'is_pregnant': user.is_pregnant,
    })

    return render(request, 'core/patient_profile.html', {
        'user': user,
        'form': form,
    })

# Doctor views
@never_cache
@doctor_required
def doctor_dashboard(request):
    user    = current_user(request)
    records = PatientRecord.objects.select_related('patient', 'reviewed_by').order_by('-created_at')
    search  = request.GET.get('search', '').strip()
    status  = request.GET.get('status', '')

    if search:
        records = records.filter(
            patient__name__icontains=search
        ) | records.filter(
            patient__user_id__icontains=search
        )
        records = records.distinct()
    if status == 'reviewed':
        records = records.filter(is_reviewed=True)
    elif status == 'pending':
        records = records.filter(is_reviewed=False)

    return render(request, 'core/doctor_dashboard.html', {
        'user': user, 'records': records,
        'search': search, 'status_filter': status,
        'total'   : records.count(),
        'pending' : records.filter(is_reviewed=False).count(),
        'reviewed': records.filter(is_reviewed=True).count(),
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
            # Cap platelet count
            if platelet < 10000:
                platelet = 10000
            elif platelet > 1000000:
                platelet = 1000000

            # Cap WBC count
            if wbc < 1000:
                wbc = 1000
            elif wbc > 50000:
                wbc = 50000
                
            ns1 = 1 if request.POST.get('ns1_status') == 'positive' else 0
            igg = 1 if request.POST.get('igg_status') == 'positive' else 0
            igm = 1 if request.POST.get('igm_status') == 'positive' else 0

            rec.platelet_count = platelet
            rec.wbc_count      = wbc
            rec.ns1            = ns1
            rec.igg            = igg
            rec.igm            = igm
            rec.reviewed_by    = doctor
            rec.is_reviewed    = True

            ml_input = {
                'NS1'            : ns1,
                'IgG'            : igg,
                'IgM'            : igm,
                'Platelet_Count' : platelet,
                'WBC_Count'      : wbc,
            }
            ml_res = predict_dengue(ml_input)

# Use the trained Hybrid Naive Bayes model prediction
            rec.ml_prediction = ml_res['prediction']
            rec.ml_confidence = ml_res['confidence']

            dosage_rec = recommend_dosage(
                weight_kg=rec.weight,
                age=rec.age,
                risk_level=rec.clinical_risk_level,
                platelet_count=platelet,
                is_pregnant=rec.is_pregnant,
                ml_prediction=rec.ml_prediction,
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
            platelet_count=rec.platelet_count,
            is_pregnant=rec.is_pregnant,
            ml_prediction=rec.ml_prediction,
        )
    return render(request, 'core/doctor_prediction_result.html', {
        'record': rec, 'doctor': doctor, 'dosage': dosage_rec,
    })


# Admin views — unchanged
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
            u.delete()
            return JsonResponse({'ok': True})
        except User.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'User not found.'}, status=404)
    return JsonResponse({'ok': False}, status=405)


@never_cache
@admin_required
def admin_delete_record(request, record_id):
    if request.method == 'POST':
        try:
            r = PatientRecord.objects.get(record_id=record_id)
            r.delete()
            return JsonResponse({'ok': True})
        except PatientRecord.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Record not found.'}, status=404)
    return JsonResponse({'ok': False}, status=405)


@never_cache #django decorator
@admin_required
def admin_dataset_json(request):
    info = get_dataset_info()
    if info:
        return JsonResponse(info)
    return JsonResponse({'error': 'Model not trained yet.'}, status=404)

