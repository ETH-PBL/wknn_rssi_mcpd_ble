#!/bin/python

from datetime import time
from typing import Dict
import configs
from wknn import Metric, get_estimation_point, Result
from pytablewriter import MarkdownTableWriter
from pytablewriter.style import Style
import matplotlib.pyplot as plt
import pandas as pd
import itertools


def plot_beautify(k, metric, method: str):
    LIMIT_TOL = 0.5
    limits = (configs.room.size.x, configs.room.size.y)

    beacons = ([beacon.position.x for beacon in configs.room.beacons],[beacon.position.y for beacon in configs.room.beacons])
    train = ([position.x for position in configs.room.train_points.values()],[position.y for position in configs.room.train_points.values()])

    plt.figure(figsize=[configs.room.size.x*0.7, configs.room.size.y*0.7])
    plt.rc('text', usetex=True)
    plt.rcParams.update({
        'mathtext.fontset': 'stix',
        'font.family': 'STIXGeneral',
        'font.size'   : 12,
    })
    plt.scatter(beacons[0], beacons[1], [75 for x in beacons[0]], marker='^', color='k')
    plt.scatter(train[0], train[1], [75 for x in train[0]], marker='s', color=(0.5, 0.5, 0.5))
    plt.xlim(0-LIMIT_TOL, limits[0]+LIMIT_TOL)
    plt.ylim(0-LIMIT_TOL, limits[1]+LIMIT_TOL)
    plt.xlabel("x-Coordinate in m")
    plt.ylabel("y-Coordinate in m")

    if metric == Metric.CHEBYSHEV:
        metric = "\\infty"
    else:
        metric = "2"

    if k == 0:
        plt.title("\\textbf{{Room setup}}", y=1.1)
    else:
        plt.title("\\textbf{{{}-Results for wkNN with $k={}$, $||\\cdot||_{}$}}".format(method, k, metric), y=1.1)
    plt.tight_layout()

def plot_store(k, metric, method):
    if k == 0:
        plt.legend(["Beacons","Train Pos.","Reference"], scatteryoffsets=[0.5,0.5,0.5,0.5], bbox_to_anchor=(0.5,1.1), ncol=4, columnspacing=0.5, handletextpad=-0.2, loc='upper center')
        plt.savefig("../figures/room_setup.svg")
    else:
        plt.legend(["Beacons","Train Pos.","Reference","Estimation"], scatteryoffsets=[0.5,0.5,0.5,0.5], bbox_to_anchor=(0.5,1.1), ncol=4, columnspacing=0.5, handletextpad=-0.2, loc='upper center')
        plt.savefig("../figures/k{}_{}_{}.svg".format(k, str(metric).lower(), method.lower()))

results: Dict[int, Dict[Metric, Dict[int, Result]]] = {}

# Get results for k = 3,5 and Chebyshev,Euclid norm, using Test set and Validation set
for k in [3,5]:
    results[k] = {}
    for metric in Metric:
        results[k][metric] = {}
        for p in configs.room.train_points:
            results[k][metric][p] = get_estimation_point(k, p, metric)
        for p in configs.room.validation_points:
            results[k][metric][p] = get_estimation_point(k, p, metric)


for k in [3,5]:
    for metric in Metric:
        idx = [p.idx for p in results[k][metric].values()]
        rssi_error = [p.rssi_euc_error for p in results[k][metric].values()]
        mcpd_error = [p.mcpd_euc_error for p in results[k][metric].values()]
        df = pd.DataFrame(data=[rssi_error, mcpd_error], columns=idx).round(decimals=3)
        df.insert(0, "Type", ["RSSI", "MCPD"])

        writer = MarkdownTableWriter(
            table_name="k{}_{}_error".format(k, metric),
            margin=1,
        )
        writer.from_dataframe(
            df,
            add_index_column=False,
        )
        writer.set_style(0, Style(font_weight="bold"))
        
        print(writer.dumps())


# Generate plots:
colors = [(0, 0.4470, 0.7410), (0.8500, 0.3250, 0.0980), (0.9290, 0.6940, 0.1250), (0.4940, 0.1840, 0.5560), (0.4660, 0.6740, 0.1880), (0.3010, 0.7450, 0.9330), (0.6350, 0.0780, 0.1840)]

# Generate overview plot
plot_beautify(0, None, None)
for idx, p in enumerate(configs.room.validation_points.values()):
    plt.scatter(p.x, p.y, 75, marker='*', color=colors[idx])
plot_store(0, None, None)

for k, metric, method in itertools.product([3, 5], [metric.EUCLID, metric.CHEBYSHEV], ["RSSI", "MCPD"]):
    # Generate plot
    plot_beautify(k, metric, method)
    for idx,p in enumerate(configs.room.validation_points.keys()):
        res = get_estimation_point(k, p, metric)
        plt.scatter(res.position.x, res.position.y, 75, marker='*', color=colors[idx])
        if method == "RSSI":
            data = res.rssi_estimation
        else:
            data = res.mcpd_estimation
        plt.scatter(data.x, data.y, 75, marker='o', color=colors[idx])
            
    plot_store(k, metric, method)

plt.show()
