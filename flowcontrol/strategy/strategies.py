from __future__ import print_function
from __future__ import absolute_import
import abc, argparse, logging, os

_RESULTS = {0x00: "OK", 0x01: "Not implemented", 0xFF: "Error"}


class ControlAction:
    def __init__(self, target_list, velocities=None):
        self.velocities = velocities
        self.target_list = target_list

    def get_actions(self):
        return self.__dict__.keys()


class Strategy(object):
    __metaclass__ = abc.ABCMeta

    @classmethod
    def get_from_config(cls, config):
        typ = config["strategy"]

        if config["params"]:
            params = config["params"]

        if config["destination"]:
            destination = config["destination"]

        targetclass = typ.capitalize()
        return globals()[targetclass]()

    def __init__(self, parameter, config):
        raise NotImplemented

    def update_current_state(self, position_list, velocities_list, target_list):
        self._set_positions(position_list)
        self._set_target_list(target_list)
        self._set_velocities(velocities_list)

    def _set_positions(self, position_list):
        self.positions = position_list

    def _set_velocities(self, velocities_list):
        self.velocities = velocities_list

    def _set_target_list(self, target_list):
        self.target_list = target_list

    def get_state_before_control_action(self):
        return self.positions, self.target_list, self.velocities

    def get_control_action(self, state):
        raise NotImplemented

    def compute_control_action(self, state: dict):
        raise NotImplemented

    def get_simulator_destination(self):
        raise NotImplemented


class CorridorChoice(Strategy):
    def __init__(self, parameter=None, config=None, destination="vadere"):
        self.corridors = None
        self.parameter = parameter
        self.destination = "vadere"

    def compute_control_action(self, **kwargs):

        return ControlAction(target_list=self.target_list)

    def get_simulator_destination(self):
        return self.destination


