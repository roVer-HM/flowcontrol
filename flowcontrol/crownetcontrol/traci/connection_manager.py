import argparse
from typing import Union

from flowcontrol.crownetcontrol.traci.clientmode import VadereClientModeConnection
from flowcontrol.crownetcontrol.traci.connection import (
    DomainHandler,
    BaseTraCIConnection,
)
from flowcontrol.crownetcontrol.traci.exceptions import (
    TraCISimulationEnd,
)
from flowcontrol.crownetcontrol.traci.servermode import ServerModeConnection
from flowcontrol.crownetcontrol.traci.subsciption_listners import (
    SubscriptionListener,
    VaderePersonListener,
)


def parse_args_as_dict(args=None):
    # parse arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-n",
        "--host-name",
        dest="host_name",
        default="localhost",  # TODO: discuss -> defaults
        required=True,
        help="If vadere is set, the controller is started in client-mode",
    )

    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        default=9999,
        required=True,
        help="Client: 9999, server: 9997?",
        type=int,
    )

    parser.add_argument(
        "--client-mode",
        dest="is_in_client_mode",
        action="store_true",
        default=False,
        required=False,
        help="Additional information.",  # TODO: redundant?
    )

    parser.add_argument(
        "--gui-mode",
        dest="gui_mode",
        action="store_true",
        default=False,
        required=False,
        help="Only available when server is started automatically.",
    )

    parser.add_argument(
        "--start-server",
        dest="start_server",
        action="store_true",
        default=False,
        required=False,
        help="Only available when server is started automatically.",
    )
    parser.add_argument(
        "-s",
        "--scenario",
        dest="scenario_file",
        default="",  # TODO: discuss -> defaults
        required=False,
        help="Only available in client-mode.",
    )


    if args is None:
        ns = vars(parser.parse_args())
    else:
        ns = vars(parser.parse_args(args))

    if ns["start_server"] is True and ns["is_in_client_mode"] is False:
        raise ValueError(
            "Start server option is only available in client-mode. Set --client-mode option."
        )

    if ns["start_server"] is False and ns["gui_mode"] is True:
        raise ValueError(
            "Gui mode is only available if the server is started automatically. Set --start-server option."
        )

    if ns["start_server"] is True and ns["scenario_file"] is None:
        raise ValueError("Please provide scenario file.")

    if ns["is_in_client_mode"] is True and ns["scenario_file"] is None:
        raise ValueError("Please provide scenario file.")

    return ns


class TraCiManager:
    def __init__(self, host, port, control_handler):
        self.host = host
        self.port = port
        self._running = False
        self._control_hdl = control_handler
        self.domains: DomainHandler = DomainHandler()
        self.sub_listener = {}
        self.current_time = -1
        self._sim_until = -1
        self._default_sub: Union[None, VaderePersonListener] = None

    def _set_connection(self, connection):
        self._con = connection
        self._base_client: BaseTraCIConnection = self._con
        self.domains.register(self._base_client)

    def next_call_in(self, step=-1):
        if step <= 0:
            self._sim_until = -1
        else:
            self._sim_until = self.current_time + step

    def next_call_at(self, step=-1):
        if step <= 0:
            self._sim_until = -1
        else:
            self._sim_until = step

    def register_subscription_listener(
        self, name, listener: SubscriptionListener, set_default=False
    ):
        self.sub_listener[name] = listener
        if set_default:
            self._default_sub = listener

    def unregister_subscription_listener(self, name):
        if name in self.sub_listener:
            del self.sub_listener[name]

    def _init_sub_listener(self):
        for name, listener in self.sub_listener.items():
            print(f"register listener {name}")
            self._con.add_sub_listener(listener)

    def _initialize(self, *arg, **kwargs):
        pass

    def _parse_subscription_result(self, result):
        for subscriptionResults in self._con.subscriptionMapping.values():
            subscriptionResults.reset()
        num_subs = result.readInt()
        responses = []
        while num_subs > 0:
            responses.append(self._con.read_subscription(result))
            num_subs -= 1
        self._con.notify_subscription_listener()
        return responses

    def _handle_sim_step(self):
        pass

    def _run(self):
        pass

    def _cleanup(self):
        pass

    def start(self):
        try:
            self._init_sub_listener()
            self._initialize()
            self._running = True
            self._run()
        except NotImplementedError as e:
            print(e)
        except TraCISimulationEnd as sim_end:
            print("Simulation end reached.")
        finally:
            self._cleanup()


class ControlTraciWrapper:
    @classmethod
    def get_controller_from_args(cls, working_dir, args=None, controller=None):
        ns = parse_args_as_dict(args)

        if (
            ns["port"] == 9999
            and ns["is_in_client_mode"]
        ):
            return VadereClientModeConnection(
                control_handler=controller,
                port=ns["port"],
                is_start_server=ns["start_server"],
                is_gui_mode=ns["gui_mode"],
                scenario=ns["scenario_file"],
                host=ns["host_name"]
            )
        elif (
            ns["host_name"] == "omnet"
            and ns["port"] == 9997 #TODO check port number
            and not ns["is_in_client_mode"]
        ):
            return ServerModeConnection(control_handler=controller, port=ns["port"])
        else:
            raise NotImplementedError("Port and host configuration not found.")
