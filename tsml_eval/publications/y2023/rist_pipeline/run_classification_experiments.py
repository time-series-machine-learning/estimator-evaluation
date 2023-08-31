"""Experiment runner for RIST pipeline publication."""

__author__ = ["MatthewMiddlehurst"]

import os
import sys

os.environ["MKL_NUM_THREADS"] = "1"  # must be done before numpy import!!
os.environ["NUMEXPR_NUM_THREADS"] = "1"  # must be done before numpy import!!
os.environ["OMP_NUM_THREADS"] = "1"  # must be done before numpy import!!

from tsml_eval.experiments import load_and_run_classification_experiment
from tsml_eval.publications.y2023.rist_pipeline.set_rist_classifier import (
    _set_rist_classifier,
)
from tsml_eval.utils.experiments import _results_present, parse_args

classifiers = [
    "FreshPRINCE",
    "STC",
    "RDST",
    "R-STSF",
    "DrCIF",
    "ROCKET",
    "HC2",
    "RIST-ExtraT",
    "RIST-RF",
    "RIST-RidgeCV",
    "IntervalPipeline",
]


def _run_classification_experiment(args):
    if args is None or args.__len__() < 1:
        data_path = "../"
        results_path = "../"
        classifier_name = "RIST"
        dataset_name = "ItalyPowerDemand"
        resample_id = 0
        n_jobs = 1
        kwargs = None
        overwrite = False
    else:
        print("Input args = ", args)
        args = parse_args(args)
        data_path = args.data_path
        results_path = args.results_path
        classifier_name = args.estimator_name
        dataset_name = args.dataset_name
        resample_id = args.resample_id
        n_jobs = args.n_jobs
        kwargs = args.kwargs
        overwrite = args.overwrite

    # Skip if not overwrite and results already present
    # this is also checked in load_and_run, but doing a quick check here so can
    # print a message and make sure data is not loaded
    if not overwrite and _results_present(
        results_path,
        classifier_name,
        dataset_name,
        resample_id=resample_id,
        split="TEST",
    ):
        print("Ignoring, results already present")
    else:
        load_and_run_classification_experiment(
            data_path,
            results_path,
            dataset_name,
            _set_rist_classifier(
                classifier_name,
                random_state=resample_id,
                n_jobs=n_jobs,
                **kwargs,
            ),
            classifier_name=classifier_name,
            resample_id=resample_id,
            overwrite=overwrite,
        )


if __name__ == "__main__":
    """
    Example simple usage, with arguments input via script or hard coded for testing.
    """
    print("Running run_classification_experiments.py main")
    _run_classification_experiment(sys.argv[1:])
