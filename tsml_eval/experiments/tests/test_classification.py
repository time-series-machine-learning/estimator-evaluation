# -*- coding: utf-8 -*-
"""Tests for classification experiments."""

__author__ = ["MatthewMiddlehurst"]

import os

import pytest

from tsml_eval.experiments.classification_experiments import run_experiment
from tsml_eval.utils.tests.test_results_writing import _check_classification_file_format


@pytest.mark.parametrize(
    "classifier",
    ["DummyClassifier-tsml", "DummyClassifier-sktime", "DummyClassifier-sklearn"],
)
def test_run_classification_experiment(classifier):
    """Test classification experiments with test data and classifier."""
    result_path = (
        "./test_output/classification/"
        if os.getcwd().split("\\")[-1] != "tests"
        else "../../../test_output/classification/"
    )
    data_path = (
        "./tsml_eval/datasets/"
        if os.getcwd().split("\\")[-1] != "tests"
        else "../../datasets/"
    )
    dataset = "MinimalChinatown"

    args = [
        None,
        data_path,
        result_path,
        classifier,
        dataset,
        "0",
        "True",
        "False",
    ]
    run_experiment(args, overwrite=True)

    test_file = f"{result_path}{classifier}/Predictions/{dataset}/testResample0.csv"
    train_file = f"{result_path}{classifier}/Predictions/{dataset}/trainResample0.csv"

    assert os.path.exists(test_file) and os.path.exists(train_file)

    _check_classification_file_format(test_file)
    _check_classification_file_format(train_file)

    os.remove(test_file)
    os.remove(train_file)
