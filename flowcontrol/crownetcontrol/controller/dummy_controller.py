import abc
import pprint

from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.crownetcontrol.traci.connection_manager import ServerModeConnection, ClientModeConnection, TraCiManager
from flowcontrol.crownetcontrol.traci.subsciption_listners import VaderePersonListener


class Controller:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.con_manager = None

    @abc.abstractmethod
    def initialize_connection(self, connection):
        pass

    def start_controller(self):
        if self.con_manager is None:
            raise RuntimeError("Controller has not working connection")
        self.con_manager.start()

    @abc.abstractmethod
    def handle_sim_step(self, sim_time, sim_state, traci_client):
        pass

    @abc.abstractmethod
    def handle_init(self, sim_time, sim_state, traci_client):
        pass


