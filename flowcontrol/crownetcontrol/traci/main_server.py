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

# @file    main.py
# @author  Christina Mayr mayr9@hm.edu


from __future__ import print_function
from __future__ import absolute_import

from . import _person, _route, _controller

person = _person.PersonDomain()
route = _route.RouteDomain()
controller = _controller.Controller()

_connections = {}
_traceFile = {}
_traceGetters = {}
# cannot use immutable type as global variable
_currentLabel = [""]
_connectHook = None




