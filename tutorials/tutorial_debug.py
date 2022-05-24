import os

from flowcontrol.crownetcontrol.setup.entrypoints import get_controller_from_args
from flowcontrol.crownetcontrol.state.state_listener import VadereDefaultStateListener
from flowcontrol.crownetcontrol.controller import Controller
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.utils.misc import get_scenario_file


class PingPong(Controller):
    def __init__(self):
        super().__init__()
        self.control = [
            (5.0, ["3"]),
            (10, ["2"]),
            (15, ["3"]),
            (20, ["2"]),
            (25, ["3"]),
            (30, ["2"]),
        ]
        self.count = 0

    def handle_sim_step(self, sim_time, sim_state):
        if self.count > len(self.control)-1:
            return
        print(f"TikTokController: {sim_time} handle_sim_step evaluate control...")

        print(f"TikTokController: {sim_time} apply control action ")
        for ped_id in ["1", "2", "3", "4"]:
            self.con_manager.domains.v_person.set_target_list(
                str(ped_id), self.control[self.count][1]
            )

        self.count += 1

    def set_next_step_time(self):
        if self.count <= len(self.control) - 1:
            self.con_manager.next_call_at(self.control[self.count][0])
        else:
            self.con_manager.next_call_at(100) # simulation end

if __name__ == "__main__":

    settings = ["--port",
                "9999",
                "--host-name",
                "localhost",
                "--client-mode",
                "--scenario-file",
                get_scenario_file("scenarios/test001.scenario")
                ]

    # Content, see Tutorial 1:

    # Take-away from this tutorial
    # - learn how to debug

    # Open the vadere repository in an IDE and configure the Vadere Manager (org.vadere.manager.Manager):
    # Pass following arguments to the Vadere Manager
    # "--loglevel TRACE --single-client --gui-mode --port 9999"
    # Set a breakpoint in the method 'process_setTargetList' (org.vadere.manager.traci.commandHandler.PersonCommandHandler)

    # Debugging:
    # Vadere IDE: Run org.vadere.manager.Manager in debug mode.
    # In this IDE: Run this main (mode=debug/run).

    sub = VadereDefaultStateListener.with_vars(
        "persons",
        {"pos": tc.VAR_POSITION, "speed": tc.VAR_SPEED, "angle": tc.VAR_ANGLE},
        init_sub=True,
    )

    controller = PingPong()

    controller = get_controller_from_args(
        working_dir=os.getcwd(), args=settings, controller=controller
    )

    controller.register_state_listener("default", sub, set_default=True)
    controller.start_controller()
