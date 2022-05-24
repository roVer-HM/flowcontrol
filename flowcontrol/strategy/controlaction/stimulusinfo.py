

from typing import Union, List
from flowcontrol.strategy.controlaction.area import Shape, Rectangle
from flowcontrol.strategy.controlaction.stimulus import InformationStimulus, Stimulus
from flowcontrol.strategy.controlaction.json import JsonRepresentation


class TimeFrame(JsonRepresentation):

    def __init__(self, start_time = 0.0,
                 end_time = 100000.0, # simulation end time
                 repeat: bool = False,
                 waitTimeBetweenRepetition = 0.0):

        self.startTime = start_time
        self.endTime = end_time
        self.repeat = repeat
        self.waitTimeBetweenRepetition = waitTimeBetweenRepetition



class Location(JsonRepresentation):

    def __init__(self, areas: Union[Shape, List[Shape]] = None):
        self.set_areas(areas=areas)

    def set_areas(self, areas):
        if areas == None:
            areas = list()
        if isinstance(areas, Shape):
            areas = [areas]
        self.areas = areas

class SubpopulationFilter(JsonRepresentation):

    def __init__(self, affectedPedestrianIds : Union[List[int], int] = None):
        self.set_affectedPedestrianIds(affectedPedestrianIds)

    def set_affectedPedestrianIds(self, affectedPedestrianIds):
        if affectedPedestrianIds == None:
            affectedPedestrianIds = list()
        if isinstance(affectedPedestrianIds, int):
            affectedPedestrianIds = [affectedPedestrianIds]
        self.affectedPedestrianIds = affectedPedestrianIds

    def get_affectedPedestrianIds(self):
        return self.affectedPedestrianIds


class StimulusInfo(JsonRepresentation):

    def __init__(self, timeframe: TimeFrame = None,
                 location : Location = None,
                 subpopulationFilter : SubpopulationFilter = None,
                 stimuli = None):
        self.set_time_frame(timeframe)
        self.set_location(location)
        self.set_sub_population_filter(subpopulationFilter)
        self.set_stimuli(stimuli)

    def set_location(self, location):
        if location == None:
            location = Location()
        self.location = location

    def set_sub_population_filter(self, subpopulationFilter):
        if subpopulationFilter == None:
            subpopulationFilter = SubpopulationFilter()
        self.subpopulationFilter = subpopulationFilter

    def set_stimuli(self, stimuli):
        if stimuli == None:
            stimuli = list()
        if isinstance(stimuli, Stimulus):
            stimuli = [stimuli]
        self.stimuli = stimuli

    def set_time_frame(self, timeframe):
        if timeframe == None:
            timeframe = TimeFrame()
        self.timeframe = timeframe



if __name__ == "__main__":

    pass


