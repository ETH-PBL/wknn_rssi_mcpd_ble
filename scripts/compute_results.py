#!/bin/python

from datetime import time
from typing import Dict, List
import configs
from wknn import Metric, get_estimation_point, Result, get_estimation_point_from_average
from pytablewriter import MarkdownTableWriter
from pytablewriter.style import Style
import matplotlib.pyplot as plt
from math import ceil
import seaborn as sns
import pandas as pd
import itertools
import numpy as np

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
        plt.legend(["Beacons","Train Pos.","Reference"], scatteryoffsets=[0.5,0.5,0.5], bbox_to_anchor=(0.5,1.1), ncol=3, columnspacing=0.5, handletextpad=-0.2, loc='upper center')
        leg = plt.gca().get_legend()
        leg.legendHandles[2].set_edgecolor('k')
        leg.legendHandles[2].set_facecolor('#FFFFFF')
        plt.savefig("../figures/room_setup.svg")
        #plt.show()
        plt.close('all')
    else:
        plt.legend(["Beacons","Train Pos.","Ref.","Est.", "Avg. Est."], scatteryoffsets=[0.5,0.5,0.5,0.5,0.5], bbox_to_anchor=(0.5,1.1), ncol=5, columnspacing=0.4, handletextpad=-0.3, loc='upper center')
        leg = plt.gca().get_legend()
        for i in range(2,5):
            leg.legendHandles[i].set_edgecolor('k')
            leg.legendHandles[i].set_facecolor('#FFFFFF')
        plt.savefig("../figures/k{}_{}_{}.svg".format(k, str(metric).lower(), method.lower()))
        #plt.show()
        plt.close('all')

def histogram_boxplot(data, k, metric, method: str, xlim: List = [], bins = None):
    sns.set_theme()
    sns.set_style("whitegrid")
    sns.set_style({'mathtext.fontset': 'stix',
        'font.family': 'STIXGeneral',
        'font.size': 12,
        'axes.edgecolor': 'black',
        'axes.linewidth': 1})
    sns.set_context(font_scale=2)
    f, (ax_box, ax_hist) = plt.subplots(2, gridspec_kw={"height_ratios": (.15, .85)})
    sns.boxplot(data, ax=ax_box, orient='h')
    sns.histplot(data, ax=ax_hist, bins=bins, kde=True) if bins else sns.histplot(data, ax=ax_hist, kde=True, stat='density')
    ax_box.set(yticks=[], xticks=[])
    ax_hist.set(xlabel="Estimation error in m")
    if len(xlim) != 0: ax_hist.set(xlim=xlim)
    if len(xlim) != 0: ax_box.set(xlim=xlim)

    if metric == Metric.CHEBYSHEV:
        tit_metric = "\\infty"
    else:
        tit_metric = "2"
    plt.suptitle("\\textbf{{{}-Error for wkNN with $k={}$, $||\\cdot||_{}$}}".format(method, k, tit_metric), y=0.95)
    plt.tight_layout()
    plt.savefig("../figures/hist_k{}_{}_{}.svg".format(k, str(metric).lower(), method.lower()))
    #plt.show()
    plt.close('all')

        
# Dict[k][metric][point] = List[Result]
results: Dict[int, Dict[Metric, Dict[int, List[Result]]]] = {}

