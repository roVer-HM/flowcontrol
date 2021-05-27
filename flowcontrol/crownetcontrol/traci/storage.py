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

# @file    storage.py
# @author  Michael Behrisch
# @author  Lena Kalleske
# @author  Mario Krumnow
# @author  Daniel Krajzewicz
# @author  Jakob Erdmann
# @date    2008-10-09

from __future__ import print_function
from __future__ import absolute_import
import struct
from flowcontrol.crownetcontrol.traci import constants_vadere as tc

_DEBUG = False


class Storage:
    def __init__(self, content):
        self._content = content
        self._pos = 0

    def check_number_bytes(self, length):
        if (self._pos + length) < len(self._content):
            raise RuntimeError(
                f"expected command with length {length} but only {len(self._content) - self._pos} bytes left."
            )
        return True

    def read_cmd_length(self):
        cmd_id = self.read("!B")[0]
        if cmd_id > 0:
            return cmd_id
        else:
            return self.readInt()

    def read_cmd_var(self):
        return self.read("!BB")

    def read_status(self):
        status_dict = {
            "length": self.read_cmd_length(),
            "cmd": self.read("!B")[0],
            "result": self.read("!B")[0],
            "err": self.readString(),
        }
        return status_dict

    def read(self, format):
        oldPos = self._pos
        self._pos += struct.calcsize(format)
        return struct.unpack(format, self._content[oldPos : self._pos])

    def readInt(self):
        return self.read("!i")[0]

    def readTypedInt(self):
        t, i = self.read("!Bi")
        assert t == tc.TYPE_INTEGER
        return i

    def readDouble(self):
        return self.read("!d")[0]

    def readTypedDouble(self):
        t, d = self.read("!Bd")
        assert t == tc.TYPE_DOUBLE
        return d

    def readLength(self):
        length = self.read("!B")[0]
        if length > 0:
            return length
        return self.read("!i")[0]

    def readString(self):
        length = self.read("!i")[0]
        return str(self.read("!%ss" % length)[0].decode("latin1"))

    def readTypedString(self):
        t = self.read("!B")[0]
        assert t == tc.TYPE_STRING, "expected TYPE_STRING (%02x), found %02x." % (
            tc.TYPE_STRING,
            t,
        )
        return self.readString()

    def readStringList(self):
        n = self.read("!i")[0]
        return tuple([self.readString() for i in range(n)])

    def readTypedStringList(self):
        t = self.read("!B")[0]
        assert t == tc.TYPE_STRINGLIST
        return self.readStringList()

    def readDoubleList(self):
        n = self.read("!i")[0]
        return tuple([self.readDouble() for i in range(n)])

    def read2DPosition(self):
        return self.read("!dd")

    def read3DPosition(self):
        return self.read("!ddd")

    def read2DPositionList(self):
        n = self.read("!i")[0]
        return tuple([self.read2DPosition() for i in range(n)])

    def read3DPositionList(self):
        n = self.read("!i")[0]
        return tuple([self.read3DPosition() for i in range(n)])

    def readIntegerList(self):
        n = self.read("!i")[0]
        return tuple([self.readInt() for i in range(n)])

    def readShape(self):
        length = self.readLength()
        return tuple([self.read("!dd") for i in range(length)])

    def readCompound(self, expectedSize=None):
        t, s = self.read("!Bi")
        assert t == tc.TYPE_COMPOUND
        assert expectedSize is None or s == expectedSize
        return s

    def ready(self):
        return self._pos < len(self._content)

    def printDebug(self):
        if _DEBUG:
            for char in self._content[self._pos :]:
                print("%03i %02x %s" % (ord(char), ord(char), char))


class SingleCommand(Storage):
    def __init__(self, content):
        super().__init__(content)
