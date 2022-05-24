from unittest import TestCase, expectedFailure

from flowcontrol.strategy.controller.control_algorithm import *



class TestAlternateTargetAlgorithm(TestCase):

    def test__alternating(self):

        alternate_target_alg = AlternateTargetAlgorithm(alternate_targets=[2,7,4], first_target_index=1)
        targets = [7,4,2,7,4,2,7,4,2]
        targets_actual = [alternate_target_alg.get_next_target() for __ in targets]
        self.assertEqual(targets_actual, targets)


class TestMinimalDensityAlgorithm(TestCase):


    def test__get_target(self):
        target_expected = 5
        minimal_density_alg = MinimalDensityAlgorithm(alternate_targets=[2,target_expected,21,1])
        densities = [1.3, 0.2, 0.2, 0.9]
        target = minimal_density_alg.get_next_target(densities)
        self.assertEqual(target, target_expected)

    def test__get_target_long_preferred(self):
        target_expected = 21
        minimal_density_alg = MinimalDensityAlgorithm(alternate_targets=[2,5,target_expected,1],
                                                      is_prefer_short_routes=False)
        densities = [1.3, 0.2, 0.2, 0.9]
        target = minimal_density_alg.get_next_target(densities)
        self.assertEqual(target, target_expected)

    @expectedFailure
    def test__fail_target_duplicates(self):
        minimal_density_alg = MinimalDensityAlgorithm(alternate_targets=[2,5,5,1])
        minimal_density_alg.get_next_target(densities=None)

    @expectedFailure
    def test__fail_density_vector_size_does_not_match(self):
        minimal_density_alg = MinimalDensityAlgorithm(alternate_targets=[2,5,1])
        minimal_density_alg.get_next_target(densities=[0.,0.])

    @expectedFailure
    def test__fail_zero_densities_not_allowed(self):
        minimal_density_alg = MinimalDensityAlgorithm(alternate_targets=[2, 5, 1])
        minimal_density_alg.get_next_target(densities=[0., 0., -1.0])





