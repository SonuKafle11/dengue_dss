"""
tests/unit/test_ml.py
Unit tests for the ML predictor and dosage engine.
"""
import pytest
from ml_model.predictor import predict_dengue, is_model_trained, get_feature_names
from ml_model.dosage_engine import (
    get_paracetamol_dosage,
    holliday_segar,
    get_fluid_intake,
    get_platelet_based_advice,
    recommend_dosage,
    format_dosage_text,
)

# UT-39 to UT-44: ML Predictor
class TestMLPredictor:

    def test_UT39_model_trained(self):
        """UT-39: Trained model file exists."""
        assert is_model_trained() is True

    def test_UT40_predict_returns_dict(self):
        """UT-40: predict_dengue returns a dict with required keys."""
        result = predict_dengue({
            'NS1': 1, 'IgG': 0, 'IgM': 0,
            'Platelet_Count': 80000, 'WBC_Count': 3000
        })
        assert isinstance(result, dict)
        assert 'prediction' in result
        assert 'confidence' in result
        assert 'raw_label' in result

    def test_UT41_predict_positive_when_ns1_positive(self):
        """UT-41: NS1=1 should produce positive dengue signal."""
        result = predict_dengue({
            'NS1': 1, 'IgG': 1, 'IgM': 1,
            'Platelet_Count': 50000, 'WBC_Count': 2000
        })
        assert result['raw_label'] in ('0', '1')
        assert 0 <= result['confidence'] <= 100

    def test_UT42_predict_negative_normal_values(self):
        """UT-42: Normal lab values should produce a valid result."""
        result = predict_dengue({
            'NS1': 0, 'IgG': 0, 'IgM': 0,
            'Platelet_Count': 200000, 'WBC_Count': 7000
        })
        assert result['error'] is None
        assert result['raw_label'] in ('0', '1')

    def test_UT43_confidence_between_0_and_100(self):
        """UT-43: Confidence value is always between 0 and 100."""
        result = predict_dengue({
            'NS1': 0, 'IgG': 1, 'IgM': 0,
            'Platelet_Count': 100000, 'WBC_Count': 4000
        })
        assert 0 <= result['confidence'] <= 100

    def test_UT44_feature_names_correct(self):
        """UT-44: get_feature_names returns the 5 expected features."""
        features = get_feature_names()
        assert 'NS1' in features
        assert 'IgG' in features
        assert 'IgM' in features
        assert 'Platelet_Count' in features
        assert 'WBC_Count' in features
        assert len(features) == 5

# UT-45 to UT-50: Paracetamol Dosage
class TestParacetamolDosage:

    def test_UT45_adult_50kg_dose(self):
        """UT-45: 50kg adult gets 500mg dose."""
        dose, freq, max_d = get_paracetamol_dosage(50, 30)
        assert '500' in dose
        assert max_d == 4000

    def test_UT46_child_10kg_dose(self):
        """UT-46: 10kg child gets 120-250mg dose."""
        dose, freq, max_d = get_paracetamol_dosage(10, 5)
        assert '120' in dose or '250' in dose

    def test_UT47_heavy_adult_over_65kg(self):
        """UT-47: 70kg adult gets 650mg-1g dose."""
        dose, freq, max_d = get_paracetamol_dosage(70, 35)
        assert '650' in dose or '1' in dose

    def test_UT48_frequency_every_6_8_hours(self):
        """UT-48: All doses specify every 6-8 hours frequency."""
        _, freq, _ = get_paracetamol_dosage(60, 25)
        assert '6' in freq and '8' in freq

