import os, pickle, json
import numpy as np

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PKL  = os.path.join(BASE, 'naive_bayes_model.pkl')
SCALER_PKL = os.path.join(BASE, 'scaler.pkl')
FEAT_JSON  = os.path.join(BASE, 'feature_names.json')
INFO_JSON  = os.path.join(BASE, 'dataset_info.json')

FEATURES = [
    'NS1',
    'IgG',
    'IgM',
    'Platelet_Count',
    'WBC_Count',
]

_model = _scaler = None


def _load():
    global _model, _scaler
    if _model is None:
        if not os.path.exists(MODEL_PKL):
            raise FileNotFoundError(
                "Model not trained yet. Run: python ml_model/train_model.py")
        with open(MODEL_PKL, 'rb') as f:
            _model = pickle.load(f)
    return _model


def _build_vector(d):
    mapping = {
        'NS1'            : float(d.get('NS1', 0)),
        'IgG'            : float(d.get('IgG', 0)),
        'IgM'            : float(d.get('IgM', 0)),
        'Platelet_Count' : float(d.get('Platelet_Count', 150000)),
        'WBC_Count'      : float(d.get('WBC_Count', 6000)),
    }
    return [mapping[f] for f in FEATURES]

def predict_dengue(input_dict):
    try:
        model = _load()
        vec = _build_vector(input_dict)
        X = np.array([vec])
        label, confidence = model.predict_single_with_confidence(X[0])
        label_str = str(label).strip()
        readable  = 'Dengue' if label_str == '1' else 'NO Dengue'
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
    return os.path.exists(MODEL_PKL)


def get_dataset_info():
    if os.path.exists(INFO_JSON):
        with open(INFO_JSON) as f:
            return json.load(f)
    return None


def get_feature_names():
    return FEATURES
