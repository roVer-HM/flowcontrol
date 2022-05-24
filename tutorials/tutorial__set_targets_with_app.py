import os, sys

from flowcontrol.crownetcontrol.setup.entrypoints import get_controller_from_args
from flowcontrol.crownetcontrol.state.state_listener import VadereDefaultStateListener
from flowcontrol.crownetcontrol.controller import Controller
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.utils.misc import get_scenario_file

from flowcontrol.strategy.controlaction import InformationStimulus, Circle, StimulusInfo, Location, Rectangle

from flowcontrol.strategy.timestepping.timestepping import FixedTimeStepper




class CorridorChoiceExample(Controller):
    def __init__(self):
        self.redirection_area = Circle(radius=100) #
        self.current_target = 3
        super().__init__(time_stepper=FixedTimeStepper(start_time=4.0, end_time=4.0))


    def get_stimulus_info(self, target):

        location = Location(areas=self.redirection_area)
        recommendation = InformationStimulus(f"use target [{target}]")
        s = StimulusInfo(location=location, stimuli=recommendation)
        return s


    def handle_sim_step(self, sim_time, sim_state):

        s = self.get_stimulus_info(target=3)
        print(s.toJSON())
        self.con_manager.domains.v_sim.send_control(message=s.toJSON())
        self.time_stepper.forward_time()

    def handle_init(self, sim_time, sim_state):
        super().handle_init(sim_time, sim_state)
        self.con_manager.domains.v_sim.init_control()


if __name__ == "__main__":

    if len(sys.argv) == 1:
        settings = [
            "--port",
            "9999",
            "--host-name",
            "localhost",
            "--client-mode",
            "--start-server",
            "--gui-mode",
            "--output-dir",
            os.path.splitext(os.path.basename(__file__))[0],
            "--download-jar-file",  # remove this if you prefer to build vadere locally
        ]
    else:
        settings = sys.argv[1:]

    settings.extend(["--scenario-file", get_scenario_file("scenarios/test001.scenario")])

    # Tutorial 3:

    # Scenario: there are two targets.
    # Control action: change the agents' targets over time using a navigation app.
    # Communication channel: navigation app (no delay, information arrives immediately)
    # Reaction behavior: agents react with a probability 50%-100%

    # Take-away from this tutorial
    # - learn how to disseminate information using a navigation app

    # Before you start:
    # Make sure that the system variable VADERE_PATH=/path/to/vadere-repo/ is defined (e.g. add it to your configuration).

    sub = VadereDefaultStateListener.with_vars(
        "persons",
        {"pos": tc.VAR_POSITION, "speed": tc.VAR_SPEED, "angle": tc.VAR_ANGLE},
        init_sub=True,
    )

    controller = CorridorChoiceExample()

    controller = get_controller_from_args(
        working_dir=os.getcwd(), args=settings, controller=controller
    )

    controller.register_state_listener("default", sub, set_default=True)
    controller.start_controller()
