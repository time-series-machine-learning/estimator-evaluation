"""Test the Cluster ensemble package."""
import numpy as np
import pytest
from aeon.datasets import load_arrow_head
from sklearn.metrics import rand_score

from tsml_eval.estimators.clustering.consensus import (
    CSPAFromFile,
    HGPAFromFile,
    MCLAFromFile,
    HBGFFromFile,
    NMFFromFile,
)
from tsml_eval.testing.testing_utils import _TEST_RESULTS_PATH

ENSEMBLE_METHODS = [
    CSPAFromFile,
    HGPAFromFile,
    MCLAFromFile,
    HBGFFromFile,
    NMFFromFile,
]


@pytest.mark.parametrize("ensemble_method", ENSEMBLE_METHODS)
def test_cluster_ensemble_package(ensemble_method):
    """Test SimpleVote from file with ArrowHead results."""
    X_train, y_train = load_arrow_head(split="train")
    X_test, y_test = load_arrow_head(split="test")

    file_paths = [
        _TEST_RESULTS_PATH + "/clustering/PAM-DTW/Predictions/ArrowHead/",
        _TEST_RESULTS_PATH + "/clustering/PAM-ERP/Predictions/ArrowHead/",
        _TEST_RESULTS_PATH + "/clustering/PAM-MSM/Predictions/ArrowHead/",
        ]

    model = ensemble_method(clusterers=file_paths, n_clusters=3, random_state=0)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    assert model.labels_.shape == (len(X_train),)
    assert isinstance(model.labels_, np.ndarray)
    assert rand_score(y_train, model.labels_) >= 0.6
    assert preds.shape == (len(X_test),)
    assert isinstance(preds, np.ndarray)
    assert rand_score(y_test, preds) >= 0.6
