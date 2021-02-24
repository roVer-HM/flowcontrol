# -*- coding: utf-8 -*-
# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2008-2020 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    connection.py
# @author  Michael Behrisch
# @author  Lena Kalleske
# @author  Mario Krumnow
# @author  Daniel Krajzewicz
# @author  Jakob Erdmann
# @date    2008-10-09

from __future__ import print_function
from __future__ import absolute_import

import logging
import socket
import struct
import sys
import threading
import warnings
import abc

from . import constants as tc
from .VaderePersonAPI import VaderePersonAPI
from .VadereMiscAPI import VadereMiscAPI
from .VadereSimulationAPI import VadereSimulationAPI
from .exceptions import TraCIException, FatalTraCIError
from .domain import _defaultDomains
from .storage import Storage

from flowcontrol.strategy.strategies import Strategy, ControlAction

_RESULTS = {0x00: "OK", 0x01: "Not implemented", 0xFF: "Error"}


def _create_client_socket():
    if sys.platform.startswith("java"):
        # working around jython 2.7.0 bug #2273
        _socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
        )
    else:
        _socket = socket.socket()
    _socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return _socket

def _create_accept_server_socket(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(0)  # only one client
    logging.info(f"listening on port {port} ...")
    _socket, addr = s.accept()
    return s, _socket, addr[0], addr[1]


class Connection(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, _socket=None):
        self._socket = _socket

    def recv_exact(self):
        try:
            result = bytes()
            while len(result) < 4:
                t = self._socket.recv(4 - len(result))
                if not t:
                    return None
                result += t
            length = struct.unpack("!i", result)[0] - 4
            result = bytes()
            while len(result) < length:
                t = self._socket.recv(length - len(result))
                if not t:
                    return None
                result += t
            return Storage(result)
        except socket.error:
            return None

    def send_traci_msg(self, data):
        length = struct.pack("!i", len(self._string) + 4)
        self._socket.send(length + data)

    def send_exact(self):
        if self._socket is None:
            raise FatalTraCIError("Connection already closed.")
        # print("python_sendExact: '%s'" % ' '.join(map(lambda x : "%X" % ord(x), self._string)))
        self.send_traci_msg(self._string)
        result = self.recv_exact()
        if not result:
            self._socket.close()
            del self._socket
            raise FatalTraCIError("connection closed by SUMO")
        for command in self._queue:
            prefix = result.read("!BBB")
            err = result.readString()
            if prefix[2] or err:
                self._string = bytes()
                self._queue = []
                raise TraCIException(err, prefix[1], _RESULTS[prefix[2]])
            elif prefix[1] != command:
                raise FatalTraCIError(
                    "Received answer %s for command %s." % (prefix[1], command)
                )
            elif prefix[1] == tc.CMD_STOP:
                length = result.read("!B")[0] - 1
                result.read("!%sx" % length)
        self._string = bytes()
        self._queue = []
        return result

    @staticmethod
    def pack(format, *values):
        packed = bytes()
        for f, v in zip(format, values):
            if f == "i":
                packed += struct.pack("!Bi", tc.TYPE_INTEGER, int(v))
            elif f == "I":  # raw int for setOrder
                packed += struct.pack("!i", int(v))
            elif f == "d":
                packed += struct.pack("!Bd", tc.TYPE_DOUBLE, float(v))
            elif f == "D":  # raw double for some base commands like simstep
                packed += struct.pack("!d", float(v))
            elif f == "b":
                packed += struct.pack("!Bb", tc.TYPE_BYTE, int(v))
            elif f == "B":
                packed += struct.pack("!BB", tc.TYPE_UBYTE, int(v))
            elif (
                    f == "u"
            ):  # raw unsigned byte needed for distance command and subscribe
                packed += struct.pack("!B", int(v))
            elif f == "s":
                v = str(v)
                packed += struct.pack("!Bi", tc.TYPE_STRING, len(v)) + v.encode(
                    "latin1"
                )
            elif f == "p":  # polygon
                if len(v) <= 255:
                    packed += struct.pack("!BB", tc.TYPE_POLYGON, len(v))
                else:
                    packed += struct.pack("!BBi", tc.TYPE_POLYGON, 0, len(v))
                for p in v:
                    packed += struct.pack("!dd", *p)
            elif f == "t":  # tuple aka compound
                packed += struct.pack("!Bi", tc.TYPE_COMPOUND, v)
            elif f == "c":  # color
                packed += struct.pack(
                    "!BBBBB",
                    tc.TYPE_COLOR,
                    int(v[0]),
                    int(v[1]),
                    int(v[2]),
                    int(v[3]) if len(v) > 3 else 255,
                )
            elif f == "l":  # string list
                packed += struct.pack("!Bi", tc.TYPE_STRINGLIST, len(v))
                for s in v:
                    packed += struct.pack("!i", len(s)) + s.encode("latin1")
            elif f == "f":  # float list
                packed += struct.pack("!Bi", tc.TYPE_DOUBLELIST, len(v))
                for x in v:
                    packed += struct.pack("!d", x)
            elif f == "o":
                packed += struct.pack("!Bdd", tc.POSITION_2D, *v)
            elif f == "O":
                packed += struct.pack("!Bddd", tc.POSITION_3D, *v)
            elif f == "g":
                packed += struct.pack("!Bdd", tc.POSITION_LON_LAT, *v)
            elif f == "G":
                packed += struct.pack("!Bddd", tc.POSITION_LON_LAT_ALT, *v)
            elif f == "r":
                packed += struct.pack("!Bi", tc.POSITION_ROADMAP, len(v[0])) + v[
                    0
                ].encode("latin1")
                packed += struct.pack("!dB", v[1], v[2])
        return packed

    def build_cmd(self, cmd_id, var_id, obj_id, _format="", *values):
        _cmd_string = bytes()
        packed = self.pack(_format, *values)
        length = len(packed) + 1 + 1  # length and command
        if var_id is not None:
            if isinstance(var_id, tuple):  # begin and end of a subscription
                length += 8 + 8 + 4 + len(obj_id)
            else:
                length += 1 + 4 + len(obj_id)
        if length <= 255:
            _cmd_string += struct.pack("!BB", length, cmd_id)
            # "!BB" means:
            # ! represents the network byte
            # B: unsigned char
        else:
            _cmd_string += struct.pack("!BiB", 0, length + 4, cmd_id)
            # BiB : i -> integer
        if var_id is not None:
            if isinstance(var_id, tuple):
                _cmd_string += struct.pack("!dd", *var_id)
                # d -> double
            else:
                _cmd_string += struct.pack("!B", var_id)
                # B -> unsigned char
            _cmd_string += struct.pack("!i", len(obj_id)) + obj_id.encode("latin1")
        _cmd_string += packed
        return _cmd_string

    def send_cmd(self, cmd_id, var_id, obj_id, _format="", *values):

        self._queue.append(cmd_id)
        packed = self.build_cmd(cmd_id, var_id, obj_id, _format, *values)

        self._string += packed
        return self.send_exact()

    def load(self, args):
        """
        Load a simulation from the given arguments.
        """
        self.send_cmd(tc.CMD_LOAD, None, None, "l", args)

    def get_version(self):
        command = tc.CMD_GETVERSION
        result = self.send_cmd(command, None, None)
        result.readLength()
        response = result.read("!B")[0]
        if response != command:
            raise FatalTraCIError(
                "Received answer %s for command %s." % (response, command)
            )
        return result.readInt(), result.readString()

    def set_order(self, order):
        self.send_cmd(tc.CMD_SETORDER, None, None, "I", order)

    def close(self, wait=True):
        if self._socket is not None:
            self.send_cmd(tc.CMD_CLOSE, None, None)
            self._socket.close()
            self._socket = None

    def start(self):
        raise NotImplemented


class Controller:

    @classmethod
    def build_server_mode(cls, host="localhost", port=9997):
        ctr = cls()
        connection = ServerModeConnection(control_handler=ctr, host=host, port=port)
        ctr.connection = connection
        return ctr

    @classmethod
    def build_client_mode(cls, host="localhost", port=9999):
        ctr = cls()
        connection = ClientModeConnection(control_handler=ctr, host=host, port=port)
        ctr.connection = connection
        return ctr

    def __init__(self):
        self.connection = None

    def start_controller(self):
        if self.connection is None:
            raise RuntimeError("Controller has not working connection")
        self.connection.start()

    def handle_sim_step(self, sim_time, sim_state, traci_client):
        print("handle_sim_step")
        # use traci_client to set control action manually!
        return None

    def handle_init(self, traci_client):
        print("handle_init")
        # use traci_client as needed!
        pass


class BaseTraCIConnection(Connection):

    def __init__(self, _socket, default_domains=None):
        super().__init__()

        self._socket = _socket

        self._string = bytes()
        self._queue = []  # backlog of commands waiting response
        self.subscriptionMapping = {}

        if default_domains is not None:
            for domain in default_domains:
                domain.register(self, self.subscriptionMapping)

    def clear(self):
        self._string = bytes()
        self._queue = []

    def parse_subscription_result(self, result):
        for subscriptionResults in self.subscriptionMapping.values():
            subscriptionResults.reset()
        num_subs = result.readInt()
        responses = []
        while num_subs > 0:
            responses.append(self._read_subscription(result))
            num_subs -= 1
        return responses

    def _read_subscription(self, result):
        # to enable this you also need to set _DEBUG to True in storage.py
        # result.printDebug()
        result.readLength()
        response = result.read("!B")[0]
        # todo better comparison!
        is_variable_subscription = (
                 tc.RESPONSE_SUBSCRIBE_INDUCTIONLOOP_VARIABLE <= response <= tc.RESPONSE_SUBSCRIBE_BUSSTOP_VARIABLE
                                 ) or (
                tc.RESPONSE_SUBSCRIBE_PARKINGAREA_VARIABLE <= response <= tc.RESPONSE_SUBSCRIBE_OVERHEADWIRE_VARIABLE
        )
        object_id = result.readString()
        if not is_variable_subscription:
            domain = result.read("!B")[0]
        num_vars = result.read("!B")[0]
        if is_variable_subscription:
            while num_vars > 0:
                var_id, status = result.read("!BB")
                if status:
                    print("Error!", result.readTypedString())
                elif response in self.subscriptionMapping:
                    self.subscriptionMapping[response].add(object_id, var_id, result)
                else:
                    raise FatalTraCIError(
                        "Cannot handle subscription response %02x for %s."
                        % (response, object_id)
                    )
                num_vars -= 1
        else:
            object_no = result.read("!i")[0]
            for _ in range(object_no):
                oid = result.readString()
                if num_vars == 0:
                    self.subscriptionMapping[response].addContext(
                        object_id, self.subscriptionMapping[domain], oid
                    )
                for __ in range(num_vars):
                    var_id, status = result.read("!BB")
                    if status:
                        print("Error!", result.readTypedString())
                    elif response in self.subscriptionMapping:
                        self.subscriptionMapping[response].addContext(
                            object_id,
                            self.subscriptionMapping[domain],
                            oid,
                            var_id,
                            result,
                        )
                    else:
                        raise FatalTraCIError(
                            "Cannot handle subscription response %02x for %s."
                            % (response, object_id)
                        )
        return object_id, response

    def _subscribe(self, cmd_id, begin, end, obj_id, var_ids, parameters):
        _format = "u"
        args = [len(var_ids)]
        for v in var_ids:
            _format += "u"
            args.append(v)
            if parameters is not None and v in parameters:
                if isinstance(parameters[v], tuple):
                    f, a = parameters[v]
                elif isinstance(parameters[v], int):
                    f, a = "i", parameters[v]
                elif isinstance(parameters[v], float):
                    f, a = "d", parameters[v]
                else:
                    f, a = "s", parameters[v]
                _format += f
                args.append(a)
        result = self.send_cmd(cmd_id, (begin, end), obj_id, _format, *args)
        if var_ids:
            object_id, response = self._read_subscription(result)
            if response - cmd_id != 16 or object_id != obj_id:
                raise FatalTraCIError(
                    "Received answer %02x,%s for subscription command %02x,%s."
                    % (response, object_id, cmd_id, obj_id)
                )

    def _get_subscription_results(self, cmd_id):
        return self.subscriptionMapping[cmd_id]

    def _subscribe_context(
            self, cmd_id, begin, end, obj_id, domain, dist, var_ids, parameters=None
    ):
        result = self.send_cmd(
            cmd_id,
            (begin, end),
            obj_id,
            "uDu" + (len(var_ids) * "u"),
            domain,
            dist,
            len(var_ids),
            *var_ids
        )
        if var_ids:
            object_id, response = self._read_subscription(result)
            if response - cmd_id != 16 or object_id != obj_id:
                raise FatalTraCIError(
                    "Received answer %02x,%s for context subscription command %02x,%s."
                    % (response, object_id, cmd_id, obj_id)
                )

    def _add_subscription_filter(self, filter_type, params=None):
        if filter_type in (
                tc.FILTER_TYPE_NONE,
                tc.FILTER_TYPE_NOOPPOSITE,
                tc.FILTER_TYPE_TURN,
                tc.FILTER_TYPE_LEAD_FOLLOW,
        ):
            # filter without parameter
            assert params is None
            self.send_cmd(tc.CMD_ADD_SUBSCRIPTION_FILTER, None, None, "u", filter_type)
        elif filter_type in (
                tc.FILTER_TYPE_DOWNSTREAM_DIST,
                tc.FILTER_TYPE_UPSTREAM_DIST,
                tc.FILTER_TYPE_FIELD_OF_VISION,
                tc.FILTER_TYPE_LATERAL_DIST,
        ):
            # filter with float parameter
            self.send_cmd(
                tc.CMD_ADD_SUBSCRIPTION_FILTER, None, None, "ud", filter_type, params
            )
        elif filter_type in (tc.FILTER_TYPE_VCLASS, tc.FILTER_TYPE_VTYPE):
            # filter with list(string) parameter
            self.send_cmd(
                tc.CMD_ADD_SUBSCRIPTION_FILTER, None, None, "ul", filter_type, params
            )
        elif filter_type == tc.FILTER_TYPE_LANES:
            # filter with list(byte) parameter
            # check uniqueness of given lanes in list
            lanes = set()
            for i in params:
                lane = int(i)
                if lane < 0:
                    lane += 256
                lanes.add(lane)
            if len(lanes) < len(list(params)):
                warnings.warn(
                    "Ignoring duplicate lane specification for subscription filter."
                )
            self.send_cmd(
                tc.CMD_ADD_SUBSCRIPTION_FILTER,
                None,
                None,
                (len(lanes) + 2) * "u",
                filter_type,
                len(lanes),
                *lanes
            )


class Client(BaseTraCIConnection):
    """Contains the socket, the composed message string
    together with a list of TraCI commands which are inside.
    """

    def __init__(self, host="127.0.0.1", port=9997, default_domains=None, process=None):
        self._host = host
        self._port = port
        self._process = process
        _socket = _create_client_socket()
        self.stepListeners = {}
        self.nextStepListenerID = 0

        super().__init__(_socket, default_domains)
        self._socket.connect((self._host, self._port))
        self._stepListeners = {}

    def simulation_step(self, step=0.0):
        """
        Make a simulation step and simulate up to the given second in sim time.
        If the given value is 0 or absent, exactly one step is performed.
        Values smaller than or equal to the current sim time result in no action.
        """
        if type(step) is int and step >= 1000:
            warnings.warn(
                "API change now handles step as floating point seconds", stacklevel=2
            )
        result = self.send_cmd(tc.CMD_SIMSTEP, None, None, "D", step)
        for subscriptionResults in self.subscriptionMapping.values():
            subscriptionResults.reset()
        num_subs = result.readInt()
        responses = []
        while num_subs > 0:
            responses.append(self._read_subscription(result))
            num_subs -= 1
        self._manage_step_listeners(step)
        return responses

    def remove_step_listener(self, listener_id):
        """removeStepListener(traci.StepListener) -> bool

        Remove the step listener from traci's step listener container.
        Returns True if the listener was removed successfully, False if it wasn't registered.
        """
        # print ("traci: removeStepListener %s\nlisteners: %s"%(listenerID, _stepListeners))
        if listener_id in self._stepListeners:
            self._stepListeners[listener_id].cleanUp()
            del self._stepListeners[listener_id]
            # print ("traci: Removed stepListener %s"%(listenerID))
            return True
        warnings.warn(
            "Cannot remove unknown listener %s.\nlisteners:%s"
            % (listener_id, self._stepListeners)
        )
        return False

    def _manage_step_listeners(self, step):
        listeners_to_remove = []
        for (listenerID, listener) in self._stepListeners.items():
            keep = listener.step(step)
            if not keep:
                listeners_to_remove.append(listenerID)
        for listenerID in listeners_to_remove:
            self.remove_step_listener(listenerID)

    def add_step_listener(self, listener):
        """addStepListener(traci.StepListener) -> int

        Append the step listener (its step function is called at the end of every call to traci.simulationStep())
        Returns the ID assigned to the listener if it was added successfully, None otherwise.
        """
        if issubclass(type(listener), StepListener):
            listener.setID(self.nextStepListenerID)
            self._stepListeners[self.nextStepListenerID] = listener
            self.nextStepListenerID += 1
            # print ("traci: Added stepListener %s\nlisteners: %s"%(_nextStepListenerID - 1, _stepListeners))
            return self.nextStepListenerID - 1
        warnings.warn(
            "Proposed listener's type must inherit from traci.StepListener. Not adding object of type '%s'"
            % type(listener)
        )
        return None

    def close(self, wait=True):
        for listenerID in list(self._stepListeners.keys()):
            self.remove_step_listener(listenerID)
        super().close(wait=wait)
        if wait and self._process is not None:
            self._process.wait()


class DomainHandler:

    def __init__(self):
        self.v_person = VaderePersonAPI()
        self.v_misc = VadereMiscAPI()
        self.v_sim = VadereSimulationAPI()
        self._registered = False

    def register(self, connection: BaseTraCIConnection):
        if not self._registered:
            self.v_person.register(connection, connection.subscriptionMapping, copy_domain=False)
            self.v_misc.register(connection, connection.subscriptionMapping, copy_domain=False)
            self.v_sim.register(connection, connection.subscriptionMapping, copy_domain=False)
            self._registered = True

    @property
    def registered(self):
        return self.registered


class TraCiManager:

    def __init__(self, host, port, control_handler):
        self.host = host
        self.port = port
        self._running = False
        self._control_hdl: Controller = control_handler
        self.domains: DomainHandler = DomainHandler()

    def _set_connection(self, connection):
        self._con = connection

    def _set_base_client(self, client):
        self._base_client: BaseTraCIConnection = client
        self.domains.register(self._base_client)

    def _initialize(self, *arg, **kwargs):
        pass

    def _parse_subscription_result(self, result):
        return 42.0, {}

    def _handle_sim_step(self, subscription_result):
        """ implement """
        # todo: update subscription
        time_step, state = self._parse_subscription_result(subscription_result)
        result = self._control_hdl.handle_sim_step(time_step, state, self._base_client)
        return result

    def _send_response(self, data):
        self._con.send_traci_msg(data)

    def _run(self):
        pass

    def _cleanup(self):
        pass

    def start(self):
        try:
            self._initialize()
            self._run()
        except NotImplementedError as e:
            print(e)
        finally:
            self._cleanup()


class ClientModeConnection(TraCiManager):

    def __init__(self, control_handler, host="127.0.0.1", port=9999):
        super().__init__(host, port, control_handler)
        self._set_connection(BaseTraCIConnection(_create_client_socket()))
        self._set_base_client(self._con)
        self._con._socket.connect(host, port)

        self._sim_until = -1

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

        # call controller callback
        self._control_hdl.handle_init(self._base_client)

    def _run(self):
        while self._running:
            simstep_response = self._simulation_step(self._sim_until)
            # no response required for ClientModeConnection
            self._handle_sim_step(simstep_response)
            # clear conection state (for ClientModeConnection _con == _base_client)
            self._con.clear()

    def set_step(self, step):
        # todo allow controller to set next update time manually. Currently not settable
        pass


class ServerModeConnection(TraCiManager):

    def __init__(self, control_handler: Controller, host="127.0.0.1", port=9997):
        super().__init__(host, port, control_handler)
        self.server_port = -1

    def _initialize(self, *arg, **kwargs):
        cmd = kwargs["cmd"]
        self._control_hdl.handle_init(self._base_client)
        return b"ACK/NACK"

    def _run(self):
        while self._running:
            # wait for command
            cmd = self._con.recv_exact()
            if not cmd:
                self._running = False
                break

            cmd.read_cmdLength()
            cmd_id, var_id = cmd.read_cmd_var()

            if cmd_id == "INI":
                # response: simple act
                response = self._initialize(cmd=cmd)
            elif cmd_id == "timeStepResponse":
                # todo parse subscription result
                subscription_result = self._base_client.parse_subscription_result(cmd)
                # response: None
                self._handle_sim_step(subscription_result)
                response = b"ACK/NACK"
            else:
                raise TraCIException("unknown command")

            if response is not None:
                # send response for INIT or timeStepResponse and wait for next timeStepResponse
                self._con.send_traci_msg(response)

            # clear state
            self._base_client._string = bytes()
            self._base_client._queue = []

        self._con.close()
        logging.info("connection closed.")

    def start(self):
        try:
            # Connection is controlled by OMNeT++ move _initialize() into _run()
            _, _socket, _, _server_port = _create_accept_server_socket(self.host, self.port)
            self._set_connection(Connection(_socket))
            self.server_port = _server_port

            # todo: replace BaseTraCIConnection(_socket) with 'Wrapped' connection
            self._set_base_client(BaseTraCIConnection(_socket))

            self._running = True
            self._run()
        except NotImplementedError as e:
            print(e)
        finally:
            self._cleanup()


class StepListener(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def step(self, t=0):
        """step(int) -> bool

        After adding a StepListener 'listener' with traci.addStepListener(listener),
        TraCI will call listener.step(t) after each call to traci.simulationStep(t)
        The return value indicates whether the stepListener wants to stay active.
        """
        return True

    def cleanUp(self):
        """cleanUp() -> None

        This method is called at removal of the stepListener, allowing to schedule some final actions
        """
        pass

    def setID(self, ID):
        self._ID = ID

    def getID(self):
        return self._ID
