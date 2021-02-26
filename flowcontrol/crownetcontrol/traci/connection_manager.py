import logging
import warnings
from typing import Union

from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.crownetcontrol.traci.connection import _create_accept_server_socket, WrappedTraCIConnection, \
    DomainHandler, BaseTraCIConnection, _create_client_socket
from flowcontrol.crownetcontrol.traci.exceptions import FatalTraCIError, TraCISimulationEnd
from flowcontrol.crownetcontrol.traci.subsciption_listners import SubscriptionListener, VaderePersonListener


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

    def register_subscription_listener(self, name, listener: SubscriptionListener, set_default=False):
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


class ClientModeConnection(TraCiManager):

    def __init__(self, control_handler, host="127.0.0.1", port=9999):
        super().__init__(host, port, control_handler)
        self._set_connection(BaseTraCIConnection(_create_client_socket()))
        self._con._socket.connect((host, port))

    def _simulation_step(self, step=0.0):
        """
        Make a simulation step and simulate up to the given second in sim time.
        If the given value is 0 or absent, exactly one step is performed.
        Values smaller than or equal to the current sim time result in no action.
        """
        if type(step) is int and step >= 1000:
            warnings.warn(
                "API change now handles step as floating point seconds", stacklevel=2
            )
        result = self._con.send_cmd(tc.CMD_SIMSTEP, None, None, "D", step)
        return self._parse_subscription_result(result)

    def _initialize(self, *arg, **kwargs):
        # init
        # send file

        # default subscriptions
        print("register default subscriptions")
        for listener in self._con.subscriptionListener:
            listener.subscribe(self.domains)
        self._con.notify_subscription_listener()
        if len(self._default_sub.new_pedestrian_ids) > 0:
            print(f"new pedestrians found {self._default_sub.new_pedestrian_ids}. Subscribe pedestrians variables")
            self._default_sub.update_pedestrian_subscription(self.domains.v_person)
        self._con.notify_subscription_listener()

        # call controller callback
        self._control_hdl.handle_init(self._default_sub.time, self.sub_listener, self._base_client)

    def _run(self):
        while self._running:
            self._simulation_step(self._sim_until)
            # no response required for ClientModeConnection
            self._handle_sim_step()
            # clear connection state (for ClientModeConnection _con == _base_client)
            self._con.clear()

    def _handle_sim_step(self):
        # subscription listener already notified. Use default listener to update
        # subscription of new/removed pedestrians because we are the only client
        # and must mange the subscription here.
        self._default_sub.update_pedestrian_subscription(self.domains.v_person)
        self._con.notify_subscription_listener()

        # set current time
        self.current_time = self._default_sub.time

        # self.sub_listener contains state for controller
        self._control_hdl.handle_sim_step(self._default_sub.time, self.sub_listener, self._base_client)

        # no result expected. Controller should use base_client to trigger control action
        return None


class ServerModeConnection(TraCiManager):

    def __init__(self, control_handler, host="127.0.0.1", port=9997):
        super().__init__(host, port, control_handler)
        self.server_port = -1

    def _initialize(self, *arg, **kwargs):
        data = kwargs["data"]
        self._control_hdl.handle_init(self._default_sub.time, self.sub_listener, self._base_client)
        return b"ACK/NACK"

    def _run(self):
        while self._running:
            # wait for command
            action, data = self._con.recv_control()

            if action == "init":
                # response: simple act
                # data contains scenario files and omnetpp init.
                response = self._initialize(data=data)
            elif action == "sim_step":
                # data contains subscription result
                subscription_result = self._base_client.parse_subscription_result(data)
                # response: None
                self._handle_sim_step(subscription_result)
                response = b"ACK/NACK"
            else:
                raise FatalTraCIError("unknown command")

            if response is not None:
                # todo
                self._con.send_control_response(response, "bar")

            # clear state
            self._base_client._string = bytes()
            self._base_client._queue = []

        self._con.close()
        logging.info("connection closed.")

    def start(self):
        try:
            # Connection is controlled by OMNeT++ move _initialize() into _run()
            _, _socket, _, _server_port = _create_accept_server_socket(self.host, self.port)
            self._set_connection(WrappedTraCIConnection(_socket))
            self.server_port = _server_port

            self._running = True
            self._run()
        except NotImplementedError as e:
            print(e)
        finally:
            self._cleanup()
