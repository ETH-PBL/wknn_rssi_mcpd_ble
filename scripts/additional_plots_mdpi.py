#!/bin/python
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

BLUE = "#0072BD"
GREEN = "#77AC30"

number_of_beacons = [3, 4, 5, 6]

rssi_avg = [2.239,2.111,2.069,2.037]
rssi_var = [1.373,1.397,1.356,1.350]
rssi_std = [1.167,1.178,1.160,1.162]

mcpd_avg = [0.696,0.610, 0.539,0.579]
mcpd_var = [0.129,0.050, 0.027,0.020]
mcpd_std = [0.311,0.204,0.158, 0.143]

plt.rc('text', usetex=True)
plt.rcParams.update({
    'mathtext.fontset': 'stix',
    'font.family': 'STIXGeneral',
    'font.size'   : 12,
})
plt.plot(number_of_beacons, rssi_avg, color=BLUE, linestyle='-')
plt.plot(number_of_beacons, mcpd_avg, color=GREEN, linestyle='-')
plt.plot(number_of_beacons, rssi_var, color=BLUE, linestyle='--')
plt.plot(number_of_beacons, mcpd_var, color=GREEN, linestyle='--')
plt.plot(number_of_beacons, rssi_std, color=BLUE, linestyle=':')
plt.plot(number_of_beacons, mcpd_std, color=GREEN, linestyle=':')
plt.legend(['RSSI Avg.', 'MCPD Avg.', 'RSSI Var.', 'MCPD Var.', 'RSSI Std.', 'MCPD Std.'], bbox_to_anchor=(0.5,1.22), ncol=3, columnspacing=0.8, handletextpad=0.2, loc='upper center')
plt.xlabel('Number of beacons')
plt.ylabel('Statistics in m')
plt.title("\\textbf{{Influence of number of beacons}}", y=1.2)
plt.subplots_adjust(top=0.75)
plt.xticks([3,4,5,6])
plt.ylim(0,2.5)
plt.savefig("../figures/infl_num_beac.svg", bbox_inches='tight')
plt.show()

rssi_3b = [2.460,2.445,2.504,1.800,2.362,2.542,1.987,2.599,2.203,2.284,2.349,2.157,1.726,2.523,2.112,1.955,2.475,1.973,1.922,2.399]
print("RSSI 3B difference:")
print(100*(1-min(rssi_3b)/max(rssi_3b)))

mcpd_3b = [0.695,0.554,1.067,0.707,0.503,0.572,0.796,0.771,0.617,0.581,0.601,0.720,0.523,0.934,0.652,0.828,0.580,0.610,0.866,0.748]
print("MCPD 3B difference:")
print(100*(1-min(mcpd_3b)/max(mcpd_3b)))

sns.set_theme()
sns.set_style("whitegrid")
sns.set_style({'mathtext.fontset': 'stix',
    'font.family': 'STIXGeneral',
    'font.size': 12,
    'axes.edgecolor': 'black',
    'axes.linewidth': 1})
sns.set_context(font_scale=2)
f, (ax_box, ax_hist) = plt.subplots(2, gridspec_kw={"height_ratios": (.15, .85)})
sns.boxplot(rssi_3b, ax=ax_box, orient='h')
sns.histplot(rssi_3b, ax=ax_hist, bins=10, kde=True)
ax_box.set(yticks=[], xticks=[])
ax_hist.set(xlabel="Estimation error in m")
plt.suptitle("\\textbf{{Influence of subset on three selected beacons for RSSI}}", y=0.95)
plt.savefig("../figures/infl_subs_beac_rssi.svg", bbox_inches='tight')
plt.show()

f, (ax_box, ax_hist) = plt.subplots(2, gridspec_kw={"height_ratios": (.15, .85)})
sns.boxplot(mcpd_3b, ax=ax_box, orient='h')
sns.histplot(mcpd_3b, ax=ax_hist, bins=10, kde=True)
ax_box.set(yticks=[], xticks=[])
ax_hist.set(xlabel="Estimation error in m")
plt.suptitle("\\textbf{{Influence of subset on three selected beacons for MCPD}}", y=0.95)
plt.savefig("../figures/infl_subs_beac_mcpd.svg", bbox_inches='tight')
plt.show()
