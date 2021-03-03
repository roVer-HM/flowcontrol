from flowcontrol.crownetcontrol.controller.dummy_controller import Controller, TikTokController
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
import logging

from flowcontrol.crownetcontrol.traci.connection_manager import ClientModeConnection, ServerModeConnection
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


def client_mode():
    controller = TikTokController()
    traci_manager = ClientModeConnection(control_handler=controller, host="vadere", port=9999)
    controller.initialize_connection(traci_manager)
    controller.start_controller()


def server_mode():
    controller = TikTokController()
    traci_manager = ServerModeConnection(control_handler=controller, host="0.0.0.0", port=9997)
    controller.initialize_connection(traci_manager)
    controller.start_controller()




if __name__ == "__main__":
    # main()
    logging.getLogger().setLevel(logging.INFO)
    # client_mode()
    server_mode()
