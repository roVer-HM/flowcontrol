from flowcontrol.crownetcontrol.traci.connection import Controller, ClientModeConnection
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
import logging

from flowcontrol.crownetcontrol.traci.subsciption_listners import VaderePersonListener


def server_test():
    subListner = VaderePersonListener.with_vars("persons", {"pos": tc.VAR_POSITION, "target_list": tc.VAR_TARGET_LIST})
    controller = Controller.build_client_mode()
    s: ClientModeConnection = controller.connection
    s._con.add_sub_listener(subListner)
    s.domains.v_person.subscribe(objectID="-1", varIDs=[tc.VAR_ID_LIST, ])
    s.domains.v_sim.subscribe(objectID="-1", varIDs=[tc.VAR_TIME, tc.VAR_DEPARTED_PEDESTRIAN_IDS,
                                                     tc.VAR_ARRIVED_PEDESTRIAN_PEDESTRIAN_IDS])
    s._con.notify_subscription_listener()
    print(subListner.data)
    subListner.update_pedestrian_subscription(s.domains.v_person)
    s._con.notify_subscription_listener()
    print(subListner.data)
    # s.domains.v_person.subscribe(objectID="1", varIDs=[tc.VAR_POSITION, tc.VAR_TARGET_LIST])
    # s.domains.v_person.subscribe(objectID="2", varIDs=[tc.VAR_POSITION, tc.VAR_TARGET_LIST])
    # s.domains.v_person.subscribe(objectID="3", varIDs=[tc.VAR_POSITION, tc.VAR_TARGET_LIST])
    # s.domains.v_person.subscribe(objectID="4", varIDs=[tc.VAR_POSITION, tc.VAR_TARGET_LIST])

    sub_result = s._simulation_step(2.0)
    controller.start_controller()


if __name__ == "__main__":
    # main()
    logging.getLogger().setLevel(logging.INFO)
    server_test()
