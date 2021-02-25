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


class TikTokController(Controller):

    def __init__(self):
        super().__init__()
        self.sub = VaderePersonListener.with_vars("persons",
                                                  {"pos": tc.VAR_POSITION, "target_list": tc.VAR_TARGET_LIST},
                                                  init_sub=True)
        self.control = [(0, ["2"]), (5.0, ["3"]), (10, ["2"]), (15, ["3"]), (20, ["2"]), (25, ["3"])]
        self.count = 0

    def initialize_connection(self, con_manager):
        self.con_manager = con_manager
        self.con_manager.register_subscription_listener("vadere1", self.sub, set_default=True)

    def handle_sim_step(self, sim_time, sim_state, traci_client):
        if self.count > len(self.control):
            return
        print(f"TikTokController: {sim_time} handle_sim_step evaluate control...")

        print(f"TikTokController: {sim_state} apply control action ")
        for ped_id in self.sub.pedestrian_id_list:
            self.con_manager.domains.v_person.set_target_list(str(ped_id), self.control[self.count][1])

        self.con_manager.next_call_at(self.control[self.count][0])
        self.count += 1

    def handle_init(self, sim_time, sim_state, traci_client):
        print("TikTokController: handle_init")
        pprint.pprint(sim_state)
