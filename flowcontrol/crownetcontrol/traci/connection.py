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
import warnings
import abc
from typing import List

from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.crownetcontrol.traci.domains.VaderePersonAPI import VaderePersonAPI
from flowcontrol.crownetcontrol.traci.domains.VadereMiscAPI import VadereMiscAPI
from flowcontrol.crownetcontrol.traci.domains.VadereSimulationAPI import (
    VadereSimulationAPI,
)
from .domains.VadereControlDomain import VadereControlCommandApi
from .exceptions import TraCIException, FatalTraCIError, TraCISimulationEnd
from .storage import Storage
from flowcontrol.crownetcontrol.state.state_listener import SubscriptionListener

_RESULTS = {0x00: "OK", 0x01: "Not implemented", 0xFF: "Error"}


def create_client_socket():
    if sys.platform.startswith("java"):
        # working around jython 2.7.0 bug #2273
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    else:
        _socket = socket.socket()
    _socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return _socket


def create_accept_server_socket(host, port):
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
        self._string = bytes()
        self._queue = []

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

    def _parse_received(self, result):
        if not result:
            self._socket.close()
            del self._socket
            raise FatalTraCIError("connection closed by SUMO")
        for command in self._queue:
            status = result.read_status()
            if status["result"] or status["err"]:
                self._string = bytes()
                self._queue = []
                if status["err"] == "Simulation end reached.":
                    raise TraCISimulationEnd(
                        status["err"], status["cmd"], _RESULTS[status["result"]]
                    )
                else:
                    raise TraCIException(
                        status["err"], status["cmd"], _RESULTS[status["result"]]
                    )
            elif status["cmd"] != command:
                raise FatalTraCIError(
                    "Received answer %s for command %s." % (status["cmd"], command)
                )
            elif status["cmd"] == tc.CMD_STOP:
                length = result.read("!B")[0] - 1
                result.read("!%sx" % length)
        self._string = bytes()
        self._queue = []
        return result

    def _send_exact(self):
        if self._socket is None:
            raise FatalTraCIError("Connection already closed.")
        # print("python_sendExact: '%s'" % ' '.join(map(lambda x : "%X" % ord(x), self._string)))
        length = struct.pack("!i", len(self._string) + 4)
        self._socket.send(length + self._string)
        result = self.recv_exact()

        return self._parse_received(result)

    def send_raw(self, data, append_message_len=True):
        if self._socket is None:
            raise FatalTraCIError("Connection already closed.")
        if append_message_len:
            length = struct.pack("!i", len(data) + 4)
            self._socket.send(length + data)
        else:
            self._socket.send(data)

    @staticmethod
    def pack(_format, *values):
        if _format == "packet":
            assert type(values[0]) == bytes
            return values[0]
        packed = bytes()
        for f, v in zip(_format, values):
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

    @staticmethod
    def response(cmd_id, r_type, msg=""):
        _cmd_string = bytes()
        _cmd_string += struct.pack("!B", cmd_id)
        _cmd_string += struct.pack("!B", r_type)
        _cmd_string += struct.pack("!i", len(msg)) + msg.encode("latin1")

        length = len(_cmd_string) + 1  # length
        if length <= 255:
            _cmd_string = struct.pack("!B", length) + _cmd_string
        else:
            _cmd_string = struct.pack("!Bi", 0, length + 4) + _cmd_string

        return _cmd_string

    @staticmethod
    def res_ok(cmd_id):
        return Connection.response(cmd_id, tc.RTYPE_OK)

    @staticmethod
    def res_err(cmd_id, msg=""):
        return Connection.response(cmd_id, tc.RTYPE_ERR, msg)

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
        return self._send_exact()

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

    def clear_state(self):
        self._queue = []
        self._string = bytes()

    def connect(self, host, port):
        self._socket.connetct((host, port))


class BaseTraCIConnection(Connection):
    def __init__(self, _socket, default_domains=None):
        super().__init__()

        self._socket = _socket

        self._string = bytes()
        self._queue = []  # backlog of commands waiting response
        self.subscriptionMapping = {}
        self.subscriptionListener: List[SubscriptionListener] = []

        if default_domains is not None:
            for domain in default_domains:
                domain.register(self, self.subscriptionMapping)

    def add_sub_listener(self, listener: SubscriptionListener):
        self.subscriptionListener.append(listener)

    def notify_subscription_listener(self):
        for listener in self.subscriptionListener:
            listener.handle_subscription_result(self.subscriptionMapping)

    def clear(self):
        self._string = bytes()
        self._queue = []

    def parse_subscription_result(self, result):
        for subscriptionResults in self.subscriptionMapping.values():
            subscriptionResults.reset()
        num_subs = result.readInt()
        responses = []
        while num_subs > 0:
            responses.append(self.read_subscription(result))
            num_subs -= 1
        return responses

    def read_subscription(self, result):
        # to enable this you also need to set _DEBUG to True in storage.py
        # result.printDebug()
        result.readLength()
        response = result.read("!B")[0]
        # todo better comparison!
        is_variable_subscription = (
            tc.RESPONSE_SUBSCRIBE_INDUCTIONLOOP_VARIABLE
            <= response
            <= tc.RESPONSE_SUBSCRIBE_BUSSTOP_VARIABLE
        ) or (
            tc.RESPONSE_SUBSCRIBE_PARKINGAREA_VARIABLE
            <= response
            <= tc.RESPONSE_SUBSCRIBE_OVERHEADWIRE_VARIABLE
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
            object_id, response = self.read_subscription(result)
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
            *var_ids,
        )
        if var_ids:
            object_id, response = self.read_subscription(result)
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
                *lanes,
            )

    def send_raw(self, data, append_message_len=True):
        if self._socket is None:
            raise FatalTraCIError("Connection already closed.")
        if append_message_len:
            length = struct.pack("!i", len(data) + 4)
            self._socket.send(length + data)
        else:
            self._socket.send(data)

    def send_file(self, file_name, file_content):
        _cmd = bytes()
        _cmd += struct.pack("!B", tc.CMD_FILE_SEND)
        _cmd += struct.pack("!i", len(file_name)) + file_name.encode("latin1")
        _cmd += struct.pack("!i", len(file_content)) + file_content.encode("latin1")

        # assume big packet
        _cmd = struct.pack("!Bi", 0, len(_cmd) + 5) + _cmd

        self.send_raw(_cmd, append_message_len=True)
        result = self._recv_exact()
        temp_var = result.read_status()
        print()



