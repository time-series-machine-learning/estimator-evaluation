# -*- coding: utf-8 -*-
"""Utility functions for experiments."""

__author__ = ["TonyBagnall", "MatthewMiddlehurst"]

__all__ = [
    "resample_data",
    "stratified_resample_data",
    "write_classification_results",
    "write_regression_results",
    "write_clustering_results",
    "write_results_to_tsml_format",
    "validate_results_file",
    "fix_broken_second_line",
    "compare_result_file_resample",
    "assign_gpu",
]

import os

import gpustat
import numpy as np
import pandas as pd
from sklearn.utils import check_random_state


def resample_data(X_train, y_train, X_test, y_test, random_state=None):
    """Resample data without replacement using a random state.

    Reproducable resampling. Combines train and test, randomly resamples, then returns
    new train and test.

    Parameters
    ----------
    X_train : pd.DataFrame
        Train data attributes in sktime pandas format.
    y_train : np.array
        Train data class labels.
    X_test : pd.DataFrame
        Test data attributes in sktime pandas format.
    y_test : np.array
        Test data class labels.
    random_state : int, RandomState instance or None, default=None
        If `int`, random_state is the seed used by the random number generator;
        If `RandomState` instance, random_state is the random number generator;
        If `None`, the random number generator is the `RandomState` instance used
        by `np.random`.

    Returns
    -------
    (train_X, train_y, test_X, test_y) : tuple of pd.DataFrames
        New train and test data and class label splits.
    """
    all_targets = np.concatenate((y_train, y_test), axis=None)
    all_data = pd.concat([X_train, X_test])

    # add the target labeleds to the dataset
    all_data["target"] = all_targets

    # randomly shuffle all instances
    shuffled = all_data.sample(frac=1, random_state=random_state)

    # extract and remove the target column
    all_targets = shuffled["target"].to_numpy()
    shuffled = shuffled.drop("target", axis=1)

    # split the shuffled data into train and test
    train_cases = y_train.size
    X_train = shuffled.iloc[:train_cases]
    X_test = shuffled.iloc[train_cases:]
    y_train = all_targets[:train_cases]
    y_test = all_targets[train_cases:]

    # reset indices and return
    X_train = X_train.reset_index(drop=True)
    X_test = X_test.reset_index(drop=True)
    return X_train, y_train, X_test, y_test


def stratified_resample_data(X_train, y_train, X_test, y_test, random_state=None):
    """Stratified resample data without replacement using a random state.

    Reproducable resampling. Combines train and test, resamples to get the same class
    distribution, then returns new train and test.

    Parameters
    ----------
    X_train : pd.DataFrame
        Train data attributes in sktime pandas format.
    y_train : np.array
        Train data class labels.
    X_test : pd.DataFrame
        Test data attributes in sktime pandas format.
    y_test : np.array
        Test data class labels.
    random_state : int, RandomState instance or None, default=None
        If `int`, random_state is the seed used by the random number generator;
        If `RandomState` instance, random_state is the random number generator;
        If `None`, the random number generator is the `RandomState` instance used
        by `np.random`.

    Returns
    -------
    (train_X, train_y, test_X, test_y) : tuple of pd.DataFrames
        New train and test data and class label splits.
    """
    all_labels = np.concatenate((y_train, y_test), axis=None)
    all_data = pd.concat([X_train, X_test])

    random_state = check_random_state(random_state)

    # count class occurrences
    unique_train, counts_train = np.unique(y_train, return_counts=True)
    unique_test, counts_test = np.unique(y_test, return_counts=True)

    # ensure same classes exist in both train and test
    assert list(unique_train) == list(unique_test)

    X_train = pd.DataFrame()
    y_train = np.array([])
    X_test = pd.DataFrame()
    y_test = np.array([])

    # for each class
    for label_index in range(0, len(unique_train)):
        # get the indices of all instances with this class label
        label = unique_train[label_index]
        indices = np.where(all_labels == label)[0]

        # shuffle them
        random_state.shuffle(indices)

        # take the first lot of instances for train, remainder for test
        num_instances = counts_train[label_index]
        train_indices = indices[0:num_instances]
        test_indices = indices[num_instances:]

        # extract data from corresponding indices
        train_instances = all_data.iloc[train_indices, :]
        test_instances = all_data.iloc[test_indices, :]
        train_labels = all_labels[train_indices]
        test_labels = all_labels[test_indices]

        # concat onto current data from previous loop iterations
        X_train = pd.concat([X_train, train_instances])
        X_test = pd.concat([X_test, test_instances])
        y_train = np.concatenate([y_train, train_labels], axis=None)
        y_test = np.concatenate([y_test, test_labels], axis=None)

    # reset indices and return
    X_train = X_train.reset_index(drop=True)
    X_test = X_test.reset_index(drop=True)
    return X_train, y_train, X_test, y_test


