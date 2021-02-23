#
# Generated source file. DO NOT CHANGE!

from .domain import Domain
from . import VadereConstants as tc


class VaderePolygonAPI(Domain):
    def __init__(self):
        Domain.__init__(self, "v_polygon",tc.CMD_GET_V_POLYGON_VARIABLE, tc.CMD_SET_V_POLYGON_VARIABLE, 
                                tc.CMD_SUBSCRIBE_V_POLYGON_VARIABLE, tc.RESPONSE_SUBSCRIBE_V_POLYGON_VARIABLE, 
                                tc.CMD_SUBSCRIBE_V_POLYGON_CONTEXT, tc.RESPONSE_SUBSCRIBE_V_POLYGON_CONTEXT)

    def get_topography_bounds(self):
        return self._getUniversal(tc.VAR_TOPOGRAPHY_BOUNDS, "")

    def get_idlist(self):
        return self._getUniversal(tc.VAR_ID_LIST, "")

    def get_idcount(self):
        return self._getUniversal(tc.VAR_COUNT, "")

    def get_type(self, element_id):
        return self._getUniversal(tc.VAR_TYPE, element_id)

    def get_shape(self, element_id):
        return self._getUniversal(tc.VAR_SHAPE, element_id)

    def get_centroid(self, element_id):
        return self._getUniversal(tc.VAR_CENTROID, element_id)

    def get_distance(self, element_id, data):
        return self._getUniversal(tc.VAR_DISTANCE, element_id, data)

    def get_color(self, element_id):
        return self._getUniversal(tc.VAR_COLOR, element_id)

    def get_position2_d(self, element_id):
        return self._getUniversal(tc.VAR_POSITION, element_id)

    def get_image_file(self, element_id):
        return self._getUniversal(tc.VAR_IMAGEFILE, element_id)

    def get_image_width(self, element_id):
        return self._getUniversal(tc.VAR_WIDTH, element_id)

    def get_image_height(self, element_id):
        return self._getUniversal(tc.VAR_HEIGHT, element_id)

    def get_image_angle(self, element_id):
        return self._getUniversal(tc.VAR_ANGLE, element_id)

