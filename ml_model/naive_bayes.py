import math
import pickle
import os
import json
import numpy as np
class GaussianNaiveBayes:
   
    def __init__(self):
        self.classes = []
        self.class_priors = {}       # P(class)
        self.class_means = {}        # mean per feature per class
        self.class_variances = {}    # variance per feature per class
        self.feature_names = []

    def fit(self, X, y, feature_names=None):
        """
        Train the Naive Bayes model.
        X: list of lists or 2D array (n_samples x n_features)
        y: list of labels
        """
        X = np.array(X, dtype=float)
        y = np.array(y)

        self.classes = list(set(y))
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        n_samples = len(y)

        for cls in self.classes:
            # Get all rows belonging to this class
            X_cls = X[y == cls]

            # P(class) = count(class) / total
            self.class_priors[cls] = len(X_cls) / n_samples

            # Mean of each feature for this class
            self.class_means[cls] = np.mean(X_cls, axis=0)

            # Variance of each feature for this class (add small epsilon to avoid zero variance)
            self.class_variances[cls] = np.var(X_cls, axis=0) + 1e-9

        return self

    def _gaussian_probability(self, x, mean, variance):
        """
        Calculating Gaussian probability density.
        P(x | mean, variance) = (1 / sqrt(2*pi*var)) * exp(-(x-mean)^2 / (2*var))
        Usesing log to avoid numerical underflow.
        """
        log_prob = -0.5 * math.log(2 * math.pi * variance)
        log_prob -= ((x - mean) ** 2) / (2 * variance)
        return log_prob

    def _predict_single(self, x):
        """Predicting class and log-probabilities for a single sample."""
        x = np.array(x, dtype=float)
        log_posteriors = {}

        for cls in self.classes:
            # Start with log prior: log P(class)
            log_posterior = math.log(self.class_priors[cls])

            # Add log likelihoods: sum of log P(xi | class)
            for i in range(len(x)):
                mean = self.class_means[cls][i]
                variance = self.class_variances[cls][i]
                log_posterior += self._gaussian_probability(x[i], mean, variance)

            log_posteriors[cls] = log_posterior

        return log_posteriors

    def predict(self, X):
        """Predicting class labels for multiple samples."""
        X = np.array(X, dtype=float)
        predictions = []
        for x in X:
            log_posteriors = self._predict_single(x)
            predicted_class = max(log_posteriors, key=log_posteriors.get)
            predictions.append(predicted_class)
        return np.array(predictions)

    def predict_proba(self, X):
        """
        Predicting class probabilities using softmax over log-posteriors.
        Returns array of shape (n_samples, n_classes).
        """
        X = np.array(X, dtype=float)
        probabilities = []

        for x in X:
            log_posteriors = self._predict_single(x)

            # Convert log-posteriors to probabilities using softmax
            log_values = np.array([log_posteriors[cls] for cls in self.classes])
            # Subtract max for numerical stability
            log_values -= np.max(log_values)
            exp_values = np.exp(log_values)
            probs = exp_values / np.sum(exp_values)

            probabilities.append(probs)

        return np.array(probabilities)

    def predict_single_with_confidence(self, x):
        """
        Predicting a single sample and return (label, confidence_percent).
        """
        proba = self.predict_proba([x])[0]
        class_idx = np.argmax(proba)
        predicted_class = self.classes[class_idx]
        confidence = float(proba[class_idx]) * 100
        return predicted_class, confidence

    def get_model_info(self):
        """Return model metadata as a dict."""
        return {
            'classes': [str(c) for c in self.classes],
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'class_priors': {str(k): float(v) for k, v in self.class_priors.items()},
        }