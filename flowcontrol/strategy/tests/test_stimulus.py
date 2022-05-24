from unittest import TestCase
from flowcontrol.strategy.controlaction.stimulus import *


class TestStimuli(TestCase):


    def test__wait(self):
        w = Wait()
        assert w.STIMULUSTYPE == "Wait"

    def test__wait_json(self):
        w = Wait()
        expected = '{\n    "type": "Wait"\n}'
        actual = w.toJSON()
        assert expected == actual


    def test__change_target(self):
        ct = ChangeTarget()
        assert ct.STIMULUSTYPE == "ChangeTarget"

    def test__change_target_json(self):
        w = ChangeTarget(55)
        expected = '{\n    "type": "ChangeTarget",\n    "newTargetIds": [\n        55\n    ]\n}'
        actual = w.toJSON()
        assert expected == actual


    def test__change_target_id_none(self):
        ct = ChangeTarget()
        assert ct.get_newTargetIds() == []

    def test__change_target_id_int(self):
        id = 2
        ct = ChangeTarget(target_id=id)
        assert ct.get_newTargetIds() == [id]

    def test__change_target_id_list(self):
        id = [2, 3]
        ct = ChangeTarget(target_id=id)
        assert ct.get_newTargetIds() == [2]

    def test__distance_recommendation(self):
        dr = DistanceRecommendation()
        assert dr.STIMULUSTYPE == "DistanceRecommendation"

    def test__distance_recommendation_json(self):
        dr = DistanceRecommendation()
        expected = '{\n    "type": "DistanceRecommendation",\n    "socialDistance": 1.5,\n    "cloggingTimeAllowedInSecs": 5.0\n}'
        actual = dr.toJSON()
        assert expected == actual


    def test__information_stimulus(self):
        w = InformationStimulus()
        assert w.STIMULUSTYPE == "InformationStimulus"

    def test__information_stimulus_json(self):
        info = "this is a test"
        is_ = InformationStimulus(info)
        expected = '{\n    "type": "InformationStimulus",\n    "information": "this is a test"\n}'
        actual = is_.toJSON()
        assert expected == actual



