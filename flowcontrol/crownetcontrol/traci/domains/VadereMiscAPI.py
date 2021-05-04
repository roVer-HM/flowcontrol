#
# Generated source file. DO NOT CHANGE!

from flowcontrol.crownetcontrol.traci.domains.domain import Domain
from flowcontrol.crownetcontrol.traci import constants_vadere as tc


class VadereMiscAPI(Domain):
    def __init__(self):
        Domain.__init__(
            self,
            "v_misc",
            tc.CMD_GET_V_MISC_VARIABLE,
            tc.CMD_SET_V_MISC_VARIABLE,
            tc.CMD_SUBSCRIBE_V_MISC_VARIABLE,
            tc.RESPONSE_SUBSCRIBE_V_MISC_VARIABLE,
            tc.CMD_SUBSCRIBE_V_MISC_CONTEXT,
            tc.RESPONSE_SUBSCRIBE_V_MISC_CONTEXT,
        )

    def create_target_changer(self, data):
        self._setCmd(tc.VAR_ADD_TARGET_CHANGER, "", "s", data)

    def add_stimulus_infos(self, data):
        self._setCmd(tc.VAR_ADD_STIMULUS_INFOS, "", "s", data)

    def get_all_stimulus_infos(self):
        return self._getUniversal(tc.VAR_GET_ALL_STIMULUS_INFOS, "")

    def remove_target_changer(self, element_id):
        self._setCmd(tc.VAR_REMOVE_TARGET_CHANGER, element_id, "Error", None)

    def send_dissemination_cmd(self, cmd_content, pack_size = 0):
        # pack_size : integer
        # cmd_content: control command
        # TODO check here

        #_cmd = bytes()
        #_cmd += struct.pack("i", 3)
        #_cmd += struct.pack("i", pack_size)
        #_cmd += struct.pack("!i", len(cmd_content)) + cmd_content.encode("latin1")
        #self._connection.send_cmd(tc.CMD_CONTROLLER, tc.VAR_DISSEMINATION, None, None, "t")

        # data is of type bytes
        # data contains
        # Integer: simulated packet length
        # Integer: byte array lengths
        # Bytes: control command that contains the json-string
        self._setCmd(tc.VAR_DISSEMINATION, "", "s", cmd_content)