def write_classification_results(
    predictions,
    probabilities,
    class_labels,
    classifier_name,
    dataset_name,
    output_path,
    full_path=True,
    split=None,
    resample_id=None,
    timing_type="N/A",
    first_line_comment=None,
    parameter_info="No Parameter Info",
    accuracy=-1,
    fit_time=-1,
    predict_time=-1,
    benchmark_time=-1,
    memory_usage=-1,
    n_classes=-1,
    train_estimate_method="",
    train_estimate_time=-1,
    fit_and_estimate_time=-1,
):
    """Write the predictions for a classification experiment in the format used by tsml.

    Parameters
    ----------
    predictions : np.array
        The predicted values to write to file. Must be the same length as labels.
    probabilities : np.ndarray
        Estimated class probabilities. These are written after the
        predicted values for each case.
    class_labels : np.array
        The actual class values written to file with the predicted values.
    classifier_name : str
        Name of the classifier that made the predictions. Written to file and can
        determine file structure if full_path is False.
    dataset_name : str
        Name of the problem the classifier was built on.
    output_path : str
        Path to write the results file to or the directory to build the default file
        structure if full_path is False.
    full_path : boolean, default=True
        If True, results are written directly to the directory passed in output_path.
        If False, then a standard file structure using the classifier and dataset names
        is created and used to write the results file.
    split : str or None, default=None
        Either None, 'TRAIN' or 'TEST'. Influences the result file name and first line
        of the file.
    resample_id : int or None, default=None
        Indicates what random seed was used to resample the data or used as a
        random_state for the classifier.
    timing_type : str, default="N/A"
        The format used for timings in the file, i.e. 'Seconds', 'Milliseconds',
        'Nanoseconds'
    first_line_comment : str or None, default=None
        Optional comment appended to the end of the first line, i.e. the file used to
        generate the results.
    parameter_info : str, default="No Parameter Info"
        Unstructured estimator dependant information, i.e. estimator parameters or
        values from the model build.
    accuracy: float, default=-1
        The accuracy of the predictions.
    fit_time : int, default=-1
        The time taken to fit the classifier.
    predict_time : int, default=-1
        The time taken to predict the class labels.
    benchmark_time : int, default=-1
        A benchmark time for the hardware used to scale other timings.
    memory_usage : int, default=-1
        The memory usage of the classifier.
    n_classes : int, default=-1
        The number of classes in the dataset.
    train_estimate_method : str, default=""
        The method used to generate predictions for results on training data.
    train_estimate_time : int, default=-1
        The time taken to generate predictions for results on training data.
    fit_and_estimate_time : int, default=-1
        The time taken to fit the classifier to build and generate predictions for
        results on training data.

        This is not necessarily always going to be fit_time + train_estimate_time,
        i.e. if an estimate requires the model to be fit, fit_time would be
        included in the train_estimate_time value. In this case fit_time +
        train_estimate_time would time fitting the model twice.
    """
    if len(predictions) != len(probabilities) != len(class_labels):
        raise IndexError(
            "The number of predicted values is not the same as the number of actual "
            "class values."
        )

    if n_classes > -1 and n_classes != probabilities.shape[1]:
        raise IndexError(
            "The number of classes is not the same as the number of probability "
            "values for each case."
        )

    third_line = (
        f"{accuracy},"
        f"{fit_time},"
        f"{predict_time},"
        f"{benchmark_time},"
        f"{memory_usage},"
        f"{n_classes},"
        f"{train_estimate_method},"
        f"{train_estimate_time},"
        f"{fit_and_estimate_time}"
    )

    write_results_to_tsml_format(
        predictions,
        class_labels,
        classifier_name,
        dataset_name,
        output_path,
        predicted_probabilities=probabilities,
        full_path=full_path,
        split=split,
        resample_id=resample_id,
        timing_type=timing_type,
        first_line_comment=first_line_comment,
        second_line=parameter_info,
        third_line=third_line,
    )


