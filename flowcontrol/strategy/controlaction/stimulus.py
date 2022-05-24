from typing import Union, List

from flowcontrol.strategy.controlaction.json import JsonRepresentation

class Stimulus(JsonRepresentation):
    pass


class Wait(Stimulus):

    STIMULUSTYPE = "Wait"

    def __init__(self):
        self.type = Wait.STIMULUSTYPE


class ChangeTarget(Stimulus):

    STIMULUSTYPE = "ChangeTarget"

    def __init__(self, target_id : Union[int, List[int]] = None):
        self.type = ChangeTarget.STIMULUSTYPE

        if target_id == None:
            target_id = list()

        self.set_target_id(target_id)


    def get_newTargetIds(self):

        return self.newTargetIds

    def set_target_id(self, target_id : Union[int, List[int]]):
        if isinstance(target_id, int):
            target_id = [target_id]

        if len(target_id) == 0:
            print(f"WARNING: ChangeTarget stimulus: no target id set.")
        elif len(target_id) > 1:
            print(f"WARNING: Only one target id allowed. Got: {target_id}. Use: {target_id[:1]}.")
            target_id = target_id[:1]

        self.newTargetIds = target_id


class DistanceRecommendation(Stimulus):

    STIMULUSTYPE = "DistanceRecommendation"

    def __init__(self, socialDistance : float = 1.5, cloggingTimeAllowedInSecs : float = 5.0):
        self.type = DistanceRecommendation.STIMULUSTYPE
        self.socialDistance = socialDistance
        self.cloggingTimeAllowedInSecs = cloggingTimeAllowedInSecs

class InformationStimulus(Stimulus):

    STIMULUSTYPE = "InformationStimulus"

    def __init__(self, information : str = "information xyz"):
        self.type = InformationStimulus.STIMULUSTYPE
        self.information = information