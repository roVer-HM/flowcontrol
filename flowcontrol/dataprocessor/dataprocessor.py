import abc
import io
from typing import List, Union
import numpy as np

import pandas as pd
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
        self._file = open(file_path, mode="w", encoding="utf_8", buffering=buffer_config)
        self._is_write_header = True

    def write(self, data : pd.DataFrame):
        data.to_csv(self._file, header=self._is_write_header, sep=" ")
        self._is_write_header = False

    def finish(self):
        self._file.close()


class Processor:

    def __init__(self, file_name, is_use_buffer = True, user_defined_header = None):
        self.writer = Writer(file_name, is_use_buffer)
        self.indices = list()
        self.current_time_step = 0
        self.user_defined_header = user_defined_header

    def is_valid_state(self, data_frame):
        return self.is_index_valid(data_frame)

    def update_time_step(self, time_step):
        self.current_time_step = time_step

    def write(self, *data):
        data_frame = self.format_data(*data)
        if self.is_valid_state(data_frame):
            self.writer.write(data_frame)

    def finish(self):
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


class ControlActionCmdId(Processor):

    def __init__(self, file_name, is_use_buffer = True):
        super().__init__(file_name, is_use_buffer= is_use_buffer)

    def get_col_names(self, param):
        return ["commandId"]

    def is_command_id_valid(self, data_frame):
        d = data_frame.values[0]
        if isinstance(d, int) is False or d <= 0:
            print(f"INFO: Got command id {d}: Command id must be of type int and > 0.")


class CorridorRecommendation(Processor):

    def __init__(self, file_name, is_use_buffer=True):
        super().__init__(file_name, is_use_buffer=is_use_buffer)

    def get_col_names(self, param):
        return ["corridorRecommended"]


class DensityMeasurements(Processor):

    def __init__(self, file_name, user_defined_header, is_use_buffer=True):
        super().__init__(file_name, is_use_buffer=is_use_buffer, user_defined_header=user_defined_header)






class Manager:

    def __init__(self, simulation_step_size = 0.4):
        self.processor = dict()
        self.sim_time_step_size = simulation_step_size

    def update_sim_time(self, sim_time = None):
        step = int(np.round(sim_time / self.sim_time_step_size))
        self.update_time_step(step)

    def update_time_step(self, time_step = None):
        for proc in self.processor.values():
            proc.update_time_step(time_step)

    def write(self, key, *data):
        # [a, b, c, e, f]
        pc : Processor = self.processor[key]
        pc.write(*data)

    def registerProcessor(self, key, w: Processor):
        self.processor[key] = w

    def finish(self):
        [f.finish() for f in self.processor.values()]



if __name__ == "__main__":
    pass



