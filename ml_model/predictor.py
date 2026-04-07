"""
predictor.py  —  loads trained .pkl and predicts on new patient input.

Feature mapping (patient form -> CSV column used in training):
  fever              -> fever
  severe_headache    -> headache
  joint_back_pain    -> joint_pain
  nausea_vomiting    -> nausea
  skin_rash          -> rash
  vomiting_more_than_3 -> vomiting
  platelet_count     -> platelet_count
  wbc_count          -> wbc_count
  muscle_pain        -> 0 (not in patient form; default 0)
"""

import os, pickle, json
import numpy as np

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PKL  = os.path.join(BASE, 'naive_bayes_model.pkl')
SCALER_PKL = os.path.join(BASE, 'scaler.pkl')
FEAT_JSON  = os.path.join(BASE, 'feature_names.json')
INFO_JSON  = os.path.join(BASE, 'dataset_info.json')

# Canonical feature order (must match training)
FEATURES = ['fever', 'headache', 'joint_pain', 'muscle_pain',
            'rash', 'nausea', 'vomiting',
            'platelet_count', 'wbc_count']

_model = _scaler = None


def _load():
    global _model, _scaler
    if _model is None:
        if not os.path.exists(MODEL_PKL):
            raise FileNotFoundError(
                "Model not trained yet. Run:  python ml_model/train_model.py")
        with open(MODEL_PKL,  'rb') as f: _model  = pickle.load(f)
        with open(SCALER_PKL, 'rb') as f: _scaler = pickle.load(f)
    return _model, _scaler


def _build_vector(d):
    """
    Maping patient-form dict to the 9-feature vector used in training.
    """
    mapping = {
        'fever'        : float(d.get('fever', 0)),
        'headache'     : float(d.get('severe_headache', d.get('headache', 0))),
        'joint_pain'   : float(d.get('joint_back_pain', d.get('joint_pain', 0))),
        'muscle_pain'  : 0.0,
        'rash'         : float(d.get('skin_rash', d.get('rash', 0))),
        'nausea'       : float(d.get('nausea_vomiting', d.get('nausea', 0))),
        'vomiting'     : float(d.get('vomiting_more_than_3', d.get('vomiting', 0))),
        'platelet_count': float(d.get('platelet_count', 150000)),
        'wbc_count'    : float(d.get('wbc_count', 6000)),
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
        return {'prediction': readable, 'confidence': round(confidence, 2),
                'raw_label': label_str, 'error': None}
    except FileNotFoundError as e:
        return {'prediction': 'Pending (Model Not Trained)',
                'confidence': 0.0, 'raw_label': 'unknown', 'error': str(e)}
    except Exception as e:
        return {'prediction': 'Error', 'confidence': 0.0,
                'raw_label': 'error', 'error': str(e)}


def is_model_trained():
    return os.path.exists(MODEL_PKL) and os.path.exists(SCALER_PKL)


def get_dataset_info():
    if os.path.exists(INFO_JSON):
        with open(INFO_JSON) as f:
            return json.load(f)
    return None


def get_feature_names():
    return FEATURES