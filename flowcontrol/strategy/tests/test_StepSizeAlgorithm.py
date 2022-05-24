from unittest import TestCase

import numpy as np

from flowcontrol.strategy.timestepping.StepSizeAlgorithm import *

class TestVelocityBasedStepSize(TestCase):

    def test__next_step_size(self):
        f = 2.0
        velocity = 1.5
        velocity_based_alg = VelocityBasedStepSize(factor=f)
        step_size = velocity_based_alg.get_step_size_for_velocity(velocity=velocity)
        assert step_size == f*velocity

    def test__get_next_step_size(self):
        f = 2.0
        velocity = 1.5
        velocity_based_alg = VelocityBasedStepSize(min_step_size=0.0,
                                                   max_step_size=np.Inf,
                                                   factor=f)

        step_size = velocity_based_alg.get_next_step_size(velocity)
        assert step_size == f * velocity



    def test__next_get_min_velocity_size(self):
        velocity_based_alg = VelocityBasedStepSize()
        v_min_expected = 1.0

        assert v_min_expected == velocity_based_alg.get_min_velocity([v_min_expected])
        assert v_min_expected == velocity_based_alg.get_min_velocity(v_min_expected)
        assert v_min_expected == velocity_based_alg.get_min_velocity([v_min_expected, v_min_expected + 0.1])
        assert v_min_expected == velocity_based_alg.get_min_velocity(np.array([v_min_expected, v_min_expected + 0.1]))

    def test__apply_bounds_max(self):
        min = 0.4
        max = 10.0
        step_size = 12
        velocity_based_alg = VelocityBasedStepSize(min_step_size=min, max_step_size=max)
        assert max == velocity_based_alg.get_bounded_time_step(step_size)

    def test__apply_bounds_min(self):
        min = 0.4
        max = 10.0
        step_size = 0.2
        velocity_based_alg = VelocityBasedStepSize(min_step_size=min, max_step_size=max)
        assert min == velocity_based_alg.get_bounded_time_step(step_size)


    def test__apply_bounds_no_effect(self):
        min = 0.4
        max = 10.0
        step_size = 6
        velocity_based_alg = VelocityBasedStepSize(min_step_size=min, max_step_size=max)
        assert step_size == velocity_based_alg.get_bounded_time_step(step_size)

class TestDensityBasedStepSize(TestCase):

    def test__kladec_formula(self):
        density_based_alg = DensityBasedStepSize()
        test_densities = [0.0 , 0.5, 1.0,2.0,4.0, 5.4]
        expected_velocities = [1.34, 1.2983757, 1.05806286, 0.60623842, 0.15626005, 0.0]
        velocities = density_based_alg.map_density_to_velocity(test_densities)
        np.testing.assert_array_almost_equal(expected_velocities, velocities)