"""
train_model.py  —  Dengue DSS Naive Bayes Trainer
---------------------------------------------------
Dataset columns:  fever, headache, joint_pain, muscle_pain, rash,
                  nausea, vomiting, platelet_count, wbc_count,
                  symptom_score, lab_probability, symptom_probability,
                  final_probability, dengue  (target)

Dropped (derived/computed — not raw patient inputs):
  symptom_score, lab_probability, symptom_probability, final_probability

Features used for training:
  fever, headache, joint_pain, muscle_pain, rash, nausea,
  vomiting, platelet_count, wbc_count

Only using sklearn used for: train_test_split, StandardScaler,
accuracy_score, classification_report.
"""

import os, sys, json, pickle, math
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml_model.naive_bayes import GaussianNaiveBayes

BASE      = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(BASE)
DATASET   = os.path.join(PROJ_ROOT, 'dataset', 'dengue_dataset.csv')
MODEL_PKL = os.path.join(BASE, 'naive_bayes_model.pkl')
SCALER_PKL= os.path.join(BASE, 'scaler.pkl')
INFO_JSON = os.path.join(BASE, 'dataset_info.json')
FEAT_JSON = os.path.join(BASE, 'feature_names.json')

# Columns to DROP (derived — would cause data leakage if kept)
DROP_COLS = {'symptom_score', 'lab_probability',
             'symptom_probability', 'final_probability'}
TARGET    = 'dengue'

# Final feature order (used at prediction time too)
FEATURES  = ['fever', 'headache', 'joint_pain', 'muscle_pain',
             'rash', 'nausea', 'vomiting',
             'platelet_count', 'wbc_count']


def load_csv(path):
    rows, header = [], []
    with open(path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            vals = [v.strip().strip('"') for v in line.strip().split(',')]
            if i == 0:
                header = vals
            elif vals and len(vals) == len(header):
                rows.append(vals)
    return header, rows


def remove_outliers_iqr(X, col_indices):
    """IQR outlier removal on specified continuous columns."""
    mask = np.ones(len(X), dtype=bool)
    info = {}
    for ci in col_indices:
        col = X[:, ci]
        q1, q3 = np.percentile(col, 25), np.percentile(col, 75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5*iqr, q3 + 1.5*iqr
        bad = np.sum((col < lo) | (col > hi))
        mask &= (col >= lo) & (col <= hi)
        if bad:
            info[FEATURES[ci]] = int(bad)
    return mask, info


def train():
    print("="*60)
    print("  DENGUE DSS  —  Naive Bayes Trainer")
    print("="*60)

    # ── 1. Load ──────────────────────────────────────────────────
    print(f"\n[1] Loading: {DATASET}")
    header, rows = load_csv(DATASET)
    print(f"    Rows={len(rows)}  Cols={len(header)}")
    print(f"    Header: {header}")

    # ── 2. Build arrays ──────────────────────────────────────────
    feat_idx  = [header.index(f) for f in FEATURES]
    tgt_idx   = header.index(TARGET)

    X_list, y_list = [], []
    bad = 0
    for row in rows:
        try:
            x = [float(row[i]) for i in feat_idx]
            y = int(float(row[tgt_idx]))
            X_list.append(x); y_list.append(y)
        except (ValueError, IndexError):
            bad += 1
    if bad:
        print(f"    Skipped {bad} unparseable rows")

    X = np.array(X_list, dtype=float)
    y = np.array(y_list, dtype=int)
    print(f"    Usable rows: {len(X)}")
    print(f"    Class distribution: 0={int(np.sum(y==0))}  1={int(np.sum(y==1))}")

    # ── 3. Drop derived cols — already excluded in FEATURES ──────
    print(f"\n[2] Dropped derived columns: {sorted(DROP_COLS)}")
    print(f"    Features used: {FEATURES}")

    # ── 4. Outlier removal (only on continuous cols) ─────────────
    print("\n[3] Removing outliers (IQR) on platelet_count, wbc_count ...")
    continuous_idx = [FEATURES.index('platelet_count'),
                      FEATURES.index('wbc_count')]
    mask, out_info = remove_outliers_iqr(X, continuous_idx)
    X, y = X[mask], y[mask]
    removed = int(np.sum(~mask))
    print(f"    Removed: {removed} rows  |  Remaining: {len(X)}")
    if out_info:
        print(f"    Per-column outliers: {out_info}")

    # ── 5. Train / Test split ────────────────────────────────────
    print("\n[4] Train/test split (80/20, stratified) ...")
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"    Train={len(X_tr)}  Test={len(X_te)}")

    # ── 6. StandardScaler ────────────────────────────────────────
    print("\n[5] Scaling features ...")
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)

    # ── 7. Train Naive Bayes  ────────────────────────
    print("\n[6] Training Gaussian Naive Bayes...")
    model = GaussianNaiveBayes()
    model.fit(X_tr_s, y_tr, feature_names=FEATURES)
    print(f"    Classes : {model.classes}")
    print(f"    Priors  : { {k: round(v,3) for k,v in model.class_priors.items()} }")

    # ── 8. Evaluate ──────────────────────────────────────────────
    print("\n[7] Evaluating ...")
    y_pred = model.predict(X_te_s)
    acc    = accuracy_score(y_te, y_pred)
    report = classification_report(y_te, y_pred,
                                   target_names=['No Dengue','Dengue'])
    print(f"    Accuracy : {acc*100:.2f}%")
    print("\n    Classification Report:")
    print(report)

    # ── 9. Save ──────────────────────────────────────────────────
    print("\n[8] Saving model & scaler ...")
    with open(MODEL_PKL,  'wb') as f: pickle.dump(model,  f)
    with open(SCALER_PKL, 'wb') as f: pickle.dump(scaler, f)
    with open(FEAT_JSON,  'w') as f: json.dump(FEATURES, f, indent=2)
    print(f"    Saved: {MODEL_PKL}")
    print(f"    Saved: {SCALER_PKL}")

    # ── 10. Dataset info JSON ────────────────────────────────────
    class_dist = {str(k): int(v)
                  for k,v in zip(*np.unique(y_list, return_counts=True))}
    info = {
        "dataset_file"      : "dengue_dataset.csv",
        "total_rows"        : len(rows),
        "usable_rows"       : len(X_list),
        "rows_after_outlier_removal": int(len(X)),
        "outliers_removed"  : removed,
        "outlier_per_column": out_info,
        "total_columns"     : len(header),
        "all_columns"       : header,
        "feature_columns"   : FEATURES,
        "dropped_columns"   : sorted(DROP_COLS),
        "target_column"     : TARGET,
        "class_distribution": class_dist,
        "model_accuracy_pct": round(acc*100, 2),
        "model_info"        : model.get_model_info(),
    }
    with open(INFO_JSON, 'w') as f:
        json.dump(info, f, indent=2)
    print(f"    Dataset info JSON saved: {INFO_JSON}")

    print("\n" + "="*60)
    print("  Training complete!")
    print("="*60)
    return True


if __name__ == '__main__':
    train()