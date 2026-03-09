import statistics
from typing import Any
from synnax.control.controller import Controller

class average_ch:
    """
    Uses EWMA to run a weighted running average on data in a performant way
    https://en.wikipedia.org/wiki/EWMA_chart
    """

    avg: float
    initialized: bool
    alpha: float

    def __init__(self, window: float | int):
        # Alpha approximates a window of N items: alpha = 2 / (N + 1)
        self.alpha: float = 2.0 / (window + 1)
        self.avg = 0.0
        self.initialized = False

    def add(self, value: float | None) -> None:
        if not self.initialized:
            if value is None:
                raise Exception("Cannot add None value to uninitialized average_ch")
            self.avg: float = value
            self.initialized = True
        else:
            if value is None:
                return
            # Standard EWMA formula
            self.avg: float = (value * self.alpha) + (self.avg * (1 - self.alpha))

    def set_avg(self, input: float) -> None:
        self.avg: float = input

    def get(self) -> float:
        return self.avg

    def add_and_get(self, value: float | None) -> float:
        self.add(value)
        return self.get()


def sensor_vote_values(input: list[float], threshold: float) -> float | None:
    """
    Helper function to vote between a list of values.
    For the values agree within the given threshold, the median is returned
    Values that don't agree inside of the threshold are discarded
    """
    if not input:
        return None
    if len(input) == 1:
        return input[0]

    median_val: float = statistics.median(input)

    trusted_sensors: list[float] = [
        x for x in input if abs(x - median_val) <= threshold
    ]
    if not trusted_sensors:
        return median_val

    return sum(trusted_sensors) / len(trusted_sensors)


def sensor_vote(
    ctrl: Controller, channels: list[str], threshold: float
) -> float | None:
    """
    Wrapper of sensor_vote_values which skips the step of getting the values from the controller
    """
    values: list[float] = []
    for ch in channels:
        value: float | None = ctrl.get(ch)
        if value is not None:
            values.append(value)
    return sensor_vote_values(values, threshold)
