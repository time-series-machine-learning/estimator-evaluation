# -*- coding: utf-8 -*-
"""Set regressor function."""
__author__ = ["TonyBagnall"]


def set_regressor(regressor, resample_id=None, train_file=False, n_jobs=1):
    """Construct a regressor, possibly seeded for reproducability.

    Basic way of creating the regressor to build using the default settings. This
    set up is to help with batch jobs for multiple problems to facilitate easy
    reproducibility for use with load_and_run_classification_experiment. You can pass a
    classifier object instead to run_classification_experiment.
    TODO: add threads, contract and checkpoint options

    Parameters
    ----------
    regressor : str
        String indicating which Regressor you want.
    resample_id : int or None, default=None
        Classifier random seed.
    train_file : bool, default=False
        Whether a train file is being produced.
    n_jobs: for threading

    Return
    ------
    regressor: A BaseRegressor.
        The regressor matching the input regressor name.
    """
    name = regressor.lower()
    if name == "cnn" or name == "cnnregressor":
        from sktime.regression.deep_learning.cnn import CNNRegressor

        return CNNRegressor(random_state=resample_id)
    elif name == "tapnet" or name == "tapnetregressor":
        from sktime.regression.deep_learning.tapnet import TapNetRegressor

        return TapNetRegressor(random_state=resample_id)
    elif name == "knn" or name == "kneighborstimeseriesregressor":
        from sktime.regression.distance_based import KNeighborsTimeSeriesRegressor

        return KNeighborsTimeSeriesRegressor(
            # random_state=resample_id,
            n_jobs=n_jobs,
        )
    elif name == "rocket" or name == "rocketregressor":
        from sktime.regression.kernel_based import RocketRegressor

        return RocketRegressor(
            random_state=resample_id,
            n_jobs=n_jobs,
        )
    elif name == "tsf" or name == "timeseriesforestregressor":
        from sktime.regression.interval_based import TimeSeriesForestRegressor

        return TimeSeriesForestRegressor(
            random_state=resample_id,
            n_jobs=n_jobs,
        )
    # Other
    elif name == "dummy" or name == "dummyregressor":
        # todo we need an actual dummy for this
        raise ValueError(f" Regressor {name} is not avaiable")
