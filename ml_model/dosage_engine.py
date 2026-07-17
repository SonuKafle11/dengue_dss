def get_paracetamol_dosage(weight_kg, age):
    """
    Paracetamol dosage based on standard weight-based dosing.

    Formula:
        15 mg/kg per dose
        Every 6 hours
        Maximum:
            - Children (<12 years): 60 mg/kg/day
            - Adults (>=12 years): 4000 mg/day
    """

    # Calculate dose (15 mg/kg)
    dose_mg = round(weight_kg * 15)

    # Maximum single dose
    if dose_mg > 1000:
        dose_mg = 1000

    # Choose practical tablet strength
    if dose_mg <= 125:
        dose_str = "120 mg (Syrup)"
    elif dose_mg <= 250:
        dose_str = "250 mg"
    elif dose_mg <= 500:
        dose_str = "500 mg"
    else:
        dose_str = "500-1000 mg (1 g) depending on feaver severity"

    frequency = "Every 6-8 hours"

    # Maximum daily dose
    if age < 12:
        max_daily = min(round(weight_kg * 60), 4000)
    else:
        max_daily = 2000

    return dose_str, frequency, max_daily

def holliday_segar(weight_kg):
    """
    Holliday-Segar method for maintenance fluid calculation.
    Daily (ml/day):  first 10kg x100, next 10kg x50, above 20kg x20
    Hourly (ml/hr):  4-2-1 rule
    """
    if weight_kg <= 10:
        daily  = weight_kg * 100
        hourly = weight_kg * 4
    elif weight_kg <= 20:
        daily  = 1000 + (weight_kg - 10) * 50
        hourly = 40   + (weight_kg - 10) * 2
    else:
        daily  = 1500 + (weight_kg - 20) * 20
        hourly = 60   + (weight_kg - 20) * 1
    return round(daily), round(hourly)

def get_fluid_intake(dosing_weight, age, risk_level):
    
    daily_ml, hourly_ml = holliday_segar(dosing_weight)

    if risk_level == 'high':
        return {
            'type': "IV Isotonic Fluid (Normal Saline / Ringer's Lactate)",
            'rate': f"{hourly_ml} ml/hr",
            'daily_target': f"{daily_ml} ml/day (~{round(daily_ml/1000, 1)} L)",
            'note': (
                'Requires hospitalization and IV access. '
                'Taper to maintenance once stable. Monitor urine output every 1-2 hours.'
            )
        }
    
    else:  # low
        return {
            'type': 'Oral fluids (water, coconut water, ORS)',
            'rate': f"{hourly_ml} ml/hr  (or {round(daily_ml/6)} ml every 4 hours)",
            'daily_target': f"{daily_ml} ml/day (~{round(daily_ml/1000, 1)} L)",
            'note': (
                'Holliday-Segar maintenance. Rest and stay well hydrated. '
                'Monitor for worsening symptoms.'
            )
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

    
def recommend_dosage(weight_kg, age, risk_level, platelet_count=None,
                     is_pregnant=False, ml_prediction=None):
 
    dosing_weight = weight_kg

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
        'dosing_weight': weight_kg,
        'actual_weight': weight_kg,
        
    }

    # Rule 1: Paracetamol dosage
    dose_str, frequency, max_daily = get_paracetamol_dosage(dosing_weight, age)
    recommendations['paracetamol'] = {
        'drug': 'Paracetamol (Acetaminophen)',
        'dose': dose_str,
        'frequency': frequency,
        'max_daily': f"{max_daily} mg/day maximum" if max_daily else "As directed by doctor",
        'note': 'Do NOT exceed maximum daily dose. Do not use for more than 3 days without medical review.'
    }

    
    # Rule 2: Fluids (use ACTUAL weight — Holliday-Segar is based on real body weight)
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
        
    
        
    elif risk_level == 'high':
        recommendations['general_advice'] = [
            'IMMEDIATE hospitalization required.',
            'ICU monitoring may be needed.',
            'IV fluid resuscitation to be started.',
            'CBC, liver enzymes, coagulation profile every 6-12 hours.',
            'Platelet transfusion if <10,000/uL.',
            'Strict monitoring of vital signs every 1-2 hours.',
        ]
        
   # Hospitalization depends on ML prediction
    if risk_level == "high":
        recommendations["hospitalization"] = True

    elif platelet_count < 50000:
        recommendations["hospitalization"] = True

    elif platelet_count <= 100000 and "Positive" in str(ml_prediction):
        recommendations["hospitalization"] = True

    elif risk_level == "probable" and "Positive" in str(ml_prediction):
        recommendations["hospitalization"] = True

    else:
        recommendations["hospitalization"] = False
    

    # Rule 6: ML prediction upgrade
    if ml_prediction == "Positive Dengue" and risk_level == "low":
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
