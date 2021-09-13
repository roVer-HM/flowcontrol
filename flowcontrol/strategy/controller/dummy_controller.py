import abc
import pprint
import sys
import os
import shutil

from flowcontrol.dataprocessor.dataprocessor import Manager


class Controller:
    __metaclass__ = abc.ABCMeta


    def __init__(self):
        self.commandID = 0
        self.con_manager = None
        self.sensor_time_step_size = None
        self.processor_manager = Manager()
        self.output_dir = None
        self.next_call = None

    def initialize_connection(self, con_manager):
        self.con_manager = con_manager

    def start_controller(self, *kw, **kwargs):
        if self.con_manager is None:
            raise RuntimeError("Controller has not working connection")
        self.con_manager.start(*kw, **kwargs)

    def register_state_listener(self, name, listener, set_default=False):
        # set_default = True if omnet is present
        self.con_manager.register_state_listener(name, listener, set_default)

    def set_simulation_config_dynamically(self):
        self.set_output_dir(os.path.dirname(self.con_manager.domains.v_sim.get_output_directory()))
        self.sensor_time_step_size = self.con_manager.domains.v_sim.get_sim_ste()

    def set_next_step_time(self):
        if self.next_call is None:
            self.next_call = self.sensor_time_step_size
        else:
            self.next_call += self.sensor_time_step_size
        self.con_manager.next_call_at(self.next_call)

    @abc.abstractmethod
    def handle_sim_step(self, sim_time, sim_state):
        pass

    @abc.abstractmethod
    def handle_init(self, sim_time, sim_state):
        pass

    @classmethod
    def get(cls, controller_type):

        controllers = [c for c in cls.__subclasses__() if c().__class__.__name__ == controller_type]
        if len(controllers) == 0:
            raise ValueError(f"Controller of type {controller_type} not found. Make sure that the controller is placed in the main script or is part of the flowcontrol simulator.")
        if len(controllers) > 1:

            controllers = [c for c in controllers if c().__module__ == "__main__"]
            if len(controllers) == 1:
                print(f"Warning: Multiple controllers of type {controller_type} found. Use controller defined in {sys.argv[0]}.")

        return controllers[0]()

    def postprocess_sim_results(self):
        self.write_data()

    def write_data(self):
        pass

    def set_output_dir(self, parent_folder):
        if os.path.isdir(parent_folder):
            output_dir = os.path.join(parent_folder, "flowcontrol.d")
            if os.path.isdir(output_dir):
                shutil.rmtree(output_dir, ignore_errors=True)
            os.mkdir(output_dir)
        else:
            raise ValueError("Output directory structure not provided.")
        self.output_dir = output_dir


class TikTokController(Controller):
    def __init__(self):
        super().__init__()
        self.control = [
            (0, ["2"]),
            (5.0, ["3"]),
            (10, ["2"]),
            (15, ["3"]),
            (20, ["2"]),
            (25, ["3"]),
            (30, ["2"]),
        ]
        self.count = 0

    def initialize_connection(self, con_manager):
        self.con_manager = con_manager

    def handle_sim_step(self, sim_time, sim_state):
        if self.count >= len(self.control):
            return
        print(f"TikTokController: {sim_time} handle_sim_step evaluate control...")

        print(f"TikTokController: {sim_time} apply control action ")
        for ped_id in ["1", "2", "3", "4"]:
            self.con_manager.domains.v_person.set_target_list(
                str(ped_id), self.control[self.count][1]
            )
        # read if listeners are used

        self.con_manager.next_call_at(self.control[self.count][0])
        self.count += 1

    def handle_init(self, sim_time, sim_state):
        print("TikTokController: handle_init")
        self.con_manager.next_call_at(0.0)
        pprint.pprint(sim_state)
