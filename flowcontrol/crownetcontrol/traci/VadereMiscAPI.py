#
# Generated source file. DO NOT CHANGE!

from .domain import Domain
from . import VadereConstants as tc


class VadereMiscAPI(Domain):
    def __init__(self):
        Domain.__init__(self, "v_misc",tc.CMD_GET_V_MISC_VARIABLE, tc.CMD_SET_V_MISC_VARIABLE, 
                                tc.CMD_SUBSCRIBE_V_MISC_VARIABLE, tc.RESPONSE_SUBSCRIBE_V_MISC_VARIABLE, 
                                tc.CMD_SUBSCRIBE_V_MISC_CONTEXT, tc.RESPONSE_SUBSCRIBE_V_MISC_CONTEXT)

    def create_target_changer(self, data):
        self._setCmd(tc.VAR_ADD_TARGET_CHANGER, "", "s", data)

    def add_stimulus_infos(self, data):
        self._setCmd(tc.VAR_ADD_STIMULUS_INFOS, "", "s", data)

    def get_all_stimulus_infos(self):
        return self._getUniversal(tc.VAR_GET_ALL_STIMULUS_INFOS, "")

    def remove_target_changer(self, element_id):
        self._setCmd(tc.VAR_REMOVE_TARGET_CHANGER, element_id, "Error", None)

