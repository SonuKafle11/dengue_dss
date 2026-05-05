import os, pickle, json
import numpy as np

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PKL  = os.path.join(BASE, 'naive_bayes_model.pkl')
SCALER_PKL = os.path.join(BASE, 'scaler.pkl')
FEAT_JSON  = os.path.join(BASE, 'feature_names.json')
INFO_JSON  = os.path.join(BASE, 'dataset_info.json')

FEATURES = [
    'fever',
    'severe_headache',
    'joint_back_pain',
    'nausea_vomiting',
    'skin_rash',
    'vomiting_more_than_3',
    'bleeding',
    'extreme_weakness',
    'urine_output_low',
    'fever_not_improving',
    'drop_in_fever_with_weakness',
    'cold_hands_feet',
    'restless_drowsy',
    'platelet_count',
    'wbc_count',
]

_model = _scaler = None


def _load():
    global _model, _scaler
    if _model is None:
        if not os.path.exists(MODEL_PKL):
            raise FileNotFoundError(
                "Model not trained yet. Run: python ml_model/train_model.py")
        with open(MODEL_PKL,  'rb') as f: _model  = pickle.load(f)
        with open(SCALER_PKL, 'rb') as f: _scaler = pickle.load(f)
    return _model, _scaler


def _build_vector(d):

    mapping = {
        'fever'                       : float(d.get('fever', 0)),
        'severe_headache'             : float(d.get('severe_headache', 0)),
        'joint_back_pain'             : float(d.get('joint_back_pain', 0)),
        'nausea_vomiting'             : float(d.get('nausea_vomiting', 0)),
        'skin_rash'                   : float(d.get('skin_rash', 0)),
        'vomiting_more_than_3'        : float(d.get('vomiting_more_than_3', 0)),
        'bleeding'                    : float(d.get('bleeding', 0)),
        'extreme_weakness'            : float(d.get('extreme_weakness', 0)),
        'urine_output_low'            : float(d.get('urine_output_low', 0)),
        'fever_not_improving'         : float(d.get('fever_not_improving', 0)),
        'drop_in_fever_with_weakness' : float(d.get('drop_in_fever_with_weakness', 0)),
        'cold_hands_feet'             : float(d.get('cold_hands_feet', 0)),
        'restless_drowsy'             : float(d.get('restless_drowsy', 0)),
        'platelet_count'              : float(d.get('platelet_count', 150000)),
        'wbc_count'                   : float(d.get('wbc_count', 6000)),
    }
    return [mapping[f] for f in FEATURES]


def predict_dengue(input_dict):

    try:
        model, scaler = _load()
        vec = _build_vector(input_dict)
        X   = np.array([vec])
        Xs  = scaler.transform(X)
        label, confidence = model.predict_single_with_confidence(Xs[0])
        label_str = str(label).strip()
        readable  = 'Dengue Present' if label_str == '1' else 'Not Present'
        return {
            'prediction': readable,
            'confidence': round(confidence, 2),
            'raw_label' : label_str,
            'error'     : None
        }
    except FileNotFoundError as e:
        return {
            'prediction': 'Pending (Model Not Trained)',
            'confidence': 0.0,
            'raw_label' : 'unknown',
            'error'     : str(e)
        }
    except Exception as e:
        return {
            'prediction': 'Error',
            'confidence': 0.0,
            'raw_label' : 'error',
            'error'     : str(e)
        }


def is_model_trained():
    return os.path.exists(MODEL_PKL) and os.path.exists(SCALER_PKL)


def get_dataset_info():
    if os.path.exists(INFO_JSON):
        with open(INFO_JSON) as f:
            return json.load(f)
    return None


def get_feature_names():
    return FEATURES
