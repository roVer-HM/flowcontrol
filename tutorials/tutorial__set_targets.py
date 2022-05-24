import os, sys

from flowcontrol.crownetcontrol.setup.entrypoints import get_controller_from_args
from flowcontrol.crownetcontrol.state.state_listener import VadereDefaultStateListener
from flowcontrol.crownetcontrol.controller import Controller
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.utils.misc import get_scenario_file

from flowcontrol.crownetcontrol.controller import Controller
from flowcontrol.crownetcontrol.traci import constants_vadere as tc


PRECISION = 8

from flowcontrol.strategy.controller.control_algorithm import AlternateTargetAlgorithm
from flowcontrol.strategy.timestepping.timestepping import FixedTimeStepper

class PingPong(Controller):
    def __init__(self):
        super().__init__(control_algorithm=AlternateTargetAlgorithm(alternate_targets=[2, 3]),
            time_stepper=FixedTimeStepper(time_step_size=4.0, start_time=4.0, end_time=30.0))

    def handle_sim_step(self, sim_time, sim_state):

        print(f"TikTokController: {sim_time} apply control action ")
        target_id = self.control_algorithm.get_next_target()


        aa =  self.con_manager.domains.v_person.get_id_list()

        for ped_id in aa: #["1", "2", "3", "4"]:
            self.con_manager.domains.v_person.set_target_list(
                str(ped_id), [str(target_id)]
            )
        self.time_stepper.forward_time()

if __name__ == "__main__":

    if len(sys.argv) == 1:
        settings = [
            "--port",
            "9999",
            "--host-name",
            "localhost",
            "--client-mode",
            "--start-server",
            "--controller-type",
            "PingPong",
            "--gui-mode",
            "--output-dir",
            os.path.splitext(os.path.basename(__file__))[0],
            "-j",
            "vadere-server.jar" # run download_vadere.py first
        ]


    else:
        settings = sys.argv[1:]

    settings.extend(["--scenario-file", get_scenario_file("scenarios/test001.scenario")])

    # Tutorial 1:

    # Scenario: there are two targets.
    # Control action: change the agents' targets over time.
    # Communication channel: none (agents get informed immediately)
    # Reaction behavior: none (all agents react immediately)

    # Take-away from this tutorial
    # - learn how to define a simple controller

    sub = VadereDefaultStateListener.with_vars(
        "persons",
        {"pos": tc.VAR_POSITION, "speed": tc.VAR_SPEED, "angle": tc.VAR_ANGLE},
        init_sub=True,
    )

    controller = get_controller_from_args(working_dir=os.getcwd(), args=settings)

    controller.register_state_listener("default", sub, set_default=True)
    controller.start_controller()
