from unittest import TestCase, expectedFailure
from flowcontrol.strategy.timestepping.timestepping import *
from flowcontrol.strategy.timestepping.StepSizeAlgorithm import DensityBasedStepSize

class TestFixedTimeStepper(TestCase):

    def test_is_active(self):
        fixed_stepper = FixedTimeStepper(start_time=2.0, end_time= 10.0)
        self.assertFalse(fixed_stepper.is_active(1.0))
        self.assertTrue(fixed_stepper.is_active(2.0))
        self.assertFalse(fixed_stepper.is_active(11.0))

    def test__forward_time(self):
        fixed_stepper = FixedTimeStepper(start_time=2.0, end_time=10.0, time_step_size=10.0)

        self.assertAlmostEqual(fixed_stepper.get_time(), 2.0)
        self.assertAlmostEqual(fixed_stepper.get_next_time(), np.inf)
        self.assertAlmostEqual(fixed_stepper.get_time(), np.inf)

    @expectedFailure
    def test__discretization(self):
        fixed_stepper = FixedTimeStepper(start_time=2.0, end_time= 10.0, time_step_size=0.7)

        self.assertFalse(fixed_stepper.is_active(1.0))

class TestAdaptiveTimeSteppe(TestCase):

    def test__forward_time(self):
        density = 1.0
        time_expected = 7.290314280
        alg = DensityBasedStepSize(factor=5.0)

        adaptive_stepper = AdaptiveTimeStepper(start_time=2.0,
                                               end_time=100.0,
                                               algorithm=alg)

        self.assertAlmostEqual(adaptive_stepper.get_time(), 2.0)
        self.assertAlmostEqual( adaptive_stepper.get_next_time(sensor_data=density), time_expected)






