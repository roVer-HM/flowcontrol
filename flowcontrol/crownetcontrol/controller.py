import abc
import os
import shutil
import sys

from flowcontrol.dataprocessor.dataprocessor import Manager
from flowcontrol.strategy.controller.control_algorithm import ControlAlgorithm
from flowcontrol.strategy.timestepping.timestepping import TimeStepper


class Controller:

    def __init__(self,
                 control_algorithm : ControlAlgorithm = None,
                 time_stepper : TimeStepper = None,
                 processor_manager : Manager = None,
                 ):
        self.con_manager = None
        self.output_dir = None
        self.next_call = None
        self.processor_manager = processor_manager
        self.control_algorithm = control_algorithm
        self.time_stepper = time_stepper
        self.commandID = 0

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
        self.set_stepping_behavior()

    def set_stepping_behavior(self):
        #TODO check here
        step_size = self.con_manager.domains.v_sim.get_time()



        #if self.time_stepper.get_time() < start_time:
            #
        #pass
            #raise ValueError(f"Start time of the time stepper must be > step size = {start_time}s.")
        print()


    def set_next_step_time(self, *args):

        next_call = self.time_stepper.get_time()
        self.time_stepper.forward_time(*args)
        self.con_manager.next_call_at(next_call)

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
        print(f"Set flowcontrol output directory to {self.output_dir}")

    def set_step_xyv(self, *args):
        time = self.time_stepper.get_next_time(args)
        self.con_manager.next_call_at(time)