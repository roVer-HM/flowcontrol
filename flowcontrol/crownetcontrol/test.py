from flowcontrol.crownetcontrol.controller.dummy_controller import Controller, TikTokController
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
import logging

from flowcontrol.crownetcontrol.traci.connection_manager import ClientModeConnection
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
    sub = VaderePersonListener.with_vars("persons", {"pos": tc.VAR_POSITION, "target_list": tc.VAR_TARGET_LIST})
    controller = TikTokController()
    traci_manager = ClientModeConnection(control_handler=controller, port=9999)
    controller.initialize_connection(traci_manager)
    controller.start_controller()




if __name__ == "__main__":
    # main()
    logging.getLogger().setLevel(logging.INFO)
    server_test()
