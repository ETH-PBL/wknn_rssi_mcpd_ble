#!/bin/python
import numpy as np
import pandas as pd
import configs
from sklearn.model_selection import train_test_split
from typing import List

# Data frame holding the average values for train and test data
results_train = pd.DataFrame()
results_test = pd.DataFrame()

# For all trainings positions
for f in configs.room.train_points:
    # Read dataframe of this train position
    df = pd.read_csv(
        "{}{}.csv".format(configs.raw_data_path, f),
        header=None,
        names=configs.uart_columns,
    )
    # For each beacon
    for b in configs.room.beacons:
        # Get data of this beacon
        f_b = df[df["uuid"] == b.uuid].copy()
        # Split data: 100 for train, the rest for test
        train, test = train_test_split(f_b, train_size=100, random_state=0)
        # Store in csv
        train.to_csv('{}position_{}_beacon_{}.csv'.format(configs.train_set_path, f, b.n), index=False)
        test.to_csv('{}position_{}_beacon_{}.csv'.format(configs.test_set_path, f, b.n), index=False)
        # Calculate the average of all train data
        avg_train = train.iloc[:,2:].mean().to_frame().T
        avg_train.insert(0, 'position', f)
        avg_train.insert(1, 'id', b.n)
        results_train = pd.concat([results_train, avg_train])
        # Calculate the average of all test data
        avg_test = test.iloc[:,2:].mean().to_frame().T
        avg_test.insert(0, 'position', f)
        avg_test.insert(1, 'id', b.n)
        results_test = pd.concat([results_test, avg_test])

# Store all average results for this position for train and test set
results_train.to_csv('{}results_avg.csv'.format(configs.train_set_path), index=False)
results_test.to_csv('{}results_avg.csv'.format(configs.test_set_path), index=False)

# Data frame holding the average values for validation data
results_validation = pd.DataFrame()
for f in configs.room.validation_points:
    # Read validation data for this position
    df = pd.read_csv(
        "{}{}.csv".format(configs.raw_data_path, f),
        header=None,
        names=configs.uart_columns,
    )
    # For each beacon
    for b in configs.room.beacons:
        # Store in csv
        f_b = df[df["uuid"] == b.uuid].copy()
        f_b.to_csv('{}position_{}_beacon_{}.csv'.format(configs.validation_set_path, f, b.n), index=False)
        # Calculate the average of all validation data
        avg_validation = f_b.iloc[:,2:].mean().to_frame().T
        avg_validation.insert(0, 'position', f)
        avg_validation.insert(1, 'id', b.n)
        results_validation = pd.concat([results_validation, avg_validation])

# Store all average results for this position for validation set
results_validation.to_csv('{}results_avg.csv'.format(configs.validation_set_path), index=False)
