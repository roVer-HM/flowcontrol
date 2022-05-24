import abc

import json

class JsonRepresentation(abc.ABC):

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)