# -*- coding: utf-8 -*-
import pytest
from sklearn.utils.estimator_checks import parametrize_with_checks
from sktime.utils.estimator_checks import check_estimator

from tsml_eval.sktime_estimators.classification.convolution_based.hydra import HYDRA
from tsml_eval.sktime_estimators.classification.distance_based.mpdist import MPDist
from tsml_eval.sktime_estimators.classification.shapelet_based.rdst import (
    RDST,
    RDSTEnsemble,
)
from tsml_eval.sktime_estimators.classification.shapelet_based.rsf import (
    RandomShapeletForest,
)
from tsml_eval.sktime_estimators.classification.transformations import SFADilation
from tsml_eval.sktime_estimators.regression.convolution_based.arsenal import Arsenal
from tsml_eval.sktime_estimators.regression.dictionary_based.tde import (
    TemporalDictionaryEnsemble,
)
from tsml_eval.sktime_estimators.regression.hybrid.hivecote_v2 import HIVECOTEV2
from tsml_eval.sktime_estimators.regression.interval_based.drcif import DrCIF
from tsml_eval.sktime_estimators.regression.shapelet_based.str import (
    ShapeletTransformRegressor,
)
from tsml_eval.sktime_estimators.regression.sklearn.rotation_forest import (
    RotationForest,
)

classification_estimators = [
    # WEASEL_DILATION,
    # MUSE_DILATION,
    SFADilation,
    HYDRA,
    RDST,
    RDSTEnsemble,
    RandomShapeletForest,
    MPDist,
]
regression_estimators = [
    DrCIF,
    ShapeletTransformRegressor,
    # RandomShapeletTransform,
    Arsenal,
    TemporalDictionaryEnsemble,
    # SFA,
    HIVECOTEV2,
]


@pytest.mark.parametrize("est", classification_estimators + regression_estimators)
def test_check_estimator(est):
    check_estimator(est, return_exceptions=False)


regression_sklearn_estimators = [RotationForest(n_estimators=3)]


@parametrize_with_checks(regression_sklearn_estimators)
def test_sklearn_compatible_estimator(estimator, check):
    """Test that sklearn estimators adhere to sklearn conventions."""
    check(estimator)
