import logging

from flowcontrol.crownetcontrol.traci.connection import _create_accept_server_socket, WrappedTraCIConnection
from flowcontrol.crownetcontrol.traci.connection_manager import TraCiManager
from flowcontrol.crownetcontrol.traci.exceptions import FatalTraCIError


class ServerModeConnection(TraCiManager):
    def __init__(self, control_handler, host="127.0.0.1", port=9997):
        super().__init__(host, port, control_handler)
        self.server_port = -1

    def _initialize(self, *arg, **kwargs):
        data = kwargs["data"]
        self._control_hdl.handle_init(
            self._default_sub.time, self.sub_listener, self._base_client
        )
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
            _, _socket, _, _server_port = _create_accept_server_socket(
                self.host, self.port
            )
            self._set_connection(WrappedTraCIConnection(_socket))
            self.server_port = _server_port

            self._running = True
            self._run()
        except NotImplementedError as e:
            print(e)
        finally:
            self._cleanup()