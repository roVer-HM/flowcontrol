import os
import unittest

from ..scenario import get_scenario_file

class Scenario(unittest.TestCase):

	def test_get_scenario_top_level(self):
		scenario_name = "scenario002.scenario"
		scenario_path = get_scenario_file(scenario_name)
		file_correct = os.path.join(os.getcwd(), f"opp/tests/{scenario_name}")
		self.assertEqual(scenario_path, file_correct)

	def test_get_scenario_sub_dir(self):
		scenario_name = "scenario004.scenario"
		scenario_path = get_scenario_file(scenario_name)
		file_correct = os.path.join(os.getcwd(), f"opp/tests/vadere/scenarios/{scenario_name}")
		self.assertEqual(scenario_path, file_correct)

	def test_get_scenario_from_omnet(self):
		ini_name = "omnetpp_5.ini"
		scenario_path = get_scenario_file(ini_name, config="final")
		file_correct = os.path.join(os.getcwd(), f"opp/tests/vadere/scenarios/simple_detour_100x177_miat1.25.scenario")
		self.assertEqual(scenario_path, file_correct)




