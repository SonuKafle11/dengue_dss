"""
Dosage engine for the Dengue DSS.

Dosage is calculated based on BMI (Body Mass Index) instead of raw body weight.
    BMI = weight(kg) / height(cm)^2 * 10000

A "dosing weight" is derived from BMI so that under/overweight patients are not
under- or over-dosed when only raw weight is used. The dosing weight is the
patient's actual weight adjusted toward a normal-BMI weight when their BMI
falls outside the healthy range (18.5 - 24.9).
"""

# Healthy BMI range used as the reference for dosing
BMI_HEALTHY_LOW  = 18.5
BMI_HEALTHY_HIGH = 24.9
# Mid-range BMI used as the target for adjusted dosing weight
BMI_TARGET       = 22.0


def calculate_bmi(weight_kg, height_cm):
    """BMI = weight(kg) / height(cm)^2 * 10000. Returns 0 if height invalid."""
    try:
        if height_cm and height_cm > 0:
            return round((weight_kg / (height_cm * height_cm)) * 10000, 2)
    except (TypeError, ZeroDivisionError):
        pass
    return 0


def get_bmi_category(bmi):
    """Return human-readable BMI category."""
    if bmi <= 0:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def get_dosing_weight(weight_kg, height_cm):
    """
    Return the BMI-adjusted weight that should be used for dosing.

    - If BMI is within the healthy range (18.5 - 24.9), use actual weight.
    - If BMI is below 18.5 (underweight), use a weight calculated from
      BMI 18.5 at the patient's height (so they aren't under-dosed).
    - If BMI is above 24.9 (overweight/obese), use a weight calculated from
      BMI 24.9 at the patient's height (so they aren't over-dosed).
    - If height is missing/invalid, fall back to raw weight.
    """
    if not height_cm or height_cm <= 0:
        return weight_kg

    bmi = calculate_bmi(weight_kg, height_cm)
    height_m_sq = (height_cm / 100.0) ** 2

    if bmi < BMI_HEALTHY_LOW:
        return round(BMI_HEALTHY_LOW * height_m_sq, 2)
    if bmi > BMI_HEALTHY_HIGH:
        return round(BMI_HEALTHY_HIGH * height_m_sq, 2)
    return weight_kg


def get_paracetamol_dosage(dosing_weight, age):
    """
    Standard paracetamol dosage: 10-15 mg/kg every 4-6 hours, max 60 mg/kg/day.
    Uses BMI-adjusted dosing weight rather than raw body weight.
    """
    dose_per_kg = 10  # mg/kg
    dose_mg = dosing_weight * dose_per_kg

    # Cap at 1000mg per dose for adults
    if age >= 18 and dose_mg > 1000:
        dose_mg = 1000

    # Cap at 250mg for children under 6
    if age < 6 and dose_mg > 250:
        dose_mg = 250

    if age < 12:
        frequency = "every 6 hours"
        max_daily = dosing_weight * 60
    else:
        frequency = "every 4-6 hours"
        max_daily = min(dosing_weight * 60, 4000)

    return round(dose_mg), frequency, round(max_daily)


def get_fluid_intake(dosing_weight, age, risk_level):
    """ORS / IV Fluid recommendation, BMI-adjusted."""
    if risk_level == 'high':
        ml_per_hour = dosing_weight * 7
        return {
            'type': 'IV Isotonic Fluid (Normal Saline / Ringer\'s Lactate)',
            'rate': f"{round(ml_per_hour)} ml/hour",
            'daily_target': f"{round(ml_per_hour * 24)} ml/day",
            'note': 'Requires hospitalization and IV access. Monitor urine output every 1-2 hours.'
        }
    elif risk_level == 'possible':
        oral_ml = dosing_weight * 60
        return {
            'type': 'Oral Rehydration Solution (ORS)',
            'rate': f"{round(oral_ml)} ml every 4-6 hours",
            'daily_target': f"{round(oral_ml * 4)} ml/day",
            'note': 'Maintain adequate oral hydration. Return if symptoms worsen.'
        }
    else:  # 'low'
        water_liters = max(2.0, round(dosing_weight * 0.04, 1))
        return {
            'type': 'Oral fluids (water, coconut water, ORS)',
            'rate': f"{water_liters} liters/day minimum",
            'daily_target': f"{round(water_liters * 1000)} ml/day",
            'note': 'Rest and stay well hydrated. Monitor for worsening symptoms.'
        }


