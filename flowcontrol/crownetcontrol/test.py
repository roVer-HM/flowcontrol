import os
import sys

from flowcontrol.crownetcontrol.controller.dummy_controller import (
    Controller,
    TikTokController,
)
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
import logging

from flowcontrol.crownetcontrol.traci.connection_manager import (
	ControlTraciWrapper,
	ClientModeConnection)
from flowcontrol.crownetcontrol.traci.subsciption_listners import VaderePersonListener


# @classmethod
# def build_server_mode(cls, host="localhost", port=9997):
#     ctr = cls()
#     connection = ServerModeConnection(control_handler=ctr, host=host, port=port)
#     ctr.connection = connection
#     return ctr
#
#
# @classmethod
# def build_client_mode(cls, host="localhost", port=9999):
#     ctr = cls()
#     connection = ClientModeConnection(control_handler=ctr, host=host, port=port)
#     ctr.connection = connection
#     return ctr


def server_test():
    sub = VaderePersonListener.with_vars(
        "persons", {"pos": tc.VAR_POSITION, "target_list": tc.VAR_TARGET_LIST}
    )
    controller = TikTokController()
    traci_manager = ClientModeConnection(control_handler=controller, port=9999)
    controller.initialize_connection(traci_manager)
    controller.start_controller()


def server_test_2():
    # TODO start vadere manually, but do handle inifile
    sub = VaderePersonListener.with_vars(
        "persons", {"pos": tc.VAR_POSITION, "target_list": tc.VAR_TARGET_LIST}
    )
    controller = TikTokController()

    if len(sys.argv) == 1:
        settings = [
            "--port",
            "9999",
            "--host-name",
            "vadere",
            "--client-mode"
        ]

        traci_manager = ControlTraciWrapper.get_controller_from_args(
            working_dir=os.getcwd(), args=settings, controller=controller)
    else:
        traci_manager = ControlTraciWrapper.get_controller_from_args(
            working_dir=os.path.dirname(os.path.abspath(__file__)),
            controller=controller)

    controller.initialize_connection(traci_manager)
    controller.start_controller()

def server_test_3_start_vadere():

    scenario_file = os.path.join(os.environ["VADERE_PATH"], "Scenarios/Demos/roVer/scenarios/scenario002.scenario")

    sub = VaderePersonListener.with_vars(
        "persons", {"pos": tc.VAR_POSITION, "target_list": tc.VAR_TARGET_LIST}
    )
    controller = TikTokController()

    if len(sys.argv) == 1:
        settings = [
            "--port",
            "9999",
            "--host-name",
            "vadere",
            "--client-mode",
            "--start-server",
            "--gui-mode",
            "--scenario",
            scenario_file
        ]

        traci_manager = ControlTraciWrapper.get_controller_from_args(
            working_dir=os.getcwd(), args=settings, controller=controller)
    else:
        traci_manager = ControlTraciWrapper.get_controller_from_args(
            working_dir=os.path.dirname(os.path.abspath(__file__)),
            controller=controller)

    controller.initialize_connection(traci_manager)
    controller.start_controller()


def server_test_4_start_vadere():

    scenario_file = os.path.join(os.environ["VADERE_PATH"], "Scenarios/Demos/roVer/scenarios/scenario002.scenario")

    sub = VaderePersonListener.with_vars(
        "persons", {"pos": tc.VAR_POSITION, "target_list": tc.VAR_TARGET_LIST}
    )
    controller = TikTokController()

    if len(sys.argv) == 1:
        settings = [
            "--port",
            "9999",
            "--host-name",
            "vadere",
            "--client-mode",
            "--scenario",
            scenario_file
        ]

        traci_manager = ControlTraciWrapper.get_controller_from_args(
            working_dir=os.getcwd(), args=settings, controller=controller)
    else:
        traci_manager = ControlTraciWrapper.get_controller_from_args(
            working_dir=os.path.dirname(os.path.abspath(__file__)),
            controller=controller)

    controller.initialize_connection(traci_manager)
    controller.start_controller()


if __name__ == "__main__":
    # main()
    logging.getLogger().setLevel(logging.INFO)
    #server_test()
    #server_test_2()
    server_test_4_start_vadere()
    print()
