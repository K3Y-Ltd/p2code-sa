import os
import csv

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)


def parse_evaluation_results(results_path):
    """
    Parse `.csv` file with evaluation results.
    """
    y_true = []
    y_pred = []

    with open(results_path, "r") as file:
        reader = csv.reader(file, delimiter=",")

        for row in reader:

            name, pred = row

            y_true.append(0 if "benign" in name else 1)
            y_pred.append(int(pred))

    scores = {
        "accuracy": accuracy_score(y_true=y_true, y_pred=y_pred),
        "precision": precision_score(y_true=y_true, y_pred=y_pred),
        "recall_score": recall_score(y_true=y_true, y_pred=y_pred),
        "f1_score": f1_score(y_true=y_true, y_pred=y_pred),
    }

    return scores