def write_regression_results(
    predictions,
    labels,
    regressor_name,
    dataset_name,
    output_path,
    full_path=True,
    split=None,
    resample_id=None,
    timing_type="N/A",
    first_line_comment=None,
    parameter_info="No Parameter Info",
    mse=-1,
    fit_time=-1,
    predict_time=-1,
    benchmark_time=-1,
    memory_usage=-1,
    train_estimate_method="",
    train_estimate_time=-1,
    fit_and_estimate_time=-1,
):
    """Write the predictions for a regression experiment in the format used by tsml.

    Parameters
    ----------
    predictions : np.array
        The predicted values to write to file. Must be the same length as labels.
    labels : np.array
        The actual label values written to file with the predicted values.
    regressor_name : str
        Name of the regressor that made the predictions. Written to file and can
        determine file structure if full_path is False.
    dataset_name : str
        Name of the problem the regressor was built on.
    output_path : str
        Path to write the results file to or the directory to build the default file
        structure if full_path is False.
    full_path : boolean, default=True
        If True, results are written directly to the directory passed in output_path.
        If False, then a standard file structure using the regressor and dataset names
        is created and used to write the results file.
    split : str or None, default=None
        Either None, 'TRAIN' or 'TEST'. Influences the result file name and first line
        of the file.
    resample_id : int or None, default=None
        Indicates what random seed was used to resample the data or used as a
        random_state for the regressor.
    timing_type : str, default="N/A"
        The format used for timings in the file, i.e. 'Seconds', 'Milliseconds',
        'Nanoseconds'
    first_line_comment : str or None, default=None
        Optional comment appended to the end of the first line, i.e. the file used to
        generate the results.
    parameter_info : str, default="No Parameter Info"
        Unstructured estimator dependant information, i.e. estimator parameters or
        values from the model build.
    mse: float, default=-1
        The mean squared error of the predictions.
    fit_time : int, default=-1
        The time taken to fit the regressor.
    predict_time : int, default=-1
        The time taken to predict the regression labels.
    benchmark_time : int, default=-1
        A benchmark time for the hardware used to scale other timings.
    memory_usage : int, default=-1
        The memory usage of the regressor.
    train_estimate_method : str, default=""
        The method used to generate predictions for results on training data.
    train_estimate_time : int, default=-1
        The time taken to generate predictions for results on training data.
    fit_and_estimate_time : int, default=-1
        The time taken to fit the regressor to build and generate predictions for
        results on training data.

        This is not necessarily always going to be fit_time + train_estimate_time,
        i.e. if an estimate requires the model to be fit, fit_time would be
        included in the train_estimate_time value. In this case fit_time +
        train_estimate_time would time fitting the model twice.
    """
    third_line = (
        f"{mse},"
        f"{fit_time},"
        f"{predict_time},"
        f"{benchmark_time},"
        f"{memory_usage},"
        f"{train_estimate_method},"
        f"{train_estimate_time},"
        f"{fit_and_estimate_time}"
    )

    write_results_to_tsml_format(
        predictions,
        labels,
        regressor_name,
        dataset_name,
        output_path,
        full_path=full_path,
        split=split,
        resample_id=resample_id,
        timing_type=timing_type,
        first_line_comment=first_line_comment,
        second_line=parameter_info,
        third_line=third_line,
    )


