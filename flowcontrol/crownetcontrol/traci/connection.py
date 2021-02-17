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
import socket
import struct
import sys
import warnings
import abc

from . import constants as tc
from .exceptions import TraCIException, FatalTraCIError
from .domain import _defaultDomains
from .storage import Storage

from strategies import Strategy, ControlAction

_RESULTS = {0x00: "OK", 0x01: "Not implemented", 0xFF: "Error"}

def _readState(result):
    # compound size and type
    assert(result.read("!i")[0] == 3)
    agent_position = result.read2DPositionList()
    target_list = result.readStringList()
    is_informed = result.readIntegerList()
    return CrowNetState(agent_position, target_list, is_informed)

class CrowNetState:

    def __init__(self, agent_position, target_list, is_informed):
        self.agent_position = agent_position
        self.target_list = target_list
        self._is_informed = is_informed




class Connection(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, host, port, process):
        self._host = host
        self._port = port

        if sys.platform.startswith("java"):
            # working around jython 2.7.0 bug #2273
            self._socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
            )
        else:
            self._socket = socket.socket()
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._process = process

    def _recvExact(self):
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

    def _sendExact(self):
        if self._socket is None:
            raise FatalTraCIError("Connection already closed.")
        length = struct.pack("!i", len(self._string) + 4)
        # print("python_sendExact: '%s'" % ' '.join(map(lambda x : "%X" % ord(x), self._string)))
        self._socket.send(length + self._string)
        result = self._recvExact()
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





    def _pack(self, format, *values):
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

    def _sendCmd(self, cmdID, varID, objID, format="", *values):

        # struct.pack(fmt, *values) -> fmt = "!BB" what does this mean? see https://docs.python.org/3/library/struct.html#format-characters

        self._queue.append(cmdID)
        packed = self._pack(format, *values)
        length = len(packed) + 1 + 1  # length and command
        if varID is not None:
            if isinstance(varID, tuple):  # begin and end of a subscription
                length += 8 + 8 + 4 + len(objID)
            else:
                length += 1 + 4 + len(objID)
        if length <= 255:
            self._string += struct.pack("!BB", length, cmdID)
            # "!BB" means:
            # ! represents the network byte
            # B: unsigned char
        else:
            self._string += struct.pack("!BiB", 0, length + 4, cmdID)
            # BiB : i -> integer
        if varID is not None:
            if isinstance(varID, tuple):
                self._string += struct.pack("!dd", *varID)
                # d -> double
            else:
                self._string += struct.pack("!B", varID)
                # B -> unsigned char
            self._string += struct.pack("!i", len(objID)) + objID.encode("latin1")

        self._string += packed
        return self._sendExact()

    def load(self, args):
        """
        Load a simulation from the given arguments.
        """
        self._sendCmd(tc.CMD_LOAD, None, None, "l", args)

    def getVersion(self):
        command = tc.CMD_GETVERSION
        result = self._sendCmd(command, None, None)
        result.readLength()
        response = result.read("!B")[0]
        if response != command:
            raise FatalTraCIError(
                "Received answer %s for command %s." % (response, command)
            )
        return result.readInt(), result.readString()

    def setOrder(self, order):
        self._sendCmd(tc.CMD_SETORDER, None, None, "I", order)

    def close(self, wait=True):
        if self._socket is not None:
            self._sendCmd(tc.CMD_CLOSE, None, None)
            self._socket.close()
            self._socket = None
        if wait and self._process is not None:
            self._process.wait()

    def start(self):
        raise NotImplemented


class Server(Connection):

    def __init__(self, strategy : Strategy , host="127.0.0.1", port=9997, process=None):

        self._host = host
        self._port = port

        # TODO rm this after check
        if sys.platform.startswith("java"):
            # working around jython 2.7.0 bug #2273
            self._server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
            )
        else:
            self._server_socket = socket.socket()
        self._server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen(0)

        self._strategy = strategy
        self._ready = True


        print("Server is waiting for omnetpp-client")
        # add try counter -> ... if necssary

        # while self._ready:

        (conn, addr) = self._server_socket.accept() # TIMEOUT
        self._socket = conn
        print("Client connected")

        handler = ClientHandler(conn)

    def close(self, wait=True):
        self._server_socket.close()
        self._socket.close()



    def get_control_action(self, state: dict):
        # dict that contains the vadere state and the omnet state
        control_action = self._strategy.compute_control_action(state)
        return control_action


    def _get_state_from_traci_msg(self):

        msg = self._recvExact()
        msg.read("!B")  # Type
        state = []
        for _ in range(msg.readInt()):
            msg.read("!B")  # Type
            state.append(_readState(msg))
        return tuple(state)

    def _send_control_action(self, control_action: ControlAction):

        simulator = self._strategy.get_simulator_destination()

        if simulator == "vadere":
            cmdGetID = tc.CMD_VADERE
        elif simulator == "omnetpp":
            cmdGetID = tc.CMD_OMNETPP
        else:
            raise ValueError("Simulator must be vadere or omnetpp.")

        for act in control_action.get_actions():
            if act == "target_list":
                self._sendCmd(cmdGetID, tc.VAR_TARGET_LIST, control_action)
            if act == "velocities":
                self._sendCmd(cmdGetID, tc.VELOCITIES, control_action)


