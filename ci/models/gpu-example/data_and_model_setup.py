# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, average_precision_score, f1_score
import sigopt
from sklearn.preprocessing import StandardScaler


class LoadTransformData:

    def load_split_dataset(self, dataset_file, random_state=1, test_size=0.2):
        print("downloading and parsing data")
        df = pd.read_csv(dataset_file)
        df.head()
        X = df
        Y = df['isFraud']
        del X['isFraud']
        print('Share of fraudulent activity: {}%'.format(100 * (len(Y.loc[Y == 1]) / float(len(Y)))))
        trainX, testX, trainY, testY = train_test_split(X, Y, test_size=test_size, random_state=random_state)
        return trainX, testX, trainY, testY

    def scale_dataset(self, trainX, testX):
        sc = StandardScaler()
        scaled_trainX, scaled_testX = sc.fit_transform(trainX), sc.fit_transform(testX)
        return scaled_trainX, scaled_testX


def max_missed_fraud(prediction, label, amount):
    """record the mean transaction amount from missing fraudulent transactions"""
    fn_vec = (prediction == 0) & (label > 0)
    fraud_loss_max = np.nan_to_num(amount[fn_vec].max())
    return fraud_loss_max


def max_missed_valid(prediction, label, amount):
    """record the mean transaction amount from flagging valid transactions"""
    fp_vec = (prediction > 0) & (label == 0)
    valid_loss_max = np.nan_to_num(amount[fp_vec].max())
    return valid_loss_max


def log_inference_metrics(prediction, probabilities, testY, testX):
    """Log all relevant metrics using the `predictions` generated by the model,
    the `probabilities` associated with those predictions, the `testY` actual
    labels from the dataset, and `testX` the features."""
    F1score = f1_score(testY,prediction)
    AUPRC = average_precision_score(testY, probabilities)
    tn, fp, fn, tp = confusion_matrix(testY,prediction).ravel()

    sigopt.log_metric('AUPRC test', average_precision_score(testY, probabilities))
    sigopt.log_metric('F1score test', F1score)
    sigopt.log_metric('False Positive test', fp)
    sigopt.log_metric('False Negative test', fn)
    sigopt.log_metric('True Positive test', tp)
    sigopt.log_metric('True Negative test', tn)
    sigopt.log_metric('Max $ Missed Fraudulent', max_missed_fraud(prediction, testY, testX['amount']))
    sigopt.log_metric('Max $ Missed Valid', max_missed_valid(prediction, testY, testX['amount']))

    return F1score, AUPRC, tn, fp, fn, tp