def write_clustering_results(
    cluster_predictions,
    cluster_probabilities,
    class_labels,
    clusterer_name,
    dataset_name,
    output_path,
    full_path=True,
    split=None,
    resample_id=None,
    timing_type="N/A",
    first_line_comment=None,
    parameter_info="No Parameter Info",
    clustering_accuracy=-1,
    fit_time=-1,
    predict_time=-1,
    benchmark_time=-1,
    memory_usage=-1,
    n_classes=-1,
    n_clusters=-1,
):
    """Write the predictions for a clustering experiment in the format used by tsml.

    Parameters
    ----------
    cluster_predictions : np.array
        The predicted values to write to file. Must be the same length as labels.
    cluster_probabilities : np.ndarray
        Estimated class probabilities. If passed, these are written after the
        predicted values for each case.
    class_labels : np.array
        The actual class values written to file with the predicted values. If no label
        is available for a case, a NaN value should be substituted.
    clusterer_name : str
        Name of the clusterer that made the predictions. Written to file and can
        determine file structure if full_path is False.
    dataset_name : str
        Name of the problem the clusterer was built on.
    output_path : str
        Path to write the results file to or the directory to build the default file
        structure if full_path is False.
    full_path : boolean, default=True
        If True, results are written directly to the directory passed in output_path.
        If False, then a standard file structure using the clusterer and dataset names
        is created and used to write the results file.
    split : str or None, default=None
        Either None, 'TRAIN' or 'TEST'. Influences the result file name and first line
        of the file.
    resample_id : int or None, default=None
        Indicates what random seed was used to resample the data or used as a
        random_state for the clusterer.
    timing_type : str, default="N/A"
        The format used for timings in the file, i.e. 'Seconds', 'Milliseconds',
        'Nanoseconds'
    first_line_comment : str or None, default=None
        Optional comment appended to the end of the first line, i.e. the file used to
        generate the results or a dictionary linking label indices to actual values.
    parameter_info : str, default="No Parameter Info"
        Unstructured estimator dependant information, i.e. estimator parameters or
        values from the model build.
    clustering_accuracy : float, default=-1
        The clustering accuracy of the predictions.
    fit_time : int, default=-1
        The time taken to fit the clusterer.
    predict_time : int, default=-1
        The time taken to predict the cluster labels.
    benchmark_time : int, default=-1
        A benchmark time for the hardware used to scale other timings.
    memory_usage : int, default=-1
        The memory usage of the clusterer.
    n_classes : int, default=-1
        The number of classes in the dataset.
    n_clusters : int, default=-1
        The number of clusters founds by the clusterer.
    """
    if len(cluster_predictions) != cluster_probabilities.shape[0] != len(class_labels):
        raise IndexError(
            "The number of predicted values is not the same as the number of actual "
            "class values."
        )

    if n_clusters > -1 and n_clusters != cluster_probabilities.shape[1]:
        raise IndexError(
            "The number of clusters is not the same as the number of probability "
            "values for each case."
        )

    third_line = (
        f"{clustering_accuracy},"
        f"{fit_time},"
        f"{predict_time},"
        f"{benchmark_time},"
        f"{memory_usage},"
        f"{n_classes},"
        f"{n_clusters}"
    )

    write_results_to_tsml_format(
        cluster_predictions,
        class_labels,
        clusterer_name,
        dataset_name,
        output_path,
        predicted_probabilities=cluster_probabilities,
        full_path=full_path,
        split=split,
        resample_id=resample_id,
        timing_type=timing_type,
        first_line_comment=first_line_comment,
        second_line=parameter_info,
        third_line=third_line,
    )


