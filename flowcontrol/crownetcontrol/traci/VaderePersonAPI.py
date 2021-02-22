#
# Generated source file. DO NOT CHANGE!

from .domain import Domain
from . import VadereConstants as tc


class VaderePersonAPI(Domain):
    def __init__(self):
        Domain.__init__(self, "v_person",tc.CMD_GET_V_PERSON_VARIABLE, tc.CMD_SET_V_PERSON_VARIABLE, 
                                tc.CMD_SUBSCRIBE_V_PERSON_VARIABLE, tc.RESPONSE_SUBSCRIBE_V_PERSON_VARIABLE, 
                                tc.CMD_SUBSCRIBE_V_PERSON_CONTEXT, tc.RESPONSE_SUBSCRIBE_V_PERSON_CONTEXT)

    def get_has_next_target(self, element_id):
        return self._getUniversal(tc.VAR_HAS_NEXT_TARGET, element_id)

    def get_next_target_list_index(self, element_id):
        return self._getUniversal(tc.VAR_NEXT_TARGET_LIST_INDEX, element_id)

    def set_next_target_list_index(self, element_id, data):
        self._setCmd(tc.VAR_NEXT_TARGET_LIST_INDEX, element_id, "i", data)

    def get_id_list(self):
        return self._getUniversal(tc.VAR_ID_LIST, "")

    def get_next_free_id(self):
        return self._getUniversal(tc.VAR_NEXT_ID, "")

    def get_id_count(self):
        return self._getUniversal(tc.VAR_COUNT, "")

    def get_free_flow_speed(self, element_id):
        return self._getUniversal(tc.VAR_SPEED, element_id)

    def set_free_flow_speed(self, element_id, data):
        self._setCmd(tc.VAR_SPEED, element_id, "d", data)

    def get_position2_d(self, element_id):
        return self._getUniversal(tc.VAR_POSITION, element_id)

    def set_position2_d(self, element_id, data):
        self._setCmd(tc.VAR_POSITION, element_id, "o", data)

    def get_position3_d(self, element_id):
        return self._getUniversal(tc.VAR_POSITION3D, element_id)

    def get_velocity(self, element_id):
        return self._getUniversal(tc.VAR_VELOCITY, element_id)

    def get_maximum_speed(self, element_id):
        return self._getUniversal(tc.VAR_MAXSPEED, element_id)

    def get_position2_dlist(self):
        return self._getUniversal(tc.VAR_POSITION_LIST, "")

    def get_length(self, element_id):
        return self._getUniversal(tc.VAR_LENGTH, element_id)

    def get_width(self, element_id):
        return self._getUniversal(tc.VAR_WIDTH, element_id)

    def get_road_id(self, element_id):
        return self._getUniversal(tc.VAR_ROAD_ID, element_id)

    def get_angle(self, element_id):
        return self._getUniversal(tc.VAR_ANGLE, element_id)

    def get_type(self, element_id):
        return self._getUniversal(tc.VAR_TYPE, element_id)

    def get_target_list(self, element_id):
        return self._getUniversal(tc.VAR_TARGET_LIST, element_id)

    def set_information(self, element_id):
        self._setCmd(tc.VAR_INFORMATION_ITEM, element_id, "Error", None)

    def set_target_list(self, element_id, data):
        self._setCmd(tc.VAR_TARGET_LIST, element_id, "l", data)

    def create_new(self, data):
        self._setCmd(tc.VAR_ADD, "", "s", data)