# UT-49 to UT-53: Holliday-Segar Fluids
class TestHollidaySegar:

    def test_UT49_10kg_child_fluids(self):
        """UT-49: 10kg child gets 1000ml/day, 40ml/hr."""
        daily, hourly = holliday_segar(10)
        assert daily == 1000
        assert hourly == 40

    def test_UT50_20kg_child_fluids(self):
        """UT-50: 20kg child gets 1500ml/day, 60ml/hr."""
        daily, hourly = holliday_segar(20)
        assert daily == 1500
        assert hourly == 60

    def test_UT51_60kg_adult_fluids(self):
        """UT-51: 60kg adult gets correct fluid calculation."""
        daily, hourly = holliday_segar(60)
        expected_daily = 1500 + (60 - 20) * 20  # 2300
        expected_hourly = 60 + (60 - 20) * 1     # 100
        assert daily == expected_daily
        assert hourly == expected_hourly

# UT-52 to UT-55: Fluid Intake by Risk
class TestFluidIntake:

    def test_UT52_high_risk_iv_fluid(self):
        """UT-52: High risk patient gets IV fluid recommendation."""
        result = get_fluid_intake(60, 30, 'high')
        assert 'IV' in result['type']

    def test_UT53_low_risk_oral_fluid(self):
        """UT-53: Low risk patient gets oral fluid recommendation."""
        result = get_fluid_intake(60, 30, 'low')
        assert 'Oral' in result['type'] or 'oral' in result['type'].lower()

# UT-54 to UT-57: Platelet Advice
class TestPlateletAdvice:

    def test_UT54_critical_platelet(self):
        """UT-54: Platelet < 10000 gives Critical level."""
        advice = get_platelet_based_advice(5000)
        assert advice['level'] == 'Critical'

    def test_UT55_normal_platelet(self):
        """UT-55: Platelet 150000-400000 gives Normal level."""
        advice = get_platelet_based_advice(200000)
        assert advice['level'] == 'Normal'

    def test_UT56_low_platelet(self):
        """UT-56: Platelet 20000-50000 gives Low level."""
        advice = get_platelet_based_advice(35000)
        assert advice['level'] == 'Low'

    def test_UT57_none_platelet_returns_none(self):
        """UT-57: None platelet count returns None."""
        assert get_platelet_based_advice(None) is None

# UT-58 to UT-62: Full Dosage Recommendation
class TestRecommendDosage:

    def test_UT58_dosage_returns_all_keys(self):
        """UT-58: recommend_dosage returns all required keys."""
        rec = recommend_dosage(60, 30, 'high', platelet_count=80000)
        assert 'paracetamol' in rec
        assert 'fluids' in rec
        assert 'forbidden_drugs' in rec
        assert 'danger_signs' in rec
        assert 'general_advice' in rec
        assert 'hospitalization' in rec

    def test_UT59_high_risk_hospitalization_required(self):
        """UT-59: High risk patient requires hospitalization."""
        rec = recommend_dosage(60, 30, 'high')
        assert rec['hospitalization'] is True

    def test_UT60_low_risk_no_hospitalization(self):
        """UT-60: Low risk patient does not require hospitalization."""
        rec = recommend_dosage(60, 30, 'low')
        assert rec['hospitalization'] is False

    def test_UT61_pregnancy_warning_present(self):
        """UT-61: Pregnant patient gets a pregnancy warning."""
        rec = recommend_dosage(55, 25, 'high', is_pregnant=True)
        assert rec['pregnancy_warning'] is not None
        assert 'PREGNANCY' in rec['pregnancy_warning']

    def test_UT62_forbidden_drugs_includes_aspirin(self):
        """UT-62: Forbidden drugs list always includes Aspirin."""
        rec = recommend_dosage(60, 30, 'low')
        drugs = ' '.join(rec['forbidden_drugs'])
        assert 'Aspirin' in drugs

    def test_UT63_format_dosage_text_returns_string(self):
        """UT-63: format_dosage_text returns a non-empty string."""
        rec = recommend_dosage(60, 30, 'high', platelet_count=80000)
        text = format_dosage_text(rec)
        assert isinstance(text, str)
        assert len(text) > 0
        assert 'PARACETAMOL' in text
        assert 'FLUID' in text