class ClientHandler:

    def __init__(self, conn: Server, strategy : Strategy):
        self.running = True
        self.conn = conn
        self._strategy = strategy


    def run(self):

        while True:

            state = self.conn._get_state_from_traci_msg()
            control_action = self._strategy.get_control_action(state)
            self.conn._send_control_action(control_action)




class Client(Connection):

    """Contains the socket, the composed message string
    together with a list of TraCI commands which are inside.
    """

    def __init__(self, host="127.0.0.1", port=9997, process = None):
        super().__init__(host, port, process=process)
        self._string = bytes()
        self._queue = []
        self._subscriptionMapping = {}
        self._stepListeners = {}
        self._nextStepListenerID = 0
        for domain in _defaultDomains:
            domain._register(self, self._subscriptionMapping)

        self._socket.connect((self._host, self._port))
        print("Client connected.")


    def simulationStep(self, step=0.0):
        """
        Make a simulation step and simulate up to the given second in sim time.
        If the given value is 0 or absent, exactly one step is performed.
        Values smaller than or equal to the current sim time result in no action.
        """
        if type(step) is int and step >= 1000:
            warnings.warn(
                "API change now handles step as floating point seconds", stacklevel=2
            )
        result = self._sendCmd(tc.CMD_SIMSTEP, None, None, "D", step)
        for subscriptionResults in self._subscriptionMapping.values():
            subscriptionResults.reset()
        numSubs = result.readInt()
        responses = []
        while numSubs > 0:
            responses.append(self._readSubscription(result))
            numSubs -= 1
        self._manageStepListeners(step)
        return responses

    def removeStepListener(self, listenerID):
        """removeStepListener(traci.StepListener) -> bool

        Remove the step listener from traci's step listener container.
        Returns True if the listener was removed successfully, False if it wasn't registered.
        """
        # print ("traci: removeStepListener %s\nlisteners: %s"%(listenerID, _stepListeners))
        if listenerID in self._stepListeners:
            self._stepListeners[listenerID].cleanUp()
            del self._stepListeners[listenerID]
            # print ("traci: Removed stepListener %s"%(listenerID))
            return True
        warnings.warn(
            "Cannot remove unknown listener %s.\nlisteners:%s"
            % (listenerID, self._stepListeners)
        )
        return False

    def _manageStepListeners(self, step):
        listenersToRemove = []
        for (listenerID, listener) in self._stepListeners.items():
            keep = listener.step(step)
            if not keep:
                listenersToRemove.append(listenerID)
        for listenerID in listenersToRemove:
            self.removeStepListener(listenerID)

    def addStepListener(self, listener):
        """addStepListener(traci.StepListener) -> int

        Append the step listener (its step function is called at the end of every call to traci.simulationStep())
        Returns the ID assigned to the listener if it was added successfully, None otherwise.
        """
        if issubclass(type(listener), StepListener):
            listener.setID(self._nextStepListenerID)
            self._stepListeners[self._nextStepListenerID] = listener
            self._nextStepListenerID += 1
            # print ("traci: Added stepListener %s\nlisteners: %s"%(_nextStepListenerID - 1, _stepListeners))
            return self._nextStepListenerID - 1
        warnings.warn(
            "Proposed listener's type must inherit from traci.StepListener. Not adding object of type '%s'"
            % type(listener)
        )
        return None

    def close(self, wait=True):
        for listenerID in list(self._stepListeners.keys()):
            self.removeStepListener(listenerID)
        super().close(wait=wait)

    def _readSubscription(self, result):
        # to enable this you also need to set _DEBUG to True in storage.py
        # result.printDebug()
        result.readLength()
        response = result.read("!B")[0]
        isVariableSubscription = (
            response >= tc.RESPONSE_SUBSCRIBE_INDUCTIONLOOP_VARIABLE
            and response <= tc.RESPONSE_SUBSCRIBE_BUSSTOP_VARIABLE
        ) or (
            response >= tc.RESPONSE_SUBSCRIBE_PARKINGAREA_VARIABLE
            and response <= tc.RESPONSE_SUBSCRIBE_OVERHEADWIRE_VARIABLE
        )
        objectID = result.readString()
        if not isVariableSubscription:
            domain = result.read("!B")[0]
        numVars = result.read("!B")[0]
        if isVariableSubscription:
            while numVars > 0:
                varID, status = result.read("!BB")
                if status:
                    print("Error!", result.readTypedString())
                elif response in self._subscriptionMapping:
                    self._subscriptionMapping[response].add(objectID, varID, result)
                else:
                    raise FatalTraCIError(
                        "Cannot handle subscription response %02x for %s."
                        % (response, objectID)
                    )
                numVars -= 1
        else:
            objectNo = result.read("!i")[0]
            for _ in range(objectNo):
                oid = result.readString()
                if numVars == 0:
                    self._subscriptionMapping[response].addContext(
                        objectID, self._subscriptionMapping[domain], oid
                    )
                for __ in range(numVars):
                    varID, status = result.read("!BB")
                    if status:
                        print("Error!", result.readTypedString())
                    elif response in self._subscriptionMapping:
                        self._subscriptionMapping[response].addContext(
                            objectID,
                            self._subscriptionMapping[domain],
                            oid,
                            varID,
                            result,
                        )
                    else:
                        raise FatalTraCIError(
                            "Cannot handle subscription response %02x for %s."
                            % (response, objectID)
                        )
        return objectID, response

    def _subscribe(self, cmdID, begin, end, objID, varIDs, parameters):
        format = "u"
        args = [len(varIDs)]
        for v in varIDs:
            format += "u"
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
                format += f
                args.append(a)
        result = self._sendCmd(cmdID, (begin, end), objID, format, *args)
        if varIDs:
            objectID, response = self._readSubscription(result)
            if response - cmdID != 16 or objectID != objID:
                raise FatalTraCIError(
                    "Received answer %02x,%s for subscription command %02x,%s."
                    % (response, objectID, cmdID, objID)
                )

    def _getSubscriptionResults(self, cmdID):
        return self._subscriptionMapping[cmdID]

    def _subscribeContext(
        self, cmdID, begin, end, objID, domain, dist, varIDs, parameters=None
    ):
        result = self._sendCmd(
            cmdID,
            (begin, end),
            objID,
            "uDu" + (len(varIDs) * "u"),
            domain,
            dist,
            len(varIDs),
            *varIDs
        )
        if varIDs:
            objectID, response = self._readSubscription(result)
            if response - cmdID != 16 or objectID != objID:
                raise FatalTraCIError(
                    "Received answer %02x,%s for context subscription command %02x,%s."
                    % (response, objectID, cmdID, objID)
                )

    def _addSubscriptionFilter(self, filterType, params=None):
        if filterType in (
            tc.FILTER_TYPE_NONE,
            tc.FILTER_TYPE_NOOPPOSITE,
            tc.FILTER_TYPE_TURN,
            tc.FILTER_TYPE_LEAD_FOLLOW,
        ):
            # filter without parameter
            assert params is None
            self._sendCmd(tc.CMD_ADD_SUBSCRIPTION_FILTER, None, None, "u", filterType)
        elif filterType in (
            tc.FILTER_TYPE_DOWNSTREAM_DIST,
            tc.FILTER_TYPE_UPSTREAM_DIST,
            tc.FILTER_TYPE_FIELD_OF_VISION,
            tc.FILTER_TYPE_LATERAL_DIST,
        ):
            # filter with float parameter
            self._sendCmd(
                tc.CMD_ADD_SUBSCRIPTION_FILTER, None, None, "ud", filterType, params
            )
        elif filterType in (tc.FILTER_TYPE_VCLASS, tc.FILTER_TYPE_VTYPE):
            # filter with list(string) parameter
            self._sendCmd(
                tc.CMD_ADD_SUBSCRIPTION_FILTER, None, None, "ul", filterType, params
            )
        elif filterType == tc.FILTER_TYPE_LANES:
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
            self._sendCmd(
                tc.CMD_ADD_SUBSCRIPTION_FILTER,
                None,
                None,
                (len(lanes) + 2) * "u",
                filterType,
                len(lanes),
                *lanes
            )


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
