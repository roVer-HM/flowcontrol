#
# Generated source file. DO NOT CHANGE!
import os
import time

from flowcontrol.crownetcontrol.traci.domains.domain import Domain
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.crownetcontrol.traci.exceptions import FatalTraCIError
import numpy as np
import json
import pandas as pd


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

    def set_sim_config(self,
                       configName = "",
                       experiment = "Experiment",
                       dateTime = None,
                       resultRootDir = None,
                       iterationVariables = "1",
                       repetition = "1",
                       outputScalarFile="",
                       outputVecFile= "",
                       seed=0,
                       useVadereSeed = 1):
        if dateTime is None:
            dateTime = str(time.time())

        if resultRootDir is None:
            resultRootDir = os.getcwd()

        self._connection.send_cmd(self._cmdSetID, tc.VAR_SIM_CONFIG, "-1", "tssssssssiB", configName, experiment, dateTime, resultRootDir, iterationVariables, repetition, outputScalarFile, outputVecFile, seed, useVadereSeed)


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

    def get_output_directory(self):
        return self._getUniversal(tc.VAR_OUTPUT_DIR, "")

    def get_data_processor_value(self, processor_id):

        test = self._getUniversal(tc.VAR_PROCESSOR, str(processor_id))
        return test

    def get_density_for_measurement_area(self, processor_id):
        measurement_id, time_step, density = self._getUniversal(tc.VAR_PROCESSOR, str(processor_id))
        return density

    def get_received_command_ids(self, processor_id):
        time_step, pedestrian_ids, command_ids = self._getUniversal(tc.VAR_PROCESSOR, str(processor_id))
        frame = pd.DataFrame(data = [pedestrian_ids, command_ids])
        frame = frame.transpose()
        frame.set_index([0], inplace=True)
        frame.index.name = "pedestrianId"
        frame.columns = ["commandId"]
        frame["timeStep"] = time_step
        return frame

    def set_output_directory(self, output_directory_path = "./vadere-server-output"):
        self._connection.send_cmd(self._cmdSetID, tc.VAR_OUTPUT_DIR, "-1", "s", output_directory_path)



    def get_sim_config(self):
        return self._getUniversal(tc.VAR_SIM_CONFIG, "")

    def send_control(self, message, model, sending_node_id="-1", obj_id = "-2"):
        """
        message: a json string
        """

        #self._connection.send_cmd(cmd_id, var_id, obj_id, "s", json)
        # send_cmd (defined in Connection [connection.py:159]) will call build_cmd. THIS function is different
        # between client and server mode!!!
        # Client: only has BaseTraCIConnection which does not override build_cmd from Connection (connection.py: 234)
        # Server: has WrappedTraCIConnection which OVERRIDES build_cmd (connection.py: 542) (self._wrap)

        self._connection.send_cmd(self._cmdSetID, tc.VAR_EXTERNAL_INPUT, obj_id, "tsss", sending_node_id, model , message)

    def init_control(self, controlModelName, controlModelType, reactionModelParameter, obj_id = "-1"):

        self._connection.send_cmd(self._cmdSetID, tc.VAR_EXTERNAL_INPUT_INIT, obj_id, "tsss", controlModelName, controlModelType, reactionModelParameter)

    def get_density_map(self, sending_node):
        result = self._setUniversal(tc.VAR_DENSITY_MAP, "-2", "ts", sending_node)
        cell_dim = result[0:2]
        cell_size = result[2:4]
        if len(result) == 4:
            print("No counts provided.")
            return cell_dim, cell_size, None

        result = result[4:]
        if len(result) % 3 == 0:
            result = np.array(result).reshape(int(len(result) / 3), 3)
            result[:, 0] = result[:, 0] * cell_size[0] # x-coordinate of left lower corner
            result[:, 1] = result[:, 1] * cell_size[1] # y-coordinate of left lower corner
        else:
            raise FatalTraCIError("Expected double list of shape (n/3 , 3)")

        return cell_dim, cell_size, result

    def get_obstacles(self):
        obstacles = self._getUniversal(tc.VAR_OBSTACLES, "")
        return json.loads(obstacles)



