import math
import pickle
import os
import json
import numpy as np


class HybridNaiveBayes:
    """
    Naive Bayes that models each feature with the distribution that actually
    fits it:
      - Binary lab markers (NS1, IgG, IgM: values 0 or 1)  -> Bernoulli
      - Continuous lab values (Platelet_Count, WBC_Count)  -> Gaussian

    A pure GaussianNaiveBayes forces binary 0/1 features through a
    mean/variance model that doesn't represent them well, which can dilute
    genuinely strong signals (e.g. NS1 positivity correlating with Outcome
    in ~83% of cases in training data). Bernoulli directly models
    P(feature=1 | class), which is the correct distribution for binary data.
    """

    def __init__(self, binary_features=None):
        self.binary_features = binary_features or []

        self.classes = []
        self.class_priors = {}
        self.feature_names = []

        self.class_means = {}
        self.class_variances = {}
        self.class_bernoulli_p = {}

    def fit(self, X, y, feature_names=None):
        X = np.array(X, dtype=float)
        y = np.array(y)

        self.classes = list(set(y))
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        n_samples = len(y)

        for cls in self.classes:
            X_cls = X[y == cls]
            self.class_priors[cls] = len(X_cls) / n_samples

            self.class_means[cls] = {}
            self.class_variances[cls] = {}
            self.class_bernoulli_p[cls] = {}

            for i, fname in enumerate(self.feature_names):
                col = X_cls[:, i]
                if fname in self.binary_features:
                    p = (np.sum(col == 1) + 1) / (len(col) + 2)
                    self.class_bernoulli_p[cls][fname] = p
                else:
                    self.class_means[cls][fname] = np.mean(col)
                    self.class_variances[cls][fname] = np.var(col) + 1e-9

        return self

    def _gaussian_log_prob(self, x, mean, variance):
        log_prob = -0.5 * math.log(2 * math.pi * variance)
        log_prob -= ((x - mean) ** 2) / (2 * variance)
        return log_prob

    def _bernoulli_log_prob(self, x, p):
        p = min(max(p, 1e-9), 1 - 1e-9)
        return x * math.log(p) + (1 - x) * math.log(1 - p)

    def _predict_single(self, x):
        x = np.array(x, dtype=float)
        log_posteriors = {}

        for cls in self.classes:
            log_posterior = math.log(self.class_priors[cls])

            for i, fname in enumerate(self.feature_names):
                if fname in self.binary_features:
                    p = self.class_bernoulli_p[cls][fname]
                    log_posterior += self._bernoulli_log_prob(x[i], p)
                else:
                    mean = self.class_means[cls][fname]
                    variance = self.class_variances[cls][fname]
                    log_posterior += self._gaussian_log_prob(x[i], mean, variance)

            log_posteriors[cls] = log_posterior

        return log_posteriors

    def predict(self, X):
        X = np.array(X, dtype=float)
        predictions = []
        for x in X:
            log_posteriors = self._predict_single(x)
            predicted_class = max(log_posteriors, key=log_posteriors.get)
            predictions.append(predicted_class)
        return np.array(predictions)

    def predict_proba(self, X):
        X = np.array(X, dtype=float)
        probabilities = []

        for x in X:
            log_posteriors = self._predict_single(x)
            log_values = np.array([log_posteriors[cls] for cls in self.classes])
            log_values -= np.max(log_values)
            exp_values = np.exp(log_values)
            probs = exp_values / np.sum(exp_values)
            probabilities.append(probs)

        return np.array(probabilities)

    def predict_single_with_confidence(self, x):
        proba = self.predict_proba([x])[0]
        class_idx = np.argmax(proba)
        predicted_class = self.classes[class_idx]
        confidence = float(proba[class_idx]) * 100
        return predicted_class, confidence

    def get_model_info(self):
        return {
            'classes': [str(c) for c in self.classes],
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'binary_features': self.binary_features,
            'class_priors': {str(k): float(v) for k, v in self.class_priors.items()},
        }