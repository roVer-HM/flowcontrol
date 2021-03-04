from pythontraciwrapper.py4j_client import Py4jClient
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


from abc import ABCMeta, abstractmethod
import pandas as pd

import os


class SimulationModel(metaclass=ABCMeta):
    def __init__(
        self,
        VADERE_PATH,
        project_path,
        scenario_name=None,
        start_server=True,
        debug=True,
    ):

        if scenario_name is not None:
            self.scenario_name = scenario_name

        self.model = Py4jClient.create(
            project_path=os.path.join(VADERE_PATH, project_path),
            vadere_base_path=VADERE_PATH,
            start_server=start_server,
            debug=debug,
        )
        self.model.entrypoint_jar = (
            f"{VADERE_PATH}/VadereManager/target/vadere-traci-entrypoint.jar"
        )

        self._start_scenario()

    def _start_scenario(self, scenario_name=None):

        if scenario_name is None:
            scenario_name = self.scenario_name
        self.model.startScenario(scenarioName=scenario_name)

    def get_peds(self):
        return self.model.pers

    def get_control(self):
        return self.model.ctr

    def get_ped_positions(self):
        positions = self.model.pers.getPosition2DList()
        p0 = pd.DataFrame(positions).transpose()
        return p0

    def reset_positions_to(self, positions: pd.DataFrame):

        for index, row in positions.iterrows():
            row = row.to_numpy()
            self.model.pers.setPosition2D(index, str(row[0]), str(row[1]))

    def simulate_until(self, time):

        if not isinstance(time, list):
            time = [time]

        for t in time:
            self.model.ctr.nextStep(t)

    @abstractmethod
    def get_objective(self, state):
        raise NotImplemented


class CorridorChoice(SimulationModel):
    def __init__(self, VADERE_PATH, project_path, **kwargs):
        self.polygon = None
        super().__init__(VADERE_PATH, project_path, **kwargs)

    def get_objective(self, state):

        if self.polygon is None:
            self.polygon = Polygon(self.model.poly.getShape("1000"))

        counter = 0
        for index, row in state.iterrows():
            row = row.to_numpy()
            point = Point(row[0], row[1])
            if self.polygon.contains(point):
                counter += 1

        density = counter  # / self.polygon.area

        return density
