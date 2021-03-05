import abc

from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.crownetcontrol.traci.domains.VaderePersonAPI import VaderePersonAPI
from flowcontrol.crownetcontrol.traci.domains.domain import SubscriptionResults


class process_cmd:
    def __init__(self, data):
        self.cmd = data["cmd"]

    def __call__(self, fn):
        fn.__setattr__("cmd", self.cmd)
        return fn


class SubscriptionListener(object):
    __metaclass__ = abc.ABCMeta
    """
    ref_id: objectID
    """
    GLOBAL_OBJECT_ID = ""
    ALL_OBJECTS = "*"  # all objects ids exept "-1"

    def __init__(self, name, handle_dict: dict, init_sub=False):
        self.name = name
        self.handle_dict = handle_dict
        self._data = {}
        self._init_sub = init_sub

        # prepare cmd map
        self.f_map: dict = {}
        for key in [i for i in dir(self) if not i.startswith("__")]:
            __o = self.__getattribute__(key)
            if callable(__o):
                try:
                    __cmd = __o.__getattribute__("cmd")
                    self.f_map[__cmd] = __o
                except AttributeError:
                    continue

    def check_cmd(self, cmd):
        """
        check if ref_is is handled by this listener
        """
        return cmd in self.handle_dict.keys()

    def handle_subscription_result(self, results: dict):
        self.rest_data()
        for cmd, result in results.items():
            if cmd in self.handle_dict.keys():
                # call decorated method
                self.f_map[cmd](result)

    def subscribe(self, dom_handler):
        if not self._init_sub:
            return
        for cmd_id, subscription_map in self.handle_dict.items():
            if dom_handler.has_domain_for(cmd_id):
                dom = dom_handler.dom_for_cmd(cmd_id)
                for object_id, var_list in subscription_map.items():
                    if object_id != self.ALL_OBJECTS:
                        # only subscribe to GLOBAL_OBJECT_ID or 'real' ids (--> skip ALL_OBJECTS flag)
                        dom.subscribe(objectID=object_id, varIDs=var_list)

    @abc.abstractmethod
    def rest_data(self):
        pass

    @property
    def data(self):
        return self._data


class VadereDefaultStateListener(SubscriptionListener):
    @classmethod
    def with_vars(cls, name, var_list: dict, **kwargs):
        _handle = {
            tc.RESPONSE_SUBSCRIBE_V_PERSON_VARIABLE: {
                cls.GLOBAL_OBJECT_ID: [tc.VAR_ID_LIST],
                cls.ALL_OBJECTS: var_list,
            },
            tc.RESPONSE_SUBSCRIBE_V_SIM_VARIABLE: {
                cls.GLOBAL_OBJECT_ID: [
                    tc.VAR_TIME,
                    tc.VAR_DEPARTED_PEDESTRIAN_IDS,
                    tc.VAR_ARRIVED_PEDESTRIAN_PEDESTRIAN_IDS,
                ]
            },
        }
        return cls(name, _handle, **kwargs)

    def __init__(self, name, handle_dict, **kwargs):
        super().__init__(name, handle_dict, **kwargs)
        self.rest_data()

    def rest_data(self):
        self._data = {
            "all_ped_ids": [],
            "removed_ped_ids": [],
            "new_ped_ids": [],
            "time": -1,
            "pedestrians": [],
        }

    @property
    def new_pedestrian_ids(self):
        return self._data.get("new_ped_ids", [])

    @property
    def removed_pedestrian_ids(self):
        return self._data.get("removed_ped_ids", [])

    @property
    def pedestrian_id_list(self):
        return self._data.get("all_ped_ids", [])

    @property
    def pedestrians(self):
        return self._data.get("pedestrians", [])

    @property
    def time(self):
        return self._data.get("time", -1)

    def update_pedestrian_subscription(
        self,
        api: VaderePersonAPI,
        begin=tc.INVALID_DOUBLE_VALUE,
        end=tc.INVALID_DOUBLE_VALUE,
    ):
        vars = [
            v
            for _, v in self.handle_dict[tc.RESPONSE_SUBSCRIBE_V_PERSON_VARIABLE][
                self.ALL_OBJECTS
            ].items()
        ]
        for obj_id in self.new_pedestrian_ids:
            api.subscribe(objectID=obj_id, varIDs=vars, begin=begin, end=end)

        for obj_id in self.removed_pedestrian_ids:
            api.unsubscribe(obj_id)

    @process_cmd({"cmd": tc.RESPONSE_SUBSCRIBE_V_SIM_VARIABLE})
    def _handle_sim(self, result: SubscriptionResults):
        # simulation sub global
        _res = result.data[self.GLOBAL_OBJECT_ID]
        self._data["new_ped_ids"] = list(_res[tc.VAR_DEPARTED_PEDESTRIAN_IDS])
        self._data["removed_ped_ids"] = _res[tc.VAR_ARRIVED_PEDESTRIAN_PEDESTRIAN_IDS]
        self._data["time"] = _res[tc.VAR_TIME]

    @process_cmd({"cmd": tc.RESPONSE_SUBSCRIBE_V_PERSON_VARIABLE})
    def _handle_person(self, result: SubscriptionResults):
        _data = {}
        # person sub global
        if self.GLOBAL_OBJECT_ID in result.data:
            _res = result.data[self.GLOBAL_OBJECT_ID]
            self._data["all_ped_ids"] = list(_res[tc.VAR_ID_LIST])
        else:
            self._data["all_ped_ids"] = []

        # person sub for ALL_OBJECTS
        person_vars = self.handle_dict[tc.RESPONSE_SUBSCRIBE_V_PERSON_VARIABLE].get(
            self.ALL_OBJECTS, {}
        )
        if person_vars != {}:
            for obj_id, vars in result.data.items():
                if obj_id == self.GLOBAL_OBJECT_ID:
                    continue
                _ped = {"id": obj_id}
                for var_name, var_id in person_vars.items():
                    _ped.setdefault(var_name, vars[var_id])
                self._data["pedestrians"].append(_ped)
