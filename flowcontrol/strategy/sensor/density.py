import os
import time

import numpy as np
import pandas as pd
import shapely.ops
from shapely.geometry import Polygon, Point


working_dir = dict()
PRECISION = 8


class MeasurementArea:

    def __init__(self, id, polygon: Polygon):
        self.id = id
        self.area = polygon
        self.cell_contribution = dict()

    def get_cell_contribution(self, cells, obstacles):
        if len(self.cell_contribution) > 0:
            return self.cell_contribution

        print(f"Initialize cell contributions for measurement area with id = {self.id}.")

        for key, cell in cells.items():
            common_area = cell.polygon.intersection(self.area).area

            if common_area > 0:
                area_contribution = common_area/cell.polygon.area

                if area_contribution < 1:
                    # cell is partially in measurement area
                    count_contribution = self.get_counts_considering_obstacles(area_contribution, cell, obstacles)
                else:
                    count_contribution = 1 # cell is within measurement area

                self.cell_contribution[key] = {"area": area_contribution, "count": count_contribution}

        return self.cell_contribution

    def get_counts_considering_obstacles(self, area_contribution, cell, obstacles):

        self.check_integrity(area_contribution, cell)

        non_reachable_area = self.compute_non_reachable_area(cell, obstacles)
        non_reachable_area = non_reachable_area / cell.polygon.area
        count_contribution = np.round(area_contribution / (1 - non_reachable_area), 8)

        self.print_information(area_contribution, count_contribution, non_reachable_area, cell)

        return count_contribution

    def print_information(self, area_contribution, count_contribution, non_reachable_area, cell):
        if count_contribution > 0 and count_contribution < 1:
            print(f"Cell {cell.polygon}: ")
            print(f"{(area_contribution * 100):.1f}% of the cell is inside measurement area {self.id}.")
            print(f"{(non_reachable_area * 100):.1f}% of the cell is non-reachable (obstacles).")
            print(f"{(1 - area_contribution - non_reachable_area)*100:.1f}% of the agents ({(1 - area_contribution - non_reachable_area)*100:.1f}%) are not counted, because they are in the remaining part ({(1 - area_contribution - non_reachable_area) * 100:.1f}%) of the cell.")
            print(
                f"The count contribution is {count_contribution:.1f} (={area_contribution * 100:.1f}% / 100% - {non_reachable_area*100:.1f}%).")

    def check_integrity(self, area_contribution, cell):
        outside_area = cell.polygon.difference(self.area)
        if outside_area.area == 0 and area_contribution < 1:
            raise ValueError("The outside area must be zeto, if the cell is fully contained in the "
                             "measurement area.")

    def compute_non_reachable_area(self, cell, obstacles):
        obstacles_overlapping = [cell.polygon.intersection(obstacle) for obstacle in obstacles if
                                 cell.polygon.intersection(obstacle).area > 0]
        non_reachable_area = 0
        # make sure that obstacles area that overlap with other obstacle areas are not counted twice
        obstacles_overlapping = shapely.ops.unary_union(obstacles_overlapping)

        if obstacles_overlapping.is_empty:
            return non_reachable_area

        if isinstance(obstacles_overlapping, Polygon):
            return obstacles_overlapping.intersection(cell.polygon).area

        for obstacle_ in obstacles_overlapping.geoms:
            non_reachable_area += obstacle_.intersection(cell.polygon).area
        return non_reachable_area


class Cell:
    def __init__(self, id, polygon : Polygon, count=0):
        self.id = id
        self.polygon = polygon
        self.number_of_agents_in_cell = count

    def get_density(self):
        return self.number_of_agents_in_cell/self.polygon.area

    def get_count(self):
        return self.number_of_agents_in_cell

    def set_count(self, count):
        if not np.round(count, 6).is_integer():
            raise ValueError(f"Number of pedestrians in cell must be int values. Got {count}.")

        self.number_of_agents_in_cell = count

