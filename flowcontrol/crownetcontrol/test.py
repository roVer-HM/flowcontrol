from flowcontrol.strategy.controller.dummy_controller import TikTokController
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
import logging

from flowcontrol.crownetcontrol.traci.connection_manager import (
    ClientModeConnection,
    ServerModeConnection,
)
from flowcontrol.crownetcontrol.state.state_listener import VadereDefaultStateListener


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


def client_mode(host = "vadere", **kwargs):
    sub = VadereDefaultStateListener.with_vars(
        "persons",
        {"pos": tc.VAR_POSITION, "target_list": tc.VAR_TARGET_LIST},
        init_sub=True,
    )
    controller = TikTokController()
    traci_manager = ClientModeConnection(
        control_handler=controller, host=host, port=9999
    )
    controller.initialize_connection(traci_manager)
    traci_manager.register_state_listener("default", sub)
    controller.start_controller(**kwargs)


def server_mode():
    sub = VadereDefaultStateListener.with_vars(
        "persons",
        {"pos": tc.VAR_POSITION, "speed": tc.VAR_SPEED, "angle": tc.VAR_ANGLE},
        init_sub=True,
    )

    controller = TikTokController()
    traci_manager = ServerModeConnection(
        control_handler=controller, host="0.0.0.0", port=9997
    )
    controller.initialize_connection(traci_manager)
    controller.register_state_listener("default", sub)
    controller.start_controller()


if __name__ == "__main__":
    # main()
    logging.getLogger().setLevel(logging.INFO)
    # client_mode()
    server_mode()