def write_results_to_tsml_format(
    predictions,
    labels,
    estimator_name,
    dataset_name,
    output_path,
    predicted_probabilities=None,
    full_path=True,
    split=None,
    resample_id=None,
    timing_type="N/A",
    first_line_comment=None,
    second_line="No Parameter Info",
    third_line="N/A",
):
    """Write the predictions for an experiment in the standard format used by tsml.

    Parameters
    ----------
    predictions : np.array
        The predicted values to write to file. Must be the same length as labels.
    labels : np.array
        The actual label values written to file with the predicted values. If no label
        is available for a case, a NaN value should be substituted.
    estimator_name : str
        Name of the estimator that made the predictions. Written to file and can
        determine file structure if full_path is False.
    dataset_name : str
        Name of the problem the estimator was built on.
    output_path : str
        Path to write the results file to or the directory to build the default file
        structure if full_path is False.
    predicted_probabilities : np.ndarray, default=None
        Estimated label probabilities. If passed, these are written after the
        predicted values for each case.
    full_path : boolean, default=True
        If True, results are written directly to the directory passed in output_path.
        If False, then a standard file structure using the estimator and dataset names
        is created and used to write the results file.
    split : str or None, default=None
        Either None, 'TRAIN' or 'TEST'. Influences the result file name and first line
        of the file.
    resample_id : int or None, default=None
        Indicates what random seed was used to resample the data or used as a
        random_state for the estimator.
    timing_type : str, default="N/A"
        The format used for timings in the file, i.e. 'Seconds', 'Milliseconds',
        'Nanoseconds'
    first_line_comment : str or None, default=None
        Optional comment appended to the end of the first line, i.e. the file used to
        generate the results or a dictionary linking label indices to actual values.
    second_line : str, default="No Parameter Info"
        Unstructured estimator dependant information, i.e. estimator parameters or
        values from the model build.
    third_line : str, default = "N/A"
        Summary performance information, what values are written depends on the task.
    """
    if len(predictions) != len(labels):
        raise IndexError(
            "The number of predicted values is not the same as the number of actual "
            "labels."
        )

    # If the full directory path is not passed, make the standard structure
    if not full_path:
        output_path = f"{output_path}/{estimator_name}/Predictions/{dataset_name}/"

    try:
        os.makedirs(output_path)
    except os.error:
        pass  # raises os.error if path already exists, so just ignore this

    if split is None:
        split = ""
    elif split.lower() == "train":
        split = "TRAIN"
    elif split.lower() == "test":
        split = "TEST"
    else:
        raise ValueError("Unknown 'split' value - should be 'TRAIN', 'TEST' or None")

    fname = (
        f"{split.lower()}Results"
        if resample_id is None
        else f"{split.lower()}Resample{resample_id}"
    )
    fname = fname.lower() if split == "" else fname

    file = open(f"{output_path}/{fname}.csv", "w")

    # the first line of the output file is in the form of:
    first_line = (
        f"{dataset_name},"
        f"{estimator_name},"
        f"{'No split' if split == '' else split},"
        f"{'None' if resample_id is None else resample_id},"
        f"{timing_type},"
        f"{'' if first_line_comment is None else first_line_comment}"
    )
    file.write(first_line + "\n")

    # the second line of the output is free form and estimator-specific; usually this
    # will record info such as paramater options used, any constituent model
    # names for ensembles, etc.
    file.write(str(second_line) + "\n")

    # the third line of the file depends on the task i.e. classification or regression
    file.write(str(third_line) + "\n")

    # from line 4 onwards each line should include the actual and predicted class
    # labels (comma-separated). If present, for each case, the probabilities of
    # predicting every class value for this case should also be appended to the line (
    # a space is also included between the predicted value and the predict_proba). E.g.:
    #
    # if predict_proba data IS provided for case i:
    #   labels[i], preds[i],,prob_class_0[i],
    #   prob_class_1[i],...,prob_class_c[i]
    #
    # if predict_proba data IS NOT provided for case i:
    #   labels[i], predd[i]
    #
    # If labels[i] is NaN (if clustering), labels[i] is replaced with ? to indicate
    # missing
    for i in range(0, len(predictions)):
        label = "?" if np.isnan(labels[i]) else labels[i]
        file.write(f"{label},{predictions[i]}")

        if predicted_probabilities is not None:
            file.write(",")
            for j in predicted_probabilities[i]:
                file.write(f",{j}")
        file.write("\n")

    file.close()


def _results_present(path, estimator, dataset, res):
    """Check if results are present already."""
    full_path = f"{path}/{estimator}/Predictions/{dataset}/testResample{res}.csv"
    full_path2 = f"{path}/{estimator}/Predictions/{dataset}/trainResample{res}.csv"
    if os.path.exists(full_path) and os.path.exists(full_path2):
        return True
    return False


def _results_present_full_path(path, dataset, res):
    """Duplicate: check if results are present already without an estimator input."""
    full_path = f"{path}/Predictions/{dataset}/testResample{res}.csv"
    full_path2 = f"{path}/Predictions/{dataset}/trainResample{res}.csv"
    if os.path.exists(full_path) and os.path.exists(full_path2):
        return True
    return False


def validate_results_file(file_path):
    """Validate that a results file is in the correct format.

    Validates that the first, second, third and results lines follow the expected
    format. This does not verify that the actual contents of the results file make
    sense.

    Works for classification, regression and clustering results files.

    Parameters
    ----------
    file_path : str
        Path to the results file to be validated, including the file itself.

    Returns
    -------
    valid_file : bool
        True if the results file is valid, False otherwise.
    """
    with open(file_path, "r") as f:
        lines = f.readlines()

    if not _check_first_line(lines[0]) or not _check_second_line(lines[1]):
        return False

    if _check_classification_third_line(lines[2]) or _check_clustering_third_line(
        lines[2]
    ):
        probabilities = True
    elif _check_regression_third_line(lines[2]):
        probabilities = False
    else:
        return False

    for i in range(3, len(lines)):
        if not _check_results_line(lines[i], probabilities=probabilities):
            return False

    return True


