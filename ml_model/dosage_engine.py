"""
dosage_engine.py
----------------
If-Then rule-based is used in dosage recommendation system for dengue patients.
Based on standard dengue treatment protocol:
  - Paracetamol dosage by weight.
  - ORS fluid intake.
  - Platelet-count-based precautions.
  - Pregnancy warning is given if patient is pregnant.
  - General advice based on risk level.
  - Risk-level-based recommendations.
"""


def get_paracetamol_dosage(weight_kg, age):
    """
    Standard paracetamol dosage: 10-15 mg/kg every 4-6 hours, max 60 mg/kg/day.
    Returns dosage per dose and frequency.
    """
    dose_per_kg = 10  # mg/kg (conservative)
    dose_mg = weight_kg * dose_per_kg

    # Cap at 1000mg per dose for adults
    if age >= 18 and dose_mg > 1000:
        dose_mg = 1000

    # Cap at 250mg for children under 6
    if age < 6 and dose_mg > 250:
        dose_mg = 250

    # Frequency
    if age < 12:
        frequency = "every 6 hours"
        max_daily = weight_kg * 60
    else:
        frequency = "every 4-6 hours"
        max_daily = min(weight_kg * 60, 4000)

    return round(dose_mg), frequency, round(max_daily)


def get_fluid_intake(weight_kg, age, risk_level):
    """
    ORS / IV Fluid recommendation based on WHO dengue guidelines.
    """
    if risk_level == 'high':
        ml_per_hour = weight_kg * 7
        return {
            'type': 'IV Isotonic Fluid (Normal Saline / Ringer\'s Lactate)',
            'rate': f"{round(ml_per_hour)} ml/hour",
            'daily_target': f"{round(ml_per_hour * 24)} ml/day",
            'note': 'Requires hospitalization and IV access. Monitor urine output every 1-2 hours.'
        }
    elif risk_level == 'probable':
        oral_ml = weight_kg * 50
        return {
            'type': 'Oral Rehydration Solution (ORS) or IV if oral not tolerated',
            'rate': f"{round(oral_ml)} ml every 2-4 hours",
            'daily_target': f"{round(oral_ml * 6)} ml/day",
            'note': 'Switch to IV fluids if patient vomits repeatedly or oral intake drops.'
        }
    elif risk_level == 'possible':
        oral_ml = weight_kg * 60
        return {
            'type': 'Oral Rehydration Solution (ORS)',
            'rate': f"{round(oral_ml)} ml every 4-6 hours",
            'daily_target': f"{round(oral_ml * 4)} ml/day",
            'note': 'Maintain adequate oral hydration. Return if symptoms worsen.'
        }
    else:
        water_liters = max(2.0, round(weight_kg * 0.04, 1))
        return {
            'type': 'Oral fluids (water, coconut water, ORS)',
            'rate': f"{water_liters} liters/day minimum",
            'daily_target': f"{round(water_liters * 1000)} ml/day",
            'note': 'Rest and stay well hydrated. Monitor for worsening symptoms.'
        }


def get_platelet_based_advice(platelet_count):
    """
    Platelet count-based clinical decisions.
    Normal: 150,000 - 400,000 /uL
    """
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


def recommend_dosage(weight_kg, age, risk_level, platelet_count=None,
                     is_pregnant=False, ml_prediction=None):
    """
    Main dosage recommendation function.
    """
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
    }

    # Rule 1: Paracetamol
    dose_mg, frequency, max_daily = get_paracetamol_dosage(weight_kg, age)
    recommendations['paracetamol'] = {
        'drug': 'Paracetamol (Acetaminophen)',
        'dose': f"{dose_mg} mg",
        'frequency': frequency,
        'max_daily': f"{max_daily} mg/day maximum",
        'note': 'Do NOT exceed maximum daily dose. Do not use for more than 3 days without medical review.'
    }

    # Rule 2: Fluids
    recommendations['fluids'] = get_fluid_intake(weight_kg, age, risk_level)

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
    elif risk_level == 'probable':
        recommendations['general_advice'] = [
            'Hospital admission strongly recommended.',
            'Complete blood count (CBC) every 12-24 hours.',
            'Monitor vital signs every 4-6 hours.',
            'Strict bed rest and fall prevention.',
            'Fluid intake chart must be maintained.',
        ]
        recommendations['hospitalization'] = True
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

    return recommendations


def format_dosage_text(rec):
    """
    Convert recommendation dict to plain text for database storage.
    """
    lines = []
    lines.append(f"=== DOSAGE RECOMMENDATION (Risk: {rec['risk_level'].upper()}) ===\n")
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