class WrappedTraCIConnection(BaseTraCIConnection):
    VADERE = "V"
    OPP = "O"

    def __init__(self, _socket, default_domains=None):
        super().__init__(_socket, default_domains)

    def _simulator_prefix(self, cmd_id):
        if cmd_id > 0:
            return self.VADERE
        else:
            return self.OPP

    def connect(self, host, port):
        raise RuntimeError(
            "WrappedTraCIConnection operates in server mode. Do not connect to socket."
        )

    def _wrap(self, cmd_id):
        return tc.CMD_CONTROLLER, tc.VAR_REDIRECT, self._simulator_prefix(cmd_id)

    def build_cmd(self, cmd_id, var_id, obj_id, _format="", *values):
        """
        wrap command based on cmd_id as payload in a VAR_REDIRECT command
        """
        payload = super().build_cmd(cmd_id, var_id, obj_id, _format, *values)

        w_cmd_od, w_var_id, w_obj_id = self._wrap(cmd_id)
        wrapped_cmd = super().build_cmd(w_cmd_od, w_var_id, w_obj_id, "packet", payload)
        return wrapped_cmd

    def build_cmd_raw(self, cmd_id, var_id, obj_id, _format="", *values):
        payload = super().build_cmd(cmd_id, var_id, obj_id, _format, *values)
        return payload

    def send_traci_msg(self, data):
        length = struct.pack("!i", len(self._string) + 4)
        self._socket.send(length + data)

    def _parse_server_received(self, result):
        if not result:
            self._socket.close()
            del self._socket
            raise FatalTraCIError("connection closed by partner")
        # we are waiting as server thus there should be no queued command
        assert len(self._queue) == 0
        self._string = bytes()
        self._queue = []
        # read status and use 'cmd' to decide what to do
        result.readLength()  # cmd_len
        cmd_id = result.read("!B")[0]
        var_id = result.read("!B")[0]
        result.readString()  # object_id

        if var_id in [tc.VAR_INIT, tc.CMD_SIMSTEP]:
            result.readCompound(1)
            data = result.readTypedDouble()
        else:
            raise ValueError("unexpected variable received ")

        return {"action": var_id, "cmdId": cmd_id, "simTime": data}

    def recv_control(self):
        """unpack CONTROL commands to their respective standard commands"""
        result = self.recv_exact()
        return self._parse_server_received(result)

    def send_control_response(self, foo, bar):
        pass


class DomainHandler:
    def __init__(self):
        self.v_person = VaderePersonAPI()
        self.v_misc = VadereMiscAPI()
        self.v_sim = VadereSimulationAPI()
        self.v_ctrl = VadereControlCommandApi()
        self._registered = False
        self._cmd_domain_map = {}

    def _register(self, dom, connection: BaseTraCIConnection):
        dom.register(connection, connection.subscriptionMapping, copy_domain=False)
        self._cmd_domain_map[dom.name] = dom
        self._cmd_domain_map[dom._cmdGetID] = dom
        self._cmd_domain_map[dom._cmdSetID] = dom
        self._cmd_domain_map[dom._subscribeID] = dom
        self._cmd_domain_map[dom._subscribeResponseID] = dom
        self._cmd_domain_map[dom._contextID] = dom
        self._cmd_domain_map[dom._contextResponseID] = dom

    def has_domain_for(self, cmd):
        return cmd in self._cmd_domain_map

    def dom_for_cmd(self, cmd):
        if cmd not in self._cmd_domain_map:
            raise ValueError(f"not domain found command {cmd}")
        return self._cmd_domain_map[cmd]

    def register(self, connection: BaseTraCIConnection):
        if not self._registered:
            self._register(self.v_person, connection)
            self._register(self.v_misc, connection)
            self._register(self.v_sim, connection)
            # ctrl has no subscriptions
            self.v_ctrl.register(connection, copy_domain=False)
            self._registered = True

    @property
    def registered(self):
        return self.registered
