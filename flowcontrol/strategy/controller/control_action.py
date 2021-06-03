
import abc
import json


class ControlAction:
	__metaclass__ = abc.ABCMeta

	def __init__(self, parameter_names = None, constants = None):
		self.parameter_names = parameter_names
		self.string = None
		self.constants = dict()
		self.set_constants(constants)



	def get_action_string_repr(self):
		return self.string

	def _is_parameter(self, **kwargs):
		for k in kwargs:
			if k not in self.parameter_names:
				return False
		return True


	@abc.abstractmethod
	def set_action(self, **kwargs):
		pass

	def get_constants(self):
		return self.constants

	def set_constants(self, constants):
		if constants is not None:
			self.constants.update(constants)


class CorridorChoice(ControlAction):


	def __init__(self, parameter_names, constants = None ):
		super().__init__(parameter_names=parameter_names, constants=constants)

	def set_action(self, **kwargs):
		if self._is_parameter(**kwargs):
			self.string = self.constants.copy()
			self.string.update(kwargs)

		return json.dumps(self.string, sort_keys=True)

