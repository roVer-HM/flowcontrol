from unittest import TestCase
from flowcontrol.strategy.controller import ControlAction, CorridorChoice


class TestControlAction(TestCase):
	def test__check_action(self):
		p = ["p1", "p2"]
		action = ControlAction(parameter_names=p)
		kw = {"p1": 1.0, "p2": 2.0}
		self.assertEqual(action._is_parameter(**kw), True)

	def test__check_action_2(self):
		p = ["p1", "p2"]
		action = ControlAction(parameter_names=p)
		kw = {"p3": 1.0, "p2": 2.0}
		self.assertEqual(action._is_parameter(**kw), False)

	def test__ControlAction(self):
		const = {"c1": "OSM", "c2": "targetsIds"}
		action = ControlAction(constants=const)
		c = action.get_constants()
		self.assertEqual(len(c.keys()), 2)

	def test__ControlAction_2(self):
		action = ControlAction()
		c = action.get_constants()
		self.assertEqual(len(c.keys()), 0)


class TestCorridorChoice(TestCase):


	def test_set_action(self):
		p = ["p1", "p2"]
		constants = {"targetIDs": [1, 2, 3], "modelName": "CorridorChoice"}
		action = CorridorChoice(constants=constants, parameter_names=p)

		p_new = {"p1": 1.0, "p2" : 2.0}
		c = action.set_action(**p_new)
		should = '{"modelName": "CorridorChoice", "p1": 1.0, "p2": 2.0, "targetIDs": [1, 2, 3]}'
		self.assertEqual(should, c)




