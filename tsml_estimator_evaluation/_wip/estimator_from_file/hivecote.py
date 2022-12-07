# -*- coding: utf-8 -*-
"""Hierarchical Vote Collective of Transformation-based Ensembles (HIVE-COTE) from file.

Upgraded hybrid ensemble of classifiers from 4 separate time series classification
representations, using the weighted probabilistic CAWPE as an ensemble controller.
This version loads the ensembles predictions from file and allows to change the alfa value.
"""

__author__ = ["MatthewMiddlehurst", "ander-hg"]
__all__ = ["FromFileHIVECOTE"]

import numpy as np
from sklearn.utils import check_random_state
from sktime.classification import BaseClassifier


class FromFileHIVECOTE(BaseClassifier):
    """Hierarchical Vote Collective of Transformation-based Ensembles (HIVE-COTE) from file.
    An ensemble of the STC, DrCIF, Arsenal and TDE classifiers from different feature
    representations using the CAWPE structure as described in [1].

    Parameters
    ----------
    file_paths : list
        The paths for Arsenal, DrCIF, STC and TDE files.
    alpha : int
        The exponent to extenuate diferences in classifers and weighting with the accuracy estimate.
    random_state : int or None, default=None
        Seed for random number generation.

    Attributes
    ----------
    _weights : list
        The weight for Arsenal, DrCIF, STC and TDE probabilities.

    References
    ----------
    .. [1] Middlehurst, Matthew, James Large, Michael Flynn, Jason Lines, Aaron Bostrom,
       and Anthony Bagnall. "HIVE-COTE 2.0: a new meta ensemble for time series
       classification." Machine Learning (2021).
    """

    _tags = {
        "capability:multivariate": True,
        "classifier_type": "hybrid",
    }

    def __init__(
        self,
        file_paths,
        alpha=4,
        random_state=None,
    ):
        self.file_paths = file_paths
        self.alpha = alpha
        self.random_state = random_state

        self._weights = []

        super(FromFileHIVECOTE, self).__init__()

    def _fit(self, X, y):
        """Load HIVE-COTE accuracies from the training file.

        Parameters
        ----------
        X : 3D np.array of shape = [n_instances, n_dimensions, series_length]
            The training data.
        y : array-like, shape = [n_instances]
            The class labels.

        Returns
        -------
        self :
            Reference to self.

        Notes
        -----
        Updates the attribute _weights with the loaded from file accuracies to the power of alfa.
        """

        self._weights = []

        #   load train file at path (trainResample.csv if random_state is None, trainResample0.csv otherwise)
        file_name = 'trainResample.csv'
        if self.random_state != None:
            file_name = 'trainResample' + str(self.random_state) + '.csv'

        acc_list = []
        for path in self.file_paths:
            f = open(path + file_name, "r")
            lines = f.readlines()
            line2 = lines[2].split(",")

            #   verify file matches data, i.e. n_instances and n_classes
            if len(lines)-3 != len(X): # verify n_instances
                print("ERROR n_instances does not match in: ", path + file_name)
            if len(np.unique(y)) != int(line2[5]): # verify n_classes
                print("ERROR n_classes does not match in: ", path + file_name, len(np.unique(y)), line2[5])

            acc_list.append(float(line2[0]))

        #   add a weight to the weight list based on the files accuracy
        for acc in acc_list:
            self._weights.append(acc ** self.alpha)

    def _predict(self, X):
        rng = check_random_state(self.random_state)
        return np.array(
            [
                self.classes_[int(rng.choice(np.flatnonzero(prob == prob.max())))]
                for prob in self.predict_proba(X)
            ]
        )

    def _predict_proba(self, X):
        """Predicts labels probabilities sequences reading from files.

        Parameters
        ----------
        X : 3D np.array of shape = [n_instances, n_dimensions, series_length]
            The data to make predict probabilities for.

        Returns
        -------
        y : array-like, shape = [n_instances, n_classes_]
            Predicted probabilities using the ordering in classes_.

        Notes
        ----
        Predicts labels probabilities for sequences in X loading each ensemble estimated probabilities from file.
        Loads the probabilities from the test files,
        applies the weights and returns the estimated probabilities.
        """

        # for each file path input:
        #   load test file at path (testResample.csv if random_state is None,
        #   testResample0.csv otherwise)
        file_name = 'testResample.csv'
        if self.random_state != None:
            file_name = 'testResample' + str(self.random_state) + '.csv'

        dists = np.zeros((X.shape[0], self.n_classes_))

        i = 0
        for path in self.file_paths:
            f = open(path + file_name, "r")
            lines = f.readlines()
            line2 = lines[2].split(",")

            #   verify file matches data, i.e. n_instances and n_classes
            if len(lines) - 3 != len(X):  # verify n_instances
                print("ERROR n_instances does not match in: ", path + file_name)
            if self.n_classes_ != int(line2[5]):  # verify n_classes
                print("ERROR n_classes does not match in: ", path + file_name, self.n_classes_, line2[5])

            #   apply this files weights to the probabilities in the test file
            for j in range(X.shape[0]):
                dists[j] = np.add(
                    dists[j],
                    [float(k) for k in (lines[j+3].split(",")[3:])] * (np.ones(self.n_classes_) * self._weights[i]),
            )
            i += 1

        # Make each instances probability array sum to 1 and return
        return dists / dists.sum(axis=1, keepdims=True)

    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """Return testing parameter settings for the estimator.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.
            For classifiers, a "default" set of parameters should be provided for
            general testing, and a "results_comparison" set for comparing against
            previously recorded results if the general set does not produce suitable
            probabilities to compare against.

        Returns
        -------
        params : dict or list of dict, default={}
            Parameters to create testing instances of the class.
            Each dict are parameters to construct an "interesting" test instance, i.e.,
            `MyClass(**params)` or `MyClass(**params[i])` creates a valid test instance.
            `create_test_instance` uses the first (or only) dictionary in `params`.
        """
        file_paths = [
            "test_files/Arsenal/",
            "test_files/DrCIF/",
            "test_files/STC/",
            "test_files/TDE/",
        ]
        return {"file_paths": file_paths, "random_state": 0}
