# execute these codes once before actual performance testing codes.

import random
import time


def getRandomPosition(furthestDist):
    return [(random.random() - 0.5) * furthestDist for _ in range(3)]


def getRandomScale():
    return [random.random() * 2.0 for _ in range(3)]


def getRandomColor():
    return random.randint(0, 31)


def getRandomIndex(maxValue):
    return random.randint(0, maxValue)


def getMaxValue(locCount):
    return int(locCount / 10)


class PerfMeasurement:
    def __init__(self, label):
        self._label = label
        self._gap = 0.0

    def __enter__(self,):
        self._start = time.time()
        self._gap = 0.0

    def __exit__(self, *_, **__):
        self._gap = time.time() - self._start
        print(f"{self._label} took {round(self._gap, 4)} seconds.")

    def timeConsumed(self):
        return self._gap


class TotalPerfMeasurement:
    def __init__(self, label):
        self._measurers = []
        self._label = label

    def add(self, label):
        measurement = PerfMeasurement(label)
        self._measurers.append(measurement)
        return measurement

    def __enter__(self,):
        print("-" * 20)
        return self

    def __exit__(self, *_, **__):
        total = 0.0
        for m in self._measurers:
            total = total + m.timeConsumed()

        print(f"{self._label} took {round(total, 4)} seconds.")
        print("-" * 20)


NUM_NODES_LIST = (100, 1000, 10000)
REFINED_NUM_NODES_LIST = (10, 50, 100, 500, 1000, 5000, 10000, 50000)
