import abc
from typing import List, Union

import numpy as np


class ControlAlgorithm(abc.ABC):
    pass


class RouteRecommenderAlgorithm(ControlAlgorithm):

    def __init__(self, alternate_targets: List[int]):
        self.set_targets(alternate_targets)

    def set_targets(self, targets : List[int] ):
        if len(set(targets)) != len(targets):
            raise ValueError(f"Duplicate targets found: {targets}.")
        self.targets = targets



class AlternateTargetAlgorithm(RouteRecommenderAlgorithm):

    def __init__(self, alternate_targets: List[int], first_target_index=0):
        self.first_target_index = first_target_index
        self.count = None
        super().__init__(alternate_targets)

    def iterate_through_targets(self):
        if self.count < len(self.targets) - 1:
            self.count += 1
        else:
            self.count = 0

    def get_next_target(self):
        if self.count == None:
            self.count = self.first_target_index
        else:
            self.iterate_through_targets()
        return self.targets[self.count]

class MinimalDensityAlgorithm(RouteRecommenderAlgorithm):

    def __init__(self, alternate_targets, is_prefer_short_routes = True):
        # alternate targets: list of routes in ascending route length
        self.is_prefer_short_routes = is_prefer_short_routes
        super().__init__(alternate_targets)


    def get_next_target(self, densities : Union[List[float], np.ndarray, float]):

        if isinstance(densities, float):
            densities = [densities]
        if isinstance(densities, np.ndarray) == False:
            densities = np.array(densities)

        self.check_densities(densities)

        indices = np.argwhere(densities == densities.min()).ravel()
        route_index = self.get_index(indices)

        return self.targets[route_index]


    def get_index(self, indices):

        if len(indices) == 1:
            return indices[0]
        elif len(indices) > 1:
            i = self.get_index_in_case_of_multiple_routes()
            return indices[i]
        else:
            raise ValueError("No minimal route found.")


    def get_index_in_case_of_multiple_routes(self):
        if self.is_prefer_short_routes:
            return 0
        else:
            return -1

    def check_densities(self, densities):

        if len(densities) != len(self.targets):
            raise ValueError(f"Number of elements in densities={densities} not equal to number of elements in target list={self.targets}.")

        if densities.min() < 0.0:
            raise ValueError(f"Density must not be smaller zero. Got densities: {densities}.")
