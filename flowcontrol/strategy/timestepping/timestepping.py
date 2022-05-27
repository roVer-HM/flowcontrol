

import abc
import math

import numpy as np

from flowcontrol.strategy.timestepping.StepSizeAlgorithm import StepSizeAlgorithm

class TimeStepper(abc.ABC):

    def __init__(self, start_time = None,
                 end_time = None,
                 time_discretization_step_size = 0.4,
                 is_round_to_discretization_step_size = False):
        if start_time == None:
            start_time = 0.0
        if end_time == None:
            end_time = np.Inf

        self.time_discretization_step_size = time_discretization_step_size
        self.is_round_to_discretization_step_size = is_round_to_discretization_step_size

        self.set_start_time(start_time)
        self.set_end_time(end_time)
        self.time = None


    @abc.abstractmethod
    def forward_time(self, *args):
        raise NotImplementedError()

    def get_time(self):
        if self.time == None:
            self.time = self.start_time
        return self.time

    @abc.abstractmethod
    def get_next_time(self, sensor_data = None):
        raise NotImplementedError()

    def set_start_time(self, start_time):
        self.start_time = self.round_to_time_discretization_step_size(start_time)

    def set_end_time(self, end_time):
        if end_time == np.inf:
            self.end_time = end_time
        else:
            self.end_time = self.round_to_time_discretization_step_size(end_time)



    def is_active(self, time):
        return self.start_time <= time <= self.end_time

    def set_time_discretization_step_size(self, step_size):
        self.time_discretization_step_size = step_size

    def round_to_time_discretization_step_size(self, value):
        if self.is_round_to_discretization_step_size:
            rounded_value =  self.round_value(value)
            if math.isclose(value, rounded_value) == False:
                print(
                    f"Warning: Start time value={value}s was rounded to {rounded_value}s to match the time discretization step size={self.time_discretization_step_size}s.")
            value = rounded_value
        return value

    def is_rounded(self, value, rounded_value):
        return math.isclose(value, rounded_value)

    def round_value(self, value):
        rounded_value = self.round_to_next_discretization(value)
        if self.is_rounded(value, rounded_value) == False:
            print(
                f"Warning: Rounded value={value}s to {rounded_value}s "
                f"to match the time discretization step size={self.time_discretization_step_size}s.")
        return rounded_value

    def round_to_next_discretization(self, value):
        d = self.time_discretization_step_size
        rounded_value = math.ceil(value / d) * d
        return rounded_value


class FixedTimeStepper(TimeStepper):

    def __init__(self,
                 time_step_size=10.0,
                 start_time=0.0,
                 end_time=None,
                 is_round_to_discretization_step_size=True
                 ):
        super().__init__(start_time=start_time,
                         end_time=end_time,
                         is_round_to_discretization_step_size=is_round_to_discretization_step_size)
        self.set_time_step_size(time_step_size)

    def set_time_step_size(self, time_step_size):
        if time_step_size <= 0.0:
            raise ValueError(f"time step = {time_step_size} not allowed. Must be > 0.")

        rounded_value_1 = self.round_to_next_discretization(time_step_size)
        rounded_value_2 = rounded_value_1 - self.time_discretization_step_size

        message = f"Choose e.g. "
        if rounded_value_2 > 0:
            message += f"{rounded_value_2}s or "
        message += f"{rounded_value_1}s."

        if self.is_rounded(rounded_value=rounded_value_1, value= time_step_size) == False:
            raise ValueError(f"time step size {time_step_size}s not allowed. "
                             f"Time step must be a multiple of {self.time_discretization_step_size}s. "
                             f"{message}")


        self.time_step_size = self.round_to_time_discretization_step_size(time_step_size)

    def forward_time(self, *args):
        if self.time == None:
            self.time = self.get_time()

        self.time += self.time_step_size
        if self.time >= self.end_time:
            self.time = np.inf # assume the simulation end is

    def get_next_time(self, **kwargs):
        self.forward_time()
        return self.get_time()

class AdaptiveTimeStepper(TimeStepper):

    def __init__(self,
                 start_time=0.0,
                 end_time=None,
                 algorithm : StepSizeAlgorithm = None,
                 is_round_to_discretization_step_size=True
                 ):

        self.algorithm = algorithm
        super().__init__(start_time=start_time,
                         end_time=end_time,
                         is_round_to_discretization_step_size=True)

    def set_algorithm(self, algorithm : StepSizeAlgorithm):
        self.algorithm = algorithm

    def get_algorithm(self):
        if self.algorithm == None:
            raise ValueError("No algorithm defined.")
        return self.algorithm

    def forward_time(self, *args):
        self.time += self.get_algorithm().get_next_step_size(args)

    def get_next_time(self, sensor_data=None):
        self.forward_time(sensor_data)
        return self.get_time()