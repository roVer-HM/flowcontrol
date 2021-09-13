import abc
import io
import os.path
from typing import List, Union
import numpy as np

import pandas as pd
import time
#
# class Writer:
#
#     def __init__(self, file_path):
#         self.file_path = file_path
#
#     def write(self, file_path):
#         self.file_path = file_path
#
#     def finish(self):
#         pass
#
# class BufferWriter(Writer):
#
#     def __ini__(self, file_path):
#         self._file_buffer = open(file_path, mode="w", encoding="utf-8", buffering=1)
#
#     def write(self, *data):
#         self._file_buffer.write(*data)
#
#     def finish(self):
#         self._file_buffer.close()

class Writer:

    def __init__(self, file_path, write_to_buffer=True):
        buffer_config=None
        if write_to_buffer:
            buffer_config = 1 # line buffering (only usable in text mode), and an integer > 1 to indicate the size of a fixed-size chunk buffer.
        self.file_path = file_path
        self._file = open(file_path, mode="w", encoding="utf_8", buffering=buffer_config)
        self._is_write_header = True

    def write(self, data : pd.DataFrame):
        data.to_csv(self._file, header=self._is_write_header, sep=" ")
        self._is_write_header = False

    def finish(self):
        self._file.close()

    def get_file_path(self):
        return self.file_path


class Processor:

    def __init__(self, writer: Writer = None, user_defined_header = None, is_store_data = True):
        self.writer = writer
        self.indices = list()
        self.current_time_step = 0
        self.user_defined_header = user_defined_header
        self.is_store_data = is_store_data
        self.storage = None

    def set_output_dir_path(self, output_dir):
        self.output_dir = output_dir

    def is_valid_state(self, data_frame):
        return self.is_index_valid(data_frame)
    
    def get_values(self):
        if self.storage is None:
            raise ValueError("Only available if is_store_data is set to True.")
        return self.storage
    
    def update_time_step(self, time_step):
        self.current_time_step = time_step
        
    def append_data(self, *data):
        if self.storage is None:
            self.storage = self.format_data(*data)
        else:
            data_frame = self.format_data(*data)
            self.storage = pd.concat([self.storage, data_frame])

    def write(self, *data):
        data_frame = self.format_data(*data)
        if self.is_valid_state(data_frame):
            if self.writer is not None:
                self.writer.write(data_frame)
            if self.is_store_data:
                self.append_data(*data)

    def finish(self, *args):
        self.writer.finish()

    def format_data(self, *data):
        if self.user_defined_header is None:
            col_names = self.get_col_names(*data)
        else:
            col_names = self.user_defined_header

        frame = pd.DataFrame(data=[data], columns=col_names)
        frame.index = frame.index + self.current_time_step
        frame.index.name = "timeStep"
        return frame

    def is_index_valid(self, data_frame : pd.DataFrame):
        inds = data_frame.index.values
        if inds in self.indices:
            raise ValueError("Duplicate indices.")
        return True

    @abc.abstractmethod
    def get_col_names(self, param):
        pass

    def post_loop(self, param):
        pass


class ControlActionCmdId(Processor):

    def __init__(self, writer: Writer = None):
        super().__init__(writer)

    def get_col_names(self, param):
        return ["commandId"]

    def is_command_id_valid(self, data_frame):
        d = data_frame.values[0]
        if isinstance(d, int) is False or d <= 0:
            print(f"INFO: Got command id {d}: Command id must be of type int and > 0.")


class CorridorRecommendation(Processor):

    def __init__(self, writer : Writer = None):
        super().__init__(writer)

    def get_col_names(self, param):
        return ["corridorRecommended"]


class DensityMeasurements(Processor):

    def __init__(self, writer : Writer, user_defined_header):
        super().__init__(writer, user_defined_header=user_defined_header)


class SendingTimes(Processor):
    def __init__(self, writer : Writer = None):
        super().__init__(writer)

    def write(self, *data):
        if self.is_valid_storage_data():
            if self.storage is None:
                self.storage = data[0]
            else:
                self.storage = pd.concat([self.storage, data[0]])

    def post_loop(self, commandIds : pd.DataFrame):
        self.commandIds = commandIds

    def finish(self, *args):

        sending_times = self.compute_sending_times()
        file_name = self.writer.get_file_path()
        sending_times.to_csv(file_name, sep= " ")

    def compute_sending_times(self):
        commandIdsSent = self.commandIds
        commandIdsReceived = self.storage

        statistics = None
        for time_step, commandId in commandIdsSent.iterrows():
            times = commandIdsReceived[commandIdsReceived["commandId"] == commandId.values[0]]
            times["timeStep"] = times["timeStep"] - time_step
            times.reset_index(inplace=True)
            times.set_index('commandId', inplace=True)
            pd.DataFrame(times["timeStep"].describe().transpose())
            stats = pd.DataFrame(times["timeStep"].describe()).rename(columns={"timeStep": time_step}).transpose()
            stats.index.name = "timeStep"
            if statistics is None:
                statistics = stats
            else:
                statistics = pd.concat([statistics, stats], axis=0)
        return statistics

    def is_valid_storage_data(self, *data):
        return True


class Manager:


    def __init__(self, simulation_step_size = 0.4):
        self.processor = dict()
        self.postprocessors = dict()
        self.sim_time_step_size = simulation_step_size

    def update_sim_time(self, sim_time = None):
        step = int(np.round(sim_time / self.sim_time_step_size)) + 1 # +1 is necessary because 0.0s -> timeStep 1
        self.update_time_step(step)

    def update_time_step(self, time_step = None):
        for proc in self.processor.values():
            proc.update_time_step(time_step)

    def write(self, key, *data):
        # [a, b, c, e, f]
        pc : Processor = self.processor[key]
        pc.write(*data)

    def post_loop(self, key, *data):
        # [a, b, c, e, f]
        pc : Processor = self.processor[key]
        pc.post_loop(*data)

    def registerProcessor(self, key, w: Processor):
        self.processor[key] = w

    def finish(self):
        [f.finish() for f in self.processor.values()]

    def get_processor_values(self, key):
        pc: Processor = self.processor[key]
        return pc.get_values()

    def set_output_dir(self, output_dir_path):
        for proc in self.processor.values():
            proc.set_output_dir_path(output_dir_path)



if __name__ == "__main__":
    pass



