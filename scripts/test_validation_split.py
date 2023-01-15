#!/bin/python
import numpy as np
import pandas as pd
import configs
from sklearn.model_selection import train_test_split
from typing import List

results_train = pd.DataFrame()
results_test = pd.DataFrame()
for f in configs.room.train_points:
    df = pd.read_csv(
        "{}{}.csv".format(configs.raw_data_path, f),
        header=None,
        names=configs.uart_columns,
    )
    for b in configs.room.beacons:
        f_b = df[df["uuid"] == b.uuid].copy()
        train, test = train_test_split(f_b, train_size=100, random_state=0)
        train.to_csv('{}position_{}_beacon_{}.csv'.format(configs.train_set_path, f, b.n), index=False)
        test.to_csv('{}position_{}_beacon_{}.csv'.format(configs.test_set_path, f, b.n), index=False)
        avg_train = train.iloc[:,2:].mean().to_frame().T
        avg_train.insert(0, 'position', f)
        avg_train.insert(1, 'id', b.n)
        results_train = pd.concat([results_train, avg_train])
        avg_test = test.iloc[:,2:].mean().to_frame().T
        avg_test.insert(0, 'position', f)
        avg_test.insert(1, 'id', b.n)
        results_test = pd.concat([results_test, avg_test])

results_train.to_csv('{}results_avg.csv'.format(configs.train_set_path), index=False)
results_test.to_csv('{}results_avg.csv'.format(configs.test_set_path), index=False)

results_validation = pd.DataFrame()
for f in configs.room.validation_points:
    df = pd.read_csv(
        "{}{}.csv".format(configs.raw_data_path, f),
        header=None,
        names=configs.uart_columns,
    )
    for b in configs.room.beacons:
        f_b = df[df["uuid"] == b.uuid].copy()
        f_b.to_csv('{}position_{}_beacon_{}.csv'.format(configs.validation_set_path, f, b.n), index=False)
        avg_validation = f_b.iloc[:,2:].mean().to_frame().T
        avg_validation.insert(0, 'position', f)
        avg_validation.insert(1, 'id', b.n)
        results_validation = pd.concat([results_validation, avg_validation])

results_validation.to_csv('{}results_avg.csv'.format(configs.validation_set_path), index=False)