class DensityMapper:

    def __init__(self, cell_dimensions, cell_size, measurement_areas : dict, obstacles):
        self.cell_dimensions = cell_dimensions
        self.cell_size = cell_size
        self.cells = dict()
        self.measurement_areas = measurement_areas
        self.obstacles = obstacles

    def get_cells(self):
        if len(self.cells) > 0:
            return self.cells

        print("DensityMapper: Initialize cell grid.")

        delta_x = self.cell_size[0]
        delta_y = self.cell_size[1]

        index = 0

        for x_coor in np.arange(0, self.cell_dimensions[0])*delta_x:
            for y_coor in np.arange(0, self.cell_dimensions[1])*delta_y:
                lower_left_corner = [x_coor,y_coor]
                lower_right_corner = [x_coor+delta_x, y_coor]
                upper_right_corner = [x_coor+delta_x, y_coor+delta_y]
                upper_left_corner = [x_coor, y_coor+delta_y]
                polygon = Polygon(np.array([lower_left_corner, lower_right_corner, upper_right_corner, upper_left_corner]))
                key = self.get_cell_key(x_coor, y_coor)
                self.cells[key] = Cell(id=index, polygon=polygon)
                index += 1

        return self.cells

    def get_cell_key(self, x_coor, y_coor):
        return f"x={x_coor:.1f}_y={y_coor:.1f}"

    def get_density_in_area(self, distribution = "uniform"):

        if distribution=="uniform":
            densities = self.get_density_uniform_assumption()
        else:
            raise NotImplementedError("Not implemented yet. Use distribution type uniform.")
        return densities

    def get_density_uniform_assumption(self):

        densities = dict()
        for id, measurement_area in self.measurement_areas.items():
            area, counts = self.compute_counts_area(measurement_area)
            densities[id] = area/counts
        return densities

    def compute_counts_area(self, measurement_area : MeasurementArea):
        cell_contributions = measurement_area.get_cell_contribution(self.get_cells(), self.obstacles)

        count = 0
        unit_area = 0

        for key, weight in cell_contributions.items():
            count_raw = self.get_cells()[key].get_count()
            count += count_raw*weight["count"] # weights the counts -> if 50% of the cell area overlaps with the measurement area, the weight would be 50%
            unit_area += weight["area"]

        if not np.isclose(unit_area*self.get_cell_area(), measurement_area.area.area):
            raise ValueError(f"Measurement area computed: {unit_area*self.get_cell_area()}. Should be {measurement_area.area.area}.")

        return count, unit_area*self.get_cell_area()


    def get_cell_area(self):
        return self.cell_size[0]*self.cell_size[1]

    def update_density(self, result):
        for entry in result:
            self.update_cell(x_coor=entry[0], y_coor = entry[1], count= entry[2])

    def update_cell(self, x_coor, y_coor, count):
        cell_key = self.get_cell_key(x_coor, y_coor)

        if cell_key not in self.get_cells().keys():
            raise ValueError(f"Key {cell_key} not found.")
        self.get_cells()[cell_key].set_count(count)


class DensityMapCheck:

    @classmethod
    def _wait_until_file_exists(cls, file_path):
        while os.path.isfile(file_path) is False:
            time.sleep(1)
        time.sleep(1)
        return True

    @classmethod
    def get_cell_density_omnett_truth(cls, file_path):
        cls._wait_until_file_exists(file_path)
        globalDensityMap = pd.read_csv(
            file_path,
            delimiter=" ",
            index_col=[0],
            header=[0],
        ).sort_index(axis=1).round(PRECISION)
        globalDensityMap.index = globalDensityMap.index/0.4 # simTime to simstep
        globalDensityMap = globalDensityMap[["x", "y", "count"]]
        return globalDensityMap

    @classmethod
    def get_cell_density_vadere_truth(cls, file_path):
        cls._wait_until_file_exists(file_path)
        countsCellwiseVadere = pd.read_csv(
            file_path,
            delimiter=" ",
            index_col=[0],
        ).sort_index(axis=1).round(PRECISION)
        if (countsCellwiseVadere['size'].std() == 0) is False:
            raise ValueError("Only squares as cells allowed.")
            cell_size = countsCellwiseVadere['size'].mean()
            countsCellwiseVadere.drop(['size'], inplace=True, axis=1)
            keep = countCellwiseVadere.drop[['x', 'y']] >= 0.0
            densitiesCellWise = countsCellwiseVadere.loc[keep] / cell_size ** 2
        return densitiesCellWise