# -*- coding: utf-8 -*-
"""TODO

TODO
"""

__author__ = ["MatthewMiddlehurst", ""]
__all__ = ["FromFileHIVECOTE"]

import numpy as np
from sklearn.utils import check_random_state
from sktime.classification import BaseClassifier


class FromFileHIVECOTE(BaseClassifier):
    """TODO

    TODO
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

        # print(self.file_paths) # ['test_files/Arsenal/', 'test_files/DrCIF/', 'test_files/STC/', 'test_files/TDE/']
        print(self._weights)
        # TODO

        # for each file path input:
        #   load train file at path (trainResample.csv if random_state is None,
        #   trainResample0.csv otherwise)

        #   verify file matches data, i.e. n_instances and n_classes

        #   add a weight to the weight list based on the files accuracy

    def _predict(self, X):
        rng = check_random_state(self.random_state)
        return np.array(
            [
                self.classes_[int(rng.choice(np.flatnonzero(prob == prob.max())))]
                for prob in self.predict_proba(X)
            ]
        )

    def _predict_proba(self, X):
        # TODO

        # for each file path input:
        #   load test file at path (testResample.csv if random_state is None,
        #   testResample0.csv otherwise)

        #   verify file matches data, i.e. n_instances and train n_classes

        #   apply this files weights to the probabilities in the test file

        #  return a single row of probabilities for each input instance, with the row
        #  summing to 1. See how this is done in the HC2 paper or HC2 sktime code.

        return [0, 0]

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
