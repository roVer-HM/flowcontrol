
import abc

from typing import Union, List

import numpy as np

class StepSizeAlgorithm(abc.ABC):

    def __init__(self, min_step_size = 0.4,
                 max_step_size = 60.0):
        self.current_step_size = None
        self.next_step_size = None
        self.min_step_size = min_step_size
        self.max_step_size = max_step_size

    @abc.abstractmethod
    def get_next_step_size(self, sensor_data):
        raise NotImplementedError()

    def get_bounded_time_step(self, time_step):

        if time_step > self.max_step_size:
            return self.max_step_size
        if time_step < self.min_step_size:
            return self.min_step_size
        return time_step


class VelocityBasedStepSize(StepSizeAlgorithm):

    def __init__(self, min_step_size = 0.4, max_step_size = 60.0, factor = 10.0):
        self.factor = factor # TODO ? choose realistic value
        super().__init__(min_step_size=min_step_size,
                         max_step_size= max_step_size)

    def get_step_size_for_velocity(self, velocity):
        # low velocity: jam, -> more control necessary -> choose smaller time step
        time_step_size_adaptive = self.factor*velocity
        return time_step_size_adaptive

    def get_next_step_size(self, sensor_data: Union[List[float], float]):

        velocity = self.get_min_velocity(velocity=sensor_data)
        time_step = self.get_step_size_for_velocity(velocity)
        time_step_with_bounds = self.get_bounded_time_step(time_step)

        return time_step_with_bounds


    def get_min_velocity(self, velocity: Union[List[float], float, np.array]):
        if isinstance(velocity, float):
            velocity = [velocity]
        if isinstance(velocity, np.ndarray) == False:
            velocity = np.array(velocity)

        velocity_min = velocity.min()
        return velocity_min


class DensityBasedStepSize(VelocityBasedStepSize):

    def __init__(self, min_step_size=0.4, max_step_size=60.0, factor=10.0):
        super().__init__(min_step_size=min_step_size,
                         max_step_size=max_step_size,
                         factor=factor)

    def get_next_step_size(self, sensor_data: Union[List[float], float]):
        velocities = self.map_density_to_velocity(densities=sensor_data)
        return super().get_next_step_size(velocities)

    def map_density_to_velocity(self, densities):

        if isinstance(densities, float):
            densities = [densities]

        densities = np.array(densities)
        v0 = 1.34 # free-flow walking speed
        rho_jam = 5.4 # pedestrian density max

        # Kladec formula, Weidmann parameters
        velocities = v0*(1-np.exp(-1.913*(1/densities - 1/rho_jam)))
        return velocities




