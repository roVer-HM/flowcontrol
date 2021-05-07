#
# Generated source file. DO NOT CHANGE!

from flowcontrol.crownetcontrol.traci.domains.domain import Domain
from flowcontrol.crownetcontrol.traci import constants_vadere as tc


class VadereSimulationAPI(Domain):
    def __init__(self):
        Domain.__init__(
            self,
            "v_simulation",
            tc.CMD_GET_V_SIM_VARIABLE,
            tc.CMD_SET_V_SIM_VARIABLE,
            tc.CMD_SUBSCRIBE_V_SIM_VARIABLE,
            tc.RESPONSE_SUBSCRIBE_V_SIM_VARIABLE,
            tc.CMD_SUBSCRIBE_V_SIM_CONTEXT,
            tc.RESPONSE_SUBSCRIBE_V_SIM_CONTEXT,
        )

    def get_network_bound(self):
        return self._getUniversal(tc.VAR_NET_BOUNDING_BOX, "")

    def get_time(self):
        return self._getUniversal(tc.VAR_TIME, "")

    def get_sim_ste(self):
        return self._getUniversal(tc.VAR_DELTA_T, "")

    def set_sim_config(self):
        self._setCmd(tc.VAR_SIM_CONFIG, "", "Error", None)

    def get_hash(self, data):
        return self._getUniversal(tc.VAR_CACHE_HASH, "", data)

    def get_departed_pedestrian_id(self, data):
        return self._getUniversal(tc.VAR_DEPARTED_PEDESTRIAN_IDS, "", data)

    def get_arrived_pedestrian_ids(self, data):
        return self._getUniversal(tc.VAR_ARRIVED_PEDESTRIAN_PEDESTRIAN_IDS, "", data)

    def get_position_conversion(self, data):
        return self._getUniversal(tc.VAR_POSITION_CONVERSION, "", data)

    def get_coordinate_reference(self, data):
        return self._getUniversal(tc.VAR_COORD_REF, "", data)

    def send_control(self, message, model, pack_size=-3, sending_node_id="-1", obj_id = "-2"):
        """
        message: a json string
        """

        # No compound module needed. (I forgot that you just want to send a Json string)
        # format="s" is string see connection.py line 143 (pack) and line 165
        # self._connection.send_cmd(cmd_id, var_id, obj_id, _format="", *values)
        #self._connection.send_cmd(cmd_id, var_id, obj_id, "s", json)
        # send_cmd (defined in Connection [connection.py:159]) will call build_cmd. THIS function is different
        # between client and server mode!!!
        # Client: only has BaseTraCIConnection which does not override build_cmd from Connection (connection.py: 234)
        # Server: has WrappedTraCIConnection which OVERRIDES build_cmd (connection.py: 542) (self._wrap)

        self._connection.send_cmd(self._cmdSetID, tc.VAR_EXTERNAL_INPUT, obj_id, "tisss", pack_size, sending_node_id, model , message)