def fix_broken_second_line(file_path, save_path=None):
    """Fix a results while where the written second line has line breaks.

    This function will remove line breaks from any lines between the first line and the
    first seen valid 'third_line' for any results file format.

    Parameters
    ----------
    file_path : str
        Path to the results file to be fixed, including the file itself.
    save_path : str, default=None
        Path to save the fixed results file to, including the file new files name.
        If None, the new file will replace the original file.
    """
    with open(file_path, "r") as f:
        lines = f.readlines()

    line_count = 2
    while (
        not _check_classification_third_line(lines[line_count])
        and not _check_regression_third_line(lines[line_count])
        and not _check_clustering_third_line(lines[line_count])
    ):
        if line_count == len(lines):
            raise ValueError("No valid third line found in input results file.")
        line_count += 1

    if line_count != 2:
        lines[1] = lines[1].replace("\n", " ").replace("\r", " ")
        for i in range(2, line_count - 1):
            lines[1] = lines[1] + lines[i].replace("\n", " ").replace("\r", " ")
        lines[1] = lines[1] + lines[line_count - 1]
        lines = lines[:2] + lines[line_count:]

    if save_path is not None or line_count != 2:
        if save_path is None:
            save_path = file_path

        try:
            os.makedirs(os.path.dirname(save_path))
        except os.error:
            pass  # raises os.error if path already exists, so just ignore this

        with open(save_path, "w") as f:
            f.writelines(lines)


def _check_first_line(line):
    line = line.split(",")
    return len(line) >= 5


def _check_second_line(line):
    line = line.split(",")
    return len(line) >= 1


def _check_classification_third_line(line):
    line = line.split(",")
    floats = [0, 1, 2, 3, 4, 5, 7, 8]
    return _check_line_length_and_floats(line, 9, floats)


def _check_regression_third_line(line):
    line = line.split(",")
    floats = [0, 1, 2, 3, 4, 6, 7]
    return _check_line_length_and_floats(line, 8, floats)


def _check_clustering_third_line(line):
    line = line.split(",")
    floats = [0, 1, 2, 3, 4, 5, 6]
    return _check_line_length_and_floats(line, 7, floats)


def _check_line_length_and_floats(line, length, floats):
    if len(line) != length:
        return False

    for i in floats:
        try:
            float(line[i])
        except ValueError:
            return False

    return True


def _check_results_line(line, probabilities=True):
    line = line.split(",")

    if len(line) < 2:
        return False

    try:
        float(line[0])
        float(line[1])
    except ValueError:
        return False

    if probabilities:
        if len(line) < 5 or line[2] != "":
            return False

        try:
            float(line[3])
            float(line[4])
        except ValueError:
            return False
    else:
        if len(line) != 2:
            return False

    return True


def compare_result_file_resample(file_path1, file_path2):
    """Validate that a two results files use the same data resample.

    Files are deemed as having the same resample if the file length is the same and all
    true label values are the same in both files.

    Parameters
    ----------
    file_path1 : str
        Path to the first results file to be compared, including the file itself.
    file_path1 : str
        Path to the second results file to be compared, including the file itself.

    Returns
    -------
    same_resample : bool
        True if the results file use the same data resample, False otherwise.
    """
    with open(file_path1, "r") as f:
        lines1 = f.readlines()

    with open(file_path2, "r") as f:
        lines2 = f.readlines()

    if len(lines1) != len(lines2):
        raise ValueError("Input results file have different numbers of lines.")

    for i in range(3, len(lines1)):
        if lines1[i].split(",")[0] != lines2[i].split(",")[0]:
            return False

    return True


def assign_gpu():
    """Assign a GPU to the current process.

    Looks at the available Nvidia GPUs and assigns the GPU with the lowest used memory.

    Returns
    -------
    gpu : int
        The GPU assigned to the current process.
    """
    stats = gpustat.GPUStatCollection.new_query()
    pairs = [
        [
            gpu.entry["index"],
            float(gpu.entry["memory.used"]) / float(gpu.entry["memory.total"]),
        ]
        for gpu in stats
    ]
    return min(pairs, key=lambda x: x[1])[0]
