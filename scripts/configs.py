from dataclasses import dataclass
from typing import List, Dict, Union
from typing_extensions import Self
import math

@dataclass
class Point:
    x: float
    y: float
    def __mul__(self, other: Union[Self, float]) -> Self:
        if isinstance(other, Point):
            return Point(self.x*other.x, self.y*other.y)
        elif isinstance(other, float) or isinstance(other, int):
            return Point(self.x*other, self.y*other)
        else:
            raise TypeError("Class of other does not match Point or float/int")
    def __rmul__(self, other: Union[Self, float]) -> Self:
        return self.__mul__(other)
    def __add__(self, other: Union[Self, float]) -> Self:
        if isinstance(other, Point):
            return Point(self.x+other.x, self.y+other.y)
        elif isinstance(other, float) or isinstance(other, int):
            return Point(self.x+other, self.y+other)
        else:
            raise TypeError("Class of other does not match Point or float/int")
    def __radd__(self, other: Union[Self, float]) -> Self:
        return self.__add__(other)
    def euc_distance(self, other: Self) -> float:
        return math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2)


@dataclass
class Beacon:
    uuid: str
    n: int
    position: Point


@dataclass
class Room:
    beacons: List[Beacon]
    size: Point
    train_points: Dict[int, Point]
    validation_points: Dict[int, Point]


room = Room(
    # 5 and 6 are switched!
    beacons=[
        Beacon(uuid="EE:6F:EE:A7:34:31", n=1, position=Point(x=0, y=0)),
        Beacon(uuid="DE:64:59:3D:8E:63", n=2, position=Point(x=0, y=8.85 / 2)),
        Beacon(uuid="F1:63:F2:BE:56:44", n=3, position=Point(x=0, y=8.85)),
        Beacon(uuid="DB:6D:40:6D:A1:0F", n=4, position=Point(x=7.3, y=8.85)),
        Beacon(uuid="FC:40:5D:54:A7:DD", n=6, position=Point(x=7.3, y=8.85 / 2)),
        Beacon(uuid="FF:B4:7D:AB:1B:A2", n=5, position=Point(x=7.3, y=0)),
    ],
    size=Point(x=7.3, y=8.85),
    train_points={
        1: Point(x=1, y=1.5),
        2: Point(x=3.65, y=1.5),
        3: Point(x=7.3 - 1, y=1.5),
        4: Point(x=1, y=4.425),
        5: Point(x=3.65, y=4.425),
        6: Point(x=7.3 - 1, y=4.425),
        7: Point(x=1, y=8.85 - 1.5),
        8: Point(x=3.65, y=8.85 - 1.5),
        9: Point(x=7.3 - 1, y=8.85 - 1.5),
    },
    validation_points={
        11: Point(x=7.3 - 2.3, y=8.85 - 1.9),
        12: Point(x=2.05, y=2.7),
        13: Point(x=7.3 - 2.07, y=2.9),
        14: Point(x=1.8, y=8.85 - 2.5),
        15: Point(x=7.3 - 3.7, y=8.85 - 2.6),
    },
)

uart_columns = ['uuid', 'state', 'rssi', 'mcpd_ifft', 'mcpd_phase_slope', 'mcpd_rssi_openspace', 'best']

raw_data_path = '../raw_data/'
train_set_path = '../data/train_set/'
test_set_path = '../data/test_set/'
validation_set_path = '../data/validation_set/'
