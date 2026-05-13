# tests_unit/test_naive_bayes.py
import numpy as np
from ml_model.naive_bayes import GaussianNaiveBayes


def test_predict_separable_data():
    """On clearly separable data, predictions are correct."""
    X_train = [[1, 1], [2, 2], [100, 100], [101, 99]]
    y_train = [0, 0, 1, 1]
    model = GaussianNaiveBayes().fit(X_train, y_train)
    assert model.predict([[1.5, 1.5]])[0] == 0
    assert model.predict([[100, 100]])[0] == 1


def test_confidence_in_range():
    """Confidence percentage must be between 0 and 100."""
    model = GaussianNaiveBayes().fit([[1, 1], [10, 10]], [0, 1])
    _, conf = model.predict_single_with_confidence([5, 5])
    assert 0 <= conf <= 100