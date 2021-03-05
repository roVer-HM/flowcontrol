import unittest

from flowcontrol.strategy.strategies import *


class StrategyTest(unittest.TestCase):
    def _test_strategy_factory(self):
        config = {"strategy": "CorridorChoice", "params": None}
        strategy = Strategy.get_from_config(config)

        strategy_2 = CorridorChoice()
