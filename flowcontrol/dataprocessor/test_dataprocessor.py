import os
from unittest import TestCase, main
import numpy as np
import pandas as pd
from flowcontrol.dataprocessor.dataprocessor import Processor, Writer, Manager, ControlActionCmdId, DensityMeasurements


class DataProcessors(TestCase):
    def test__Writer(self):
        file = "output.txt"
        list_writer = Writer(file)
        for index in np.arange(0, 100):
            frame = pd.DataFrame(data=[[index*-1, index, index*-1]], columns=["feature1", "f2", "f3"])
            frame.index = (frame.index + index)*0.4
            frame.index.name = "timeStep"
            list_writer.write(frame)
        list_writer.finish()
        is_ = pd.read_csv(file, sep=" ", header=[0])
        should_ = pd.read_csv("testRessources/output_2.txt", sep=" ", header=[0])
        os.remove(file)

        assert is_.equals(should_)


    def test__Manager(self):
        file = "commandId.txt"

        mg = Manager()
        mg.registerProcessor("commandIdProcessor", ControlActionCmdId(file))
        mg.update_time_step(1)
        mg.write("commandIdProcessor", 4)
        mg.update_time_step(2)
        mg.write("commandIdProcessor", 4)
        mg.finish()

        is_ = pd.read_csv(file, sep=" ", header=[0])
        should_ = pd.read_csv("testRessources/commandId_2.txt", sep=" ", header=[0])
        os.remove(file)
        assert is_.equals(should_)


    def test__DensityMeasurements(self):
        file = "densities.txt"
        dens = DensityMeasurements(file, ["area1", "area2"])
        dens.update_time_step(5)
        dens.write(*[1.0,2.2])
        dens.finish()

        is_ = pd.read_csv(file, sep=" ", header=[0])
        should_ = pd.read_csv("testRessources/densities_2.txt", sep=" ", header=[0])
        os.remove(file)
        assert is_.equals(should_)



if __name__ == '__main__':
    main()
