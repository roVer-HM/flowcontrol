from flowcontrol.crownetcontrol.traci.connection import Client, start_server
from flowcontrol.crownetcontrol.traci.VadereMiscAPI import VadereMiscAPI
from flowcontrol.crownetcontrol.traci.VaderePersonAPI import VaderePersonAPI
import logging

def main():
    p = VaderePersonAPI()
    p2 = VadereMiscAPI()
    client = Client(port=9999, default_domains=[p, p2])
    p = client.v_person
    ret = p.get_target_list("1")
    ret = client.simulationStep(5.0)
    print("hi")


def server_test():
    s = start_server()


if __name__ == "__main__":
    # main()
    logging.getLogger().setLevel(logging.INFO)
    server_test()
