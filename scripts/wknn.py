from typing_extensions import Self
from configs import Point
from dataclasses import dataclass, field
from typing import Dict, List, Union
from numpy import infty, mean
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
    rssi_estimation: Point
    mcpd_estimation: Point
    rssi_euc_error: float
    mcpd_euc_error: float
    rssi_k_closest: Dict[int, float] = field(default_factory=lambda: dict())
    mcpd_k_closest: Dict[int, float] = field(default_factory=lambda: dict())

    @classmethod
    def average(cls, values: List[Self]) -> Self:
        if len(values) == 0:
            raise ValueError("List cannot be empty")
        idx = values[0].idx
        metric = values[0].metric
        k = values[0].k
        position = values[0].position
        rssi_estimation: Point = Point(float(mean([v.rssi_estimation.x for v in values])), float(mean([v.rssi_estimation.y for v in values])))
        mcpd_estimation: Point = Point(float(mean([v.mcpd_estimation.x for v in values])), float(mean([v.mcpd_estimation.y for v in values])))
        rssi_euc_error: float = float(mean([v.rssi_euc_error for v in values]))
        mcpd_euc_error: float = float(mean([v.mcpd_euc_error for v in values]))
        return cls(idx, metric, k, position, rssi_estimation, mcpd_estimation, rssi_euc_error, mcpd_euc_error)
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


def get_norm(measurement, reference, beacons, metric: Metric):
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
        for b in beacons:
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


def get_estimation_point(k: int, point: int, beacons, metric: Metric, measurement):
    """Computes a result for MCPD and RSSI for a given ground-truth point and a given measurement

    :param k: k-closest Neighbors
    :param point: integer, pointing to the number of the measurement position
    :param metric: Chebyshev or Euclidian norm for computation
    :param measurement: A Dataframe containing headers 'id', 'rssi', 'mcpd_ifft' - and exactly one row per beacon/id'
    :returns: Result, containing all informations needed

    """
    # Get the average reference trainings data of all positions
    reference = pd.read_csv("{}results_avg.csv".format(configs.train_set_path))[
        ["position", "id", "rssi", "mcpd_ifft"]
    ]

    # Get ground truth position "ref_point" of desired point
    if point in configs.room.validation_points:
        ref_point = configs.room.validation_points[point]
    elif point in configs.room.train_points:
        ref_point = configs.room.train_points[point]
    else:
        raise ValueError("Point {} does not exist".format(point))

    # Get norm distances between the trainings data and the measurement for all trainings points
    (rssi, mcpd) = get_norm(measurement, reference, beacons, metric)

    ### As insertion order is preserved: sort them by value to get k closest neighbors:
    # Get index
    rssi_k_closest = list(dict(sorted(rssi.items(), key=lambda item: item[1])))[0:k]
    mcpd_k_closest = list(dict(sorted(mcpd.items(), key=lambda item: item[1])))[0:k]

    # Get dictionary out of it
    rssi_k_closest = {key: rssi[key] for key in rssi_k_closest}
    mcpd_k_closest = {key: mcpd[key] for key in mcpd_k_closest}

    # Estimate position, using the set of k closest neighbors
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

def get_estimation_point_from_average(k: int, point: int, beacons, metric: Metric):
    """Computes a result for MCPD and RSSI for a given ground-truth point
    :param k: k-closest Neighbors
    :param point: integer, pointing to the number of the measurement position
    :param metric: Chebyshev or Euclidian norm for computation
    :returns: Result, containing all informations needed

    """
    # Get the average test data of all positions
    test = pd.read_csv("{}results_avg.csv".format(configs.test_set_path))[
        ["position", "id", "rssi", "mcpd_ifft"]
    ]
    # Get the average validation data of all positions
    validation = pd.read_csv("{}results_avg.csv".format(configs.validation_set_path))[
        ["position", "id", "rssi", "mcpd_ifft"]
    ]

    # Get measurement of desired point and the ground truth position "ref_point"
    if point in configs.room.validation_points:
        measurement = validation[validation["position"] == point]
    elif point in configs.room.train_points:
        measurement = test[test["position"] == point]
    else:
        raise ValueError("Point {} does not exist".format(point))
    return get_estimation_point(k, point, beacons, metric, measurement)