# Get results for k = 3,5 and Chebyshev,Euclid norm, using Test set and Validation set
for k in [3,5]:
    results[k] = {}
    for metric in Metric:
        results[k][metric] = {}
        for p in configs.room.train_points:
            results[k][metric][p] = [get_estimation_point_from_average(k, p, metric)]
        
        # For each validation position
        for p in configs.room.validation_points:
            # Generate empty result list
            results[k][metric][p] = []
            # Load the dataframes at this position and store them in the dictionary
            df = {}
            for b in configs.room.beacons:
                df[b.n] = pd.read_csv("{}position_{}_beacon_{}.csv".format(configs.validation_set_path, p, b.n))
            # Check length of measurement, on first one
            length = len(list(df.items())[0][1].index)
            # For each measurement, perform an estimation
            for i in range(length):
                # Storage element for the measurement to be performed
                measurement = pd.DataFrame()
                # Combine data from the individual beacons into 'measurement'
                for b in df.keys():
                    val = df[b].iloc[i,2:].to_frame().T
                    val.insert(0, 'position', p)
                    val.insert(1, 'id', b)
                    measurement = pd.concat([measurement, val])
                # Evaluate the measurement, and append to results
                results[k][metric][p].append(get_estimation_point(k, p, metric, measurement))        

# Compute average results:
avg_results: Dict[int, Dict[Metric, Dict[int, Result]]] = {}
for k in [3,5]:
    avg_results[k] = {}
    for metric in Metric:
        avg_results[k][metric] = {}
        for p in configs.room.train_points:
            avg_results[k][metric][p] = get_estimation_point_from_average(k, p, metric)
        for p in configs.room.validation_points:
            avg_results[k][metric][p] = get_estimation_point_from_average(k, p, metric)

# Generate Markdown table with average results
for k in [3,5]:
    for metric in Metric:
        idx = [p.idx for p in avg_results[k][metric].values()]
        # Calculate average results
        rssi_error = [p.rssi_euc_error for p in avg_results[k][metric].values()]
        mcpd_error = [p.mcpd_euc_error for p in avg_results[k][metric].values()]
        # Create dataframe with this informations
        df = pd.DataFrame(data=[rssi_error, mcpd_error], columns=idx).round(decimals=3)
        df.insert(0, "Type", ["RSSI", "MCPD"])
        # Write markdown table
        writer = MarkdownTableWriter(
            table_name="k{}_{}_error".format(k, metric),
            margin=1,
        )
        writer.from_dataframe(
            df,
            add_index_column=False,
        )
        writer.set_style(0, Style(font_weight="bold"))
        # Print Markdown Table
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
    for idx,(p,point) in enumerate(configs.room.validation_points.items()):
        res = get_estimation_point_from_average(k, p, metric)
        plt.scatter(point.x, point.y, 75, marker='*', color=colors[idx])
        if method == "RSSI":
            x = [val.rssi_estimation.x for val in results[k][metric][p]]
            x_avg = avg_results[k][metric][p].rssi_estimation.x
            y = [val.rssi_estimation.y for val in results[k][metric][p]]
            y_avg = avg_results[k][metric][p].rssi_estimation.y
        else:
            x = [val.mcpd_estimation.x for val in results[k][metric][p]]
            x_avg = avg_results[k][metric][p].mcpd_estimation.x
            y = [val.mcpd_estimation.y for val in results[k][metric][p]]
            y_avg = avg_results[k][metric][p].mcpd_estimation.y
        plt.scatter(x, y, 5, alpha=0.6, marker='o', color=colors[idx])
        plt.scatter(x_avg, y_avg, 75, alpha=0.6, marker='o', color=colors[idx])
            
    plot_store(k, metric, method)

# Generate Histogram
for k, metric, method in itertools.product([3, 5], [metric.EUCLID, metric.CHEBYSHEV], ["RSSI", "MCPD"]):
    error = []
    for idx,(p,point) in enumerate(configs.room.validation_points.items()):
        if method == "RSSI":
            error.extend([val.rssi_euc_error for val in results[k][metric][p]])
        else:
            error.extend([val.mcpd_euc_error for val in results[k][metric][p]])
    print("{}, k={}, metric={}, Var: {}, Std: {}, Avg: {}, Max: {}, Min: {}".format(method, k, metric, np.var(error), np.std(error), np.mean(error), max(error), min(error)))
    xlim = [0, ceil(max(error))]
    histogram_boxplot(error, k, metric, method, xlim=xlim, bins=20)
