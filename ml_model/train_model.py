import os
import sys
import json
import pickle
import time
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml_model.naive_bayes import GaussianNaiveBayes

BASE         = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE)

dataset_path  = os.path.join(PROJECT_ROOT, 'dataset', 'dengue_dataset.csv')
model_path    = os.path.join(BASE, 'naive_bayes_model.pkl')
scaler_path   = os.path.join(BASE, 'scaler.pkl')
info_path     = os.path.join(BASE, 'dataset_info.json')
features_path = os.path.join(BASE, 'feature_names.json')

target_column = 'dengue'

# drop derived columns — they would cause data leakage
columns_to_drop = [
    'symptom_score',
    'lab_probability',
    'symptom_probability',
    'final_probability',
]

# 13 patient form symptoms + 2 lab values = 15 features
# LEFT SIDE  — symptoms patient selects on form
# RIGHT SIDE — lab values doctor enters
feature_list = [
    # patient form symptoms — exact same names as patient form
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

def read_csv_file(filepath):
    all_rows = []
    header = []
    with open(filepath, encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            values = [v.strip().strip('"') for v in line.strip().split(',')]
            if line_num == 0:
                header = values
            else:
                if values and len(values) == len(header):
                    all_rows.append(values)
    return header, all_rows


def remove_outliers(X, column_indices):
    # IQR method on continuous columns only
    keep = np.ones(len(X), dtype=bool)
    outlier_info = {}
    for col_idx in column_indices:
        column_data = X[:, col_idx]
        q1 = np.percentile(column_data, 25)
        q3 = np.percentile(column_data, 75)
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        num_outliers = np.sum(
            (column_data < lower_fence) | (column_data > upper_fence)
        )
        keep = keep & (column_data >= lower_fence) & (column_data <= upper_fence)
        if num_outliers > 0:
            outlier_info[feature_list[col_idx]] = int(num_outliers)
    return keep, outlier_info


def train():

    total_start = time.time()

    print("=" * 60)
    print("  Dengue DSS - Training Naive Bayes Model")
    print("=" * 60)

    print(f"\n[1] Loading dataset from: {dataset_path}")
    header, rows = read_csv_file(dataset_path)
    print(f"    Rows loaded  : {len(rows)}")
    print(f"    Columns      : {len(header)}")
    print(f"    Header       : {header}")

    print("\n[2] Building feature matrix and target array...")
    feature_indices = [header.index(f) for f in feature_list]
    target_index    = header.index(target_column)

    X_data = []
    y_data = []
    skipped = 0

    for row in rows:
        try:
            x_row = [float(row[i]) for i in feature_indices]
            y_val = int(float(row[target_index]))
            X_data.append(x_row)
            y_data.append(y_val)
        except (ValueError, IndexError):
            skipped += 1

    if skipped > 0:
        print(f"    Skipped {skipped} rows with invalid data")

    X = np.array(X_data, dtype=float)
    y = np.array(y_data, dtype=int)

    num_no_dengue = int(np.sum(y == 0))
    num_dengue    = int(np.sum(y == 1))

    print(f"    Usable rows  : {len(X)}")
    print(f"    No Dengue(0) : {num_no_dengue} ({num_no_dengue/len(y)*100:.1f}%)")
    print(f"    Dengue(1)    : {num_dengue} ({num_dengue/len(y)*100:.1f}%)")

    print("\n[3] Dropping derived columns to prevent data leakage...")
    print(f"    Dropped : {columns_to_drop}")
    print(f"    Using   : {len(feature_list)} features (13 symptoms + platelet + WBC)")

    print("\n[4] Removing outliers using IQR method...")
    platelet_idx = feature_list.index('platelet_count')
    wbc_idx      = feature_list.index('wbc_count')

    keep_mask, outlier_counts = remove_outliers(X, [platelet_idx, wbc_idx])
    X = X[keep_mask]
    y = y[keep_mask]
    rows_removed = int(np.sum(~keep_mask))

    print(f"    Rows removed    : {rows_removed}")
    print(f"    Rows remaining  : {len(X)}")
    if outlier_counts:
        print(f"    Outliers found  : {outlier_counts}")
    else:
        print(f"    No outliers found - dataset was already clean")

    print("\n[5] Splitting into train/test sets (80/20)...")
    x_train, x_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    print(f"    Training set : {len(x_train)} rows")
    print(f"    Testing set  : {len(x_test)} rows")

    print("\n[6] Scaling features using StandardScaler...")
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled  = scaler.transform(x_test)
    print(f"    Scaling done (fit on train only)")

    print("\n[7] Training Gaussian Naive Bayes...")
    model = GaussianNaiveBayes()
    model.fit(x_train_scaled, y_train, feature_names=feature_list)
    print(f"    Classes : {model.classes}")
    print(f"    Priors  : { {k: round(v, 3) for k, v in model.class_priors.items()} }")

    print("\n[8] Evaluating model on test set...")
    y_predicted = model.predict(x_test_scaled)
    accuracy    = accuracy_score(y_test, y_predicted)
    report      = classification_report(
        y_test, y_predicted,
        target_names=['No Dengue', 'Dengue']
    )
    print(f"    Accuracy : {accuracy * 100:.2f}%")
    print(f"\n    Classification Report:")
    print(report)
    print(f"    Note: dengue recall lower due to class imbalance - known limitation")

    print("\n[9] Saving model and scaler...")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    with open(features_path, 'w') as f:
        json.dump(feature_list, f, indent=2)
    print(f"    Saved: naive_bayes_model.pkl")
    print(f"    Saved: scaler.pkl")
    print(f"    Saved: feature_names.json")

    total_time = time.time() - total_start
    class_distribution = {
        str(k): int(v)
        for k, v in zip(*np.unique(y_data, return_counts=True))
    }
    dataset_info = {
        "dataset_file"               : "dengue_dataset.csv",
        "total_rows"                 : len(rows),
        "usable_rows"                : len(X_data),
        "rows_after_outlier_removal" : int(len(X)),
        "outliers_removed"           : rows_removed,
        "outlier_per_column"         : outlier_counts,
        "total_columns"              : len(header),
        "all_columns"                : header,
        "feature_columns"            : feature_list,
        "dropped_columns"            : columns_to_drop,
        "target_column"              : target_column,
        "class_distribution"         : class_distribution,
        "model_accuracy_pct"         : round(accuracy * 100, 2),
        "model_info"                 : model.get_model_info(),
    }
    with open(info_path, 'w') as f:
        json.dump(dataset_info, f, indent=2)
    print(f"    Saved: dataset_info.json")

    print("\n ------------------------------------------")
    print("  Training complete!")
    print(f"\n  Accuracy         : {accuracy * 100:.2f}%")
    print(f"  Total time taken : {total_time:.2f} seconds")

    return True


if __name__ == '__main__':
    train()
