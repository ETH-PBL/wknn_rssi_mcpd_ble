from configs import Point
from dataclasses import dataclass
from typing import Dict
from numpy import infty
from numpy.linalg import norm
import configs
import pandas as pd
from enum import Enum


class Metric(Enum):
    CHEBYSHEV = infty
    EUCLID = None

    def __str__(self):
        if self == Metric.CHEBYSHEV:
            return "CHEBYSHEV-norm"
        elif self == Metric.EUCLID:
            return "EUCLIDIAN-norm"


@dataclass
class Result:
    idx: int
    metric: Metric
    k: int
    position: Point
    rssi_k_closest: Dict[int, float]
    mcpd_k_closest: Dict[int, float]
    rssi_estimation: Point
    rssi_euc_error: float
    mcpd_estimation: Point
    mcpd_euc_error: float

    def __str__(self):
        return """Result for point {}, using {}
        k: {}
        Position: {}

        RSSI-k-closest: {}
        RSSI estimation: {}
        RSSI error: {}

        MCPD-k-closest: {}
        MCPD estimation: {}
        MCPD error: {}
        """.format(
            self.idx,
            self.metric,
            self.k,
            self.position,
            self.rssi_k_closest,
            self.rssi_estimation,
            self.rssi_euc_error,
            self.mcpd_k_closest,
            self.mcpd_estimation,
            self.mcpd_euc_error,
        )


def get_norm(measurement, reference, metric: Metric):
    """Computes the norm from a measurement to all reference measurements

    :param measurement: A Dataframe containing headers 'id', 'rssi', 'mcpd_ifft' - and exactly one row per beacon/id'
    :param reference: A Dataframe containing headers 'position', 'id', 'rssi', 'mcpd_ifft' - and exactly one row per beacon/id per reference position'
    :param metric: Desired norm, chebyshev or euclid (enum)
    :returns: (rssi_vector_norm, mcpd_vector_norm), both dictionaries with refernce position as index

    """
    rssi_vector_norm = dict()
    mcpd_vector_norm = dict()

    # Create dictionary from measurement dataframe
    rssi_m = dict(zip(measurement["id"], measurement["rssi"]))
    mcpd_m = dict(zip(measurement["id"], measurement["mcpd_ifft"]))

    # For each reference positin
    for i in reference["position"].unique():
        rssi_vector_diff = []
        mcpd_vector_diff = []
        # Create dictionary from rssi
        rssi_r = reference[reference["position"] == i][["id", "rssi"]]
        rssi_r = dict(zip(rssi_r["id"], rssi_r["rssi"]))
        # Create dictionary from mcpd
        mcpd_r = reference[reference["position"] == i][["id", "mcpd_ifft"]]
        mcpd_r = dict(zip(mcpd_r["id"], mcpd_r["mcpd_ifft"]))

        # For each beacon in the room, calculate the vector difference between measurement and reference
        for b in configs.room.beacons:
            rssi_vector_diff.append(rssi_m[b.n] - rssi_r[b.n])
            mcpd_vector_diff.append(mcpd_m[b.n] - mcpd_r[b.n])

        # Compute the vector norm
        rssi_vector_norm[i] = norm(rssi_vector_diff, ord=metric.value)
        mcpd_vector_norm[i] = norm(mcpd_vector_diff, ord=metric.value)

    # Return the vector norm
    return (rssi_vector_norm, mcpd_vector_norm)


def compute_estimation(closest: Dict[int, float]) -> Point:
    """Using the k closest neighbors, computes the weighted kNN estimation

    :param closest: dictionary containing closest point as key and the corresponding distance as value
    :returns: a single Point, the result of the computation

    """
    # Get k closest references
    references = {key: configs.room.train_points[key] for key in closest}
    sum_w_i = 1 / sum([1 / x for x in closest.values()])
    estimate = sum_w_i * sum([(1 / closest[i]) * references[i] for i in closest.keys()])
    return estimate


def get_estimation_point(k: int, point: int, metric: Metric):
    """Computes a result for MCPD and RSSI for a given ground-truth point

    :param k: k-closest Neighbors
    :param point: integer, pointing to the number of the measurement position
    :param metric: Chebyshev or Euclidian norm for computation
    :returns: Result, containing all informations needed

    """
    reference = pd.read_csv("{}results_avg.csv".format(configs.train_set_path))[
        ["position", "id", "rssi", "mcpd_ifft"]
    ]
    test = pd.read_csv("{}results_avg.csv".format(configs.test_set_path))[
        ["position", "id", "rssi", "mcpd_ifft"]
    ]
    validation = pd.read_csv("{}results_avg.csv".format(configs.validation_set_path))[
        ["position", "id", "rssi", "mcpd_ifft"]
    ]
    if point in configs.room.validation_points:
        measurement = validation[validation["position"] == point]
        ref_point = configs.room.validation_points[point]
    elif point in configs.room.train_points:
        measurement = test[test["position"] == point]
        ref_point = configs.room.train_points[point]
    else:
        raise ValueError("Point {} does not exist".format(point))

    # get norm distances
    (rssi, mcpd) = get_norm(measurement, reference, metric)

    ### As insertion order is preserved: sort them by value to get k closest neighbors:
    # Get index
    rssi_k_closest = list(dict(sorted(rssi.items(), key=lambda item: item[1])))[0:k]
    mcpd_k_closest = list(dict(sorted(mcpd.items(), key=lambda item: item[1])))[0:k]

    # Get dictionary out of it
    rssi_k_closest = {key: rssi[key] for key in rssi_k_closest}
    mcpd_k_closest = {key: mcpd[key] for key in mcpd_k_closest}

    # Estimate position
    rssi_estimation = compute_estimation(rssi_k_closest)
    mcpd_estimation = compute_estimation(mcpd_k_closest)

    # Calculate error to reference point
    rssi_error = ref_point.euc_distance(rssi_estimation)
    mcpd_error = ref_point.euc_distance(mcpd_estimation)

    # Return result
    return Result(
        idx=point,
        metric=metric,
        k=k,
        position=ref_point,
        rssi_k_closest=rssi_k_closest,
        mcpd_k_closest=mcpd_k_closest,
        rssi_estimation=rssi_estimation,
        rssi_euc_error=rssi_error,
        mcpd_estimation=mcpd_estimation,
        mcpd_euc_error=mcpd_error,
    )
