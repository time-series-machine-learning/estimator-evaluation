"""Tests for performance metric functions."""

__author__ = ["MatthewMiddlehurst"]

import numpy as np

from tsml_eval.evaluation.metrics import clustering_accuracy


def test_clustering_accuracy():
    """Test clustering accuracy with random labels and clusters."""
    labels = np.random.randint(0, 3, 10)
    clusters = np.random.randint(0, 3, 10)
    cl_acc = clustering_accuracy(labels, clusters)

    assert isinstance(cl_acc, float)
    assert 0 <= cl_acc <= 1
