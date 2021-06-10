import logging
import time
from threading import Thread

from typing import Union

from flowcontrol.crownetcontrol.state.state_listener import StateListener
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.crownetcontrol.traci.connection import (
    DomainHandler,
    BaseTraCIConnection,
    create_client_socket,
    create_accept_server_socket,
    WrappedTraCIConnection,
)
from flowcontrol.crownetcontrol.traci.exceptions import (
    TraCISimulationEnd,
    FatalTraCIError,
)


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
        self._default_sub: Union[None, StateListener] = None

    def _set_connection(self, connection):
        self._traci = connection
        self.domains.register(self.traci)

    @property
    def traci(self):
        if self._traci is None:
            raise RuntimeError("traci connection not set yet!")
        return self._traci

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

    def register_state_listener(self, name, listener: StateListener, set_default=False):
        self.sub_listener[name] = listener
        if set_default:
            self._default_sub = listener

    def unregister_subscription_listener(self, name):
        if name in self.sub_listener:
            del self.sub_listener[name]

    def _init_sub_listener(self):
        for name, listener in self.sub_listener.items():
            print(f"register listener {name}")
            self.traci.add_sub_listener(listener)

    def _initialize(self, *arg, **kwargs):
        pass

    def _handle_sim_step(self, *arg, **kwargs):
        pass

    def _run(self):
        pass

    def _cleanup(self):
        pass

    def start(self, *kw, **kwargs):
        raise NotImplementedError


class ClientModeConnection(TraCiManager):
    def __init__(self, control_handler, host="127.0.0.1", port=9999, server_thread = None):
        self.server_thread : Thread = server_thread

        super().__init__(host, port, control_handler)
        self._set_connection(BaseTraCIConnection(create_client_socket()))

        startTime = time.time()
        maxWaitingTime = 10.0
        connected = False
        while not connected and ((time.time() - startTime) < maxWaitingTime) is True:
            self.traci.connect(host, port)
            connected = True

    def _simulation_step(self, step=0.0):
        """
        Make a simulation step and simulate up to the given second in sim time.
        If the given value is 0 or absent, exactly one step is performed.
        Values smaller than or equal to the current sim time result in no action.
        """
        result = self.domains.v_ctrl.sim_step(step)
        self.traci.parse_subscription_result(result)
        self.traci.notify_subscription_listener()

    def _initialize(self, *arg, **kwargs):
        # init
        # send file

        # default subscriptions
        print("register default subscriptions")
        for listener in self.traci.subscriptionListener:
            listener.subscribe(self.domains)
        self.traci.notify_subscription_listener()
        if len(self._default_sub.new_pedestrian_ids) > 0:
            print(
                f"new pedestrians found {self._default_sub.new_pedestrian_ids}. Subscribe pedestrians variables"
            )
            self._default_sub.update_pedestrian_subscription(self.domains.v_person)
        self.traci.notify_subscription_listener()

        # call controller callback
        self._control_hdl.handle_init(self._default_sub.time, self.sub_listener)

    def _run(self):
        while self._running:
            self._simulation_step(self._sim_until)
            # no response required for ClientModeConnection
            self._handle_sim_step()
            # clear connection state (for ClientModeConnection _con == _base_client)
            self.traci.clear()


    def _handle_sim_step(self):
        # subscription listener already notified. Use default listener to update
        # subscription of new/removed pedestrians because we are the only client
        # and must mange the subscription here.
        self._default_sub.update_pedestrian_subscription(self.domains.v_person)
        self.traci.notify_subscription_listener()

        # set current time
        self.current_time = self._default_sub.time

        # self.sub_listener contains state for controller
        self._control_hdl.handle_sim_step(self._default_sub.time, self.sub_listener)

        # no result expected. Controller should use base_client to trigger control action
        return None

    def start(self, *kw, **kwargs):

        try:
            self.domains.v_ctrl.send_file(kwargs["file_name"], kwargs["file_content"])
            self._init_sub_listener()
            self._initialize()
            self._running = True
            self._run()
        except NotImplementedError as e:
            print(e)
        except TraCISimulationEnd:
            print("Simulation end reached.")
        finally:
            self._cleanup()

    def _cleanup(self):

        if self.server_thread.is_alive():
           print("Shut down server.")
           self.server_thread.stop()



class ServerModeConnection(TraCiManager):
    def __init__(self, control_handler, host="127.0.0.1", port=9997):
        super().__init__(host, port, control_handler)
        self.server_port = -1

    def _initialize(self, *arg, **kwargs):
        self._control_hdl.handle_init(kwargs["sim_time"], self.sub_listener)

        # send raw command  with next time_step expected
        return self.traci.build_cmd_raw(
            tc.CMD_CONTROLLER, tc.VAR_INIT, "", "d", self._sim_until
        )

    def _handle_sim_step(self, *arg, **kwargs):
        # no default subscription update. Is handled by opp client

        # set current time
        self.current_time = kwargs["sim_time"]

        # self.sub_listener contains state for controller
        self._control_hdl.handle_sim_step(kwargs["sim_time"], self.sub_listener)

        # send raw command  with next time_step expected
        return self.traci.build_cmd_raw(
            tc.CMD_CONTROLLER, tc.CMD_SIMSTEP, "", "d", self._sim_until
        )

    def _run(self):
        while self._running:
            # wait for command
            rcv = self.traci.recv_control()

            if rcv["action"] == tc.VAR_INIT:
                # response: next sim time at which to call controller
                # data contains current simtime only.
                state = self.domains.v_ctrl.sim_state(rcv["simTime"])
                self.traci.parse_subscription_result(state)
                self.traci.notify_subscription_listener()
                response = self._initialize(sim_time=rcv["simTime"])
            elif rcv["action"] == tc.CMD_SIMSTEP:
                # data contains current simtime only.
                # access current subscriptions trough tc.CMD_SIMSTATE
                state = self.domains.v_ctrl.sim_state(rcv["simTime"])
                self.traci.parse_subscription_result(state)
                self.traci.notify_subscription_listener()
                # response: : next sim time at which to call controller
                response = self._handle_sim_step(sim_time=rcv["simTime"])
            else:
                raise FatalTraCIError("unknown command")

            if response is not None:
                self.traci.send_raw(response, append_message_len=True)

            # clear state
            self.traci.clear_state()

        self.traci.close()
        logging.info("connection closed.")

    def start(self, *kw, **kwargs):
        try:
            # Connection is controlled by OMNeT++ move _initialize() into _run()
            host = self.host
            if host != "localhost":
                host = "0.0.0.0"

            _, _socket, _, _server_port = create_accept_server_socket(host, self.port)
            self._set_connection(WrappedTraCIConnection(_socket))
            self.server_port = _server_port

            self._running = True
            self._init_sub_listener()
            self._run()
        except NotImplementedError as e:
            print(e)
        finally:
            self._cleanup()