def get_platelet_based_advice(platelet_count):
    """Platelet count-based clinical decisions. Normal: 150,000 - 400,000 /uL."""
    if platelet_count is None:
        return None

    if platelet_count < 10000:
        return {'level': 'Critical',
                'advice': 'Immediate platelet transfusion required. Hospitalize urgently.',
                'color': 'red'}
    elif platelet_count < 20000:
        return {'level': 'Very Low',
                'advice': 'Platelet transfusion may be needed. Strict bed rest. Avoid all NSAIDs.',
                'color': 'red'}
    elif platelet_count < 50000:
        return {'level': 'Low',
                'advice': 'Monitor closely every 12 hours. Avoid invasive procedures.',
                'color': 'orange'}
    elif platelet_count < 100000:
        return {'level': 'Borderline Low',
                'advice': 'Monitor daily. Restrict physical activity.',
                'color': 'yellow'}
    elif platelet_count <= 400000:
        return {'level': 'Normal',
                'advice': 'Platelet count within normal range.',
                'color': 'green'}
    else:
        return {'level': 'High',
                'advice': 'Elevated platelet count. Monitor for thrombotic events.',
                'color': 'yellow'}


def recommend_dosage(weight_kg, age, risk_level, height_cm=0, platelet_count=None,
                     is_pregnant=False, ml_prediction=None):
    """
    Main dosage recommendation function. Now uses BMI-based dosing.

    Args:
        weight_kg: actual patient weight in kg
        age: patient age in years
        risk_level: 'low', 'possible', or 'high'
        height_cm: patient height in cm (used for BMI calculation)
        platelet_count: platelet count in /uL (optional)
        is_pregnant: bool
        ml_prediction: ML prediction string (optional)
    """
    bmi = calculate_bmi(weight_kg, height_cm)
    bmi_category = get_bmi_category(bmi)
    dosing_weight = get_dosing_weight(weight_kg, height_cm)

    recommendations = {
        'paracetamol': {},
        'fluids': {},
        'platelet_advice': None,
        'general_advice': [],
        'pregnancy_warning': None,
        'danger_signs': [],
        'forbidden_drugs': [],
        'hospitalization': False,
        'risk_level': risk_level,
        'bmi': bmi,
        'bmi_category': bmi_category,
        'dosing_weight': dosing_weight,
        'actual_weight': weight_kg,
        'height_cm': height_cm,
    }

    # Rule 1: Paracetamol (BMI-adjusted)
    dose_mg, frequency, max_daily = get_paracetamol_dosage(dosing_weight, age)
    recommendations['paracetamol'] = {
        'drug': 'Paracetamol (Acetaminophen)',
        'dose': f"{dose_mg} mg",
        'frequency': frequency,
        'max_daily': f"{max_daily} mg/day maximum",
        'note': 'Do NOT exceed maximum daily dose. Do not use for more than 3 days without medical review.'
    }

    # Rule 2: Fluids (BMI-adjusted)
    recommendations['fluids'] = get_fluid_intake(dosing_weight, age, risk_level)

    # Rule 3: Platelet-based advice
    if platelet_count is not None:
        recommendations['platelet_advice'] = get_platelet_based_advice(platelet_count)

    # Rule 4: Forbidden drugs
    recommendations['forbidden_drugs'] = [
        'Aspirin (Acetylsalicylic Acid) — increases bleeding risk',
        'Ibuprofen / Brufen — increases bleeding risk',
        'Naproxen — increases bleeding risk',
        'Diclofenac — increases bleeding risk',
        'All NSAIDs are CONTRAINDICATED in dengue',
    ]

    # Rule 5: Risk-level-specific general advice
    if risk_level == 'low':
        recommendations['general_advice'] = [
            'Rest adequately at home.',
            'Monitor temperature every 4-6 hours.',
            'Return to clinic if symptoms worsen.',
            'Avoid strenuous physical activity.',
        ]
        recommendations['hospitalization'] = False
    elif risk_level == 'possible':
        recommendations['general_advice'] = [
            'Closely monitor for warning signs.',
            'Complete bed rest recommended.',
            'Visit nearest clinic every 24-48 hours.',
            'Measure urine output — should be >= 0.5 ml/kg/hour.',
            'Avoid mosquito bites to prevent spread.',
        ]
        recommendations['hospitalization'] = False
    elif risk_level == 'high':
        recommendations['general_advice'] = [
            'IMMEDIATE hospitalization required.',
            'ICU monitoring may be needed.',
            'IV fluid resuscitation to be started.',
            'CBC, liver enzymes, coagulation profile every 6-12 hours.',
            'Platelet transfusion if <10,000/uL.',
            'Strict monitoring of vital signs every 1-2 hours.',
        ]
        recommendations['hospitalization'] = True

    # Rule 6: ML prediction upgrade
    if ml_prediction == 'Dengue Present' and risk_level in ['low', 'possible']:
        recommendations['general_advice'].append(
            'ML model predicts Dengue Positive — clinical upgrade recommended. '
            'Consider admission even if score appears low.'
        )

    # Rule 7: Danger signs
    recommendations['danger_signs'] = [
        'Severe abdominal pain or tenderness',
        'Persistent vomiting (>3 times)',
        'Bleeding from nose, gums, or in vomit/stool',
        'Rapid breathing or difficulty breathing',
        'Fatigue, restlessness, or mental confusion',
        'Cold/clammy skin or pale appearance',
        'Decreased urine output for 4-6 hours',
        'Sudden drop in fever with worsening condition',
    ]

    # Rule 8: Pregnancy warning
    if is_pregnant:
        recommendations['pregnancy_warning'] = (
            'PREGNANCY WARNING: This patient is pregnant. '
            'Paracetamol is safe when used at the recommended dose. '
            'Avoid all NSAIDs (especially in 3rd trimester). '
            'Increased risk of preterm delivery and neonatal dengue — '
            'immediate obstetric consultation required if dengue is confirmed. '
            'Monitor fetal heart rate if hospitalized.'
        )

    # Rule 9: Pediatric adjustments
    if age < 12:
        recommendations['general_advice'].append(
            f'Pediatric patient (age {age:.0f}): Use weight-based dosing strictly. '
            'Consult pediatrician if unsure.'
        )

    # Rule 10: Elderly adjustments
    if age >= 60:
        recommendations['general_advice'].append(
            'Elderly patient: Higher risk of severe dengue. '
            'Lower threshold for hospitalization. Monitor renal function.'
        )

    # Rule 11: BMI-based note
    if bmi > 0:
        if bmi_category == 'Underweight':
            recommendations['general_advice'].append(
                f'BMI {bmi} ({bmi_category}): Dosing adjusted upward toward healthy-BMI weight '
                'to avoid sub-therapeutic dosing.'
            )
        elif bmi_category in ('Overweight', 'Obese'):
            recommendations['general_advice'].append(
                f'BMI {bmi} ({bmi_category}): Dosing capped at healthy-BMI weight '
                'to avoid risk of overdose.'
            )

    return recommendations


