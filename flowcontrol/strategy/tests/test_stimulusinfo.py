from unittest import TestCase
from flowcontrol.strategy.controlaction.stimulusinfo import *


class TestTimeFrame(TestCase):

    def test__default_parameter(self):
        t = TimeFrame()
        assert t.repeat == False
        assert t.waitTimeBetweenRepetition == 0.0
        assert t.startTime == 0.0
        assert t.endTime == 100000.0

    def test__json_represenation(self):
        t = TimeFrame()
        expected = '{\n    "startTime": 0.0,\n    "endTime": 100000.0,\n    "repeat": false,\n    "waitTimeBetweenRepetition": 0.0\n}'
        actual = t.toJSON()
        assert actual == expected



class TestSubPopulationFilter(TestCase):


    def test_default(self):
        filter = SubpopulationFilter()
        assert filter.get_affectedPedestrianIds() == []

    def test_single_id(self):
        filter = SubpopulationFilter(3)
        assert filter.get_affectedPedestrianIds() == [3]

    def test_multiple_ids(self):
        ids = [5, 2, 3]
        filter = SubpopulationFilter(ids)
        assert filter.get_affectedPedestrianIds() == ids

    def test__json_representation(self):
        t = SubpopulationFilter()
        expected = '{\n    "affectedPedestrianIds": []\n}'
        actual = t.toJSON()
        assert actual == expected


class TestStimulusInfo(TestCase):

    def test__json_representation(self):

        s = StimulusInfo(location=Location(areas=Rectangle()),
                         stimuli=InformationStimulus("use target [1]"))

        # just check if it is serializable
        s.toJSON()