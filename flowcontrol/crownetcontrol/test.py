from flowcontrol.crownetcontrol.traci import Client
from flowcontrol.crownetcontrol.traci.VaderePersonAPI import VaderePersonAPI


def main():
    p = VaderePersonAPI()
    client = Client(port=9999, default_domains=[p])
    p = client.v_person
    ret = p.get_target_list("1")
    ret = client.simulationStep(5.0)
    print("hi")

if __name__ == "__main__":
    main()