def format_dosage_text(rec):
    lines = []
    lines.append(f"=== DOSAGE RECOMMENDATION (Risk: {rec['risk_level'].upper()}) ===\n")

    # BMI summary
    if rec.get('bmi'):
        lines.append(
            f"PATIENT BMI: {rec['bmi']} ({rec['bmi_category']})  |  "
            f"Actual weight: {rec['actual_weight']} kg  |  "
            f"Height: {rec['height_cm']} cm  |  "
            f"Dosing weight used: {rec['dosing_weight']} kg\n"
        )

    p = rec['paracetamol']
    lines.append(f"PARACETAMOL:")
    lines.append(f"  Dose: {p['dose']} {p['frequency']}")
    lines.append(f"  Maximum: {p['max_daily']}")
    lines.append(f"  Note: {p['note']}\n")
    fl = rec['fluids']
    lines.append(f"FLUID INTAKE:")
    lines.append(f"  Type: {fl['type']}")
    lines.append(f"  Rate: {fl['rate']}")
    lines.append(f"  Daily Target: {fl['daily_target']}")
    lines.append(f"  Note: {fl['note']}\n")
    if rec.get('platelet_advice'):
        pa = rec['platelet_advice']
        lines.append(f"PLATELET STATUS: {pa['level']}")
        lines.append(f"  {pa['advice']}\n")
    lines.append("CONTRAINDICATED DRUGS:")
    for drug in rec['forbidden_drugs']:
        lines.append(f"  X {drug}")
    lines.append("")
    lines.append(f"HOSPITALIZATION: {'Required' if rec['hospitalization'] else 'Not required (monitor closely)'}\n")
    if rec.get('pregnancy_warning'):
        lines.append(rec['pregnancy_warning'] + "\n")
    lines.append("GENERAL ADVICE:")
    for adv in rec['general_advice']:
        lines.append(f"  * {adv}")
    return "\n".join(lines)
