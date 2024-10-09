from aeon.classification.base import BaseClassifier


class CondenserClassifier(BaseClassifier):
    """
    Classifier wrapper for its use with any condensing approach.

    Parameters
    ----------
    distance
    distance_params

    Examples
    --------
     >>> from ...
     >>> from ...
    """

    _tags = {
        "univariate-only": True,
        "fit_is_empty": False,
        "X_inner_mtype": ["np-list", "numpy3D"],
    }

    def __init__(
        self,
        condenser=None,
        distance="dtw",
        distance_params=None,
        classifier=None,
        num_instances=1,
        random_state=None,
    ):
        self.distance = distance

        self.distance_params = distance_params
        if self.distance_params is None:
            self.distance_params = {}

        self.num_instances = num_instances

        self.random_state = random_state

        self.condenser = condenser
        if self.condenser is None:
            from tsml_eval._wip.condensing.clustering_condenser import (
                ClusteringCondenser,
            )

            self.condenser = ClusteringCondenser(
                clustering_approach="kmeans",
                distance=self.distance,
                distance_params=self.distance_params,
                num_instances_per_class=self.num_instances,
                random_state=self.random_state,
            )

        self.classifier = classifier
        if self.classifier is None:
            from aeon.classification.distance_based import (
                KNeighborsTimeSeriesClassifier,
            )

            self.classifier = KNeighborsTimeSeriesClassifier(
                distance=self.distance,
                weights="distance",
                distance_params=self.distance_params,
                n_neighbors=1,
            )
        super().__init__()

    def _fit(self, X, y):
        condensed_X, condensed_y = self.condenser.fit_transform(X, y)
        self.classifier.fit(condensed_X, condensed_y)
        return self

    def _predict(self, X):
        return self.classifier.predict(X)
