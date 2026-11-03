"""Unit tests for the pure calculation core. Standard library only.

Run with:  python -m unittest discover -s tests -v
"""

from __future__ import annotations

import math
import time
import unittest

import gearbox as gb

# The design used as a reference throughout the tests:
#   m = 2 mm, N = 3 planets, i = 4  ->  Zs = 18, Zr = 54, Zp = 18
# Its ring measures 113 mm outside, so the envelope must allow at least that.
REFERENCE_ARGS = dict(module=2.0, n_planets=3, i_requested=4.0)


class ReferenceSolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0)
        cls.best = cls.result.best

    def test_reference_solution_is_the_expected_tooth_set(self) -> None:
        self.assertTrue(self.result.ok)
        self.assertIsNotNone(self.best)
        self.assertEqual(
            (self.best.z_sun, self.best.z_planet, self.best.z_ring), (18, 18, 54)
        )

    def test_reference_solution_is_fully_valid(self) -> None:
        self.assertTrue(self.best.valid)
        self.assertEqual(self.best.failed_checks, ())

    def test_reference_ratio_is_exact(self) -> None:
        self.assertAlmostEqual(self.best.i_real, 4.0, places=9)
        self.assertAlmostEqual(self.best.ratio_deviation, 0.0, places=12)

    def test_reference_pitch_diameters_follow_the_module(self) -> None:
        self.assertAlmostEqual(self.best.d_sun, 36.0)
        self.assertAlmostEqual(self.best.d_planet, 36.0)
        self.assertAlmostEqual(self.best.d_ring, 108.0)
        self.assertAlmostEqual(self.best.d_carrier, 72.0)
        self.assertAlmostEqual(self.best.d_ext, 113.0)

    def test_module_scales_the_geometry_linearly(self) -> None:
        small = gb.solve_planetary(1.0, 3, 4.0, 60.0).best
        large = gb.solve_planetary(2.0, 3, 4.0, 120.0).best
        self.assertEqual((small.z_sun, small.z_ring), (large.z_sun, large.z_ring))
        self.assertAlmostEqual(large.d_ext, 2 * small.d_ext)


class DesignConditionTests(unittest.TestCase):
    """One test per condition: they must hold on any valid solution."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.best = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0).best

    def test_concentricity_condition_holds(self) -> None:
        self.assertEqual(self.best.z_ring, self.best.z_sun + 2 * self.best.z_planet)

    def test_assembly_condition_holds(self) -> None:
        self.assertEqual((self.best.z_sun + self.best.z_ring) % self.best.n_planets, 0)

    def test_adjacency_condition_holds(self) -> None:
        lhs = (self.best.z_sun + self.best.z_planet) * math.sin(
            math.pi / self.best.n_planets
        )
        rhs = self.best.z_planet + gb.ADJACENCY_CLEARANCE
        self.assertGreater(lhs, rhs)

    def test_envelope_condition_holds(self) -> None:
        self.assertLessEqual(self.best.d_ext, 120.0 + 1e-9)

    def test_every_returned_solution_satisfies_the_structural_conditions(self) -> None:
        for d_max in (150.0, 200.0, 400.0):
            result = gb.solve_planetary(2.0, 4, 5.0, d_max)
            for solution in (result.best, *result.alternatives):
                if solution is None:
                    continue
                with self.subTest(d_max=d_max, z_sun=solution.z_sun):
                    self.assertTrue(solution.geometry_valid)
                    self.assertEqual(
                        solution.z_ring, solution.z_sun + 2 * solution.z_planet
                    )
                    self.assertEqual(
                        (solution.z_sun + solution.z_ring) % solution.n_planets, 0
                    )
                    self.assertLessEqual(solution.d_ext, d_max + 1e-9)
                    self.assertGreaterEqual(solution.z_sun, gb.MIN_TEETH_SUN)
                    self.assertGreaterEqual(solution.z_planet, gb.MIN_TEETH_PLANET)

    def test_checks_expose_the_four_mandatory_conditions(self) -> None:
        keys = {check.key for check in self.best.checks}
        self.assertLessEqual(
            {"concentricity", "assembly", "adjacency", "envelope"}, keys
        )


class InfeasibleInputTests(unittest.TestCase):
    def test_plan_reference_envelope_of_100_mm_has_no_solution(self) -> None:
        """The 113 mm train cannot live in a 100 mm envelope, and nothing smaller can.

        Zr = 54 alone gives a 108 mm pitch diameter, so the 100 mm case is
        geometrically impossible, not merely a tight fit.
        """
        result = gb.solve_planetary(**REFERENCE_ARGS, d_max=100.0)
        self.assertFalse(result.ok)
        self.assertIsNone(result.best)
        self.assertEqual(result.message, gb.NO_SOLUTION_MESSAGE)

    def test_infeasible_result_explains_what_to_change(self) -> None:
        result = gb.solve_planetary(**REFERENCE_ARGS, d_max=100.0)
        self.assertTrue(result.suggestions)
        self.assertTrue(any("D_max" in text for text in result.suggestions))

    def test_infeasible_result_diagnoses_the_binding_constraint(self) -> None:
        result = gb.solve_planetary(**REFERENCE_ARGS, d_max=100.0)
        self.assertIn("envelope", result.diagnosis)

    def test_infeasible_result_never_raises_for_extreme_inputs(self) -> None:
        for d_max in (10.0, 20.0, 50.0):
            with self.subTest(d_max=d_max):
                result = gb.solve_planetary(2.0, 3, 4.0, d_max)
                self.assertFalse(result.ok)
                self.assertTrue(result.suggestions)

    def test_six_planets_at_ratio_four_is_infeasible(self) -> None:
        """Adjacency caps N=6 just below i = 4 for every sun size."""
        result = gb.solve_planetary(2.0, 6, 4.0, 500.0)
        self.assertFalse(result.ok)
        self.assertTrue(any("ratio" in text.lower() for text in result.suggestions))

    def test_infeasible_ratio_is_diagnosed_as_a_ratio_problem(self) -> None:
        result = gb.solve_planetary(2.0, 6, 4.0, 500.0)
        self.assertIn("no tooth combination reaches", result.diagnosis.lower())
        self.assertTrue(any("N=" in text for text in result.suggestions))

    def test_six_planets_work_at_a_ratio_their_geometry_allows(self) -> None:
        result = gb.solve_planetary(2.0, 6, 3.0, 500.0)
        self.assertTrue(result.ok)
        self.assertTrue(result.best.valid)


class RoundingBehaviourTests(unittest.TestCase):
    def test_real_ratio_is_reported_when_teeth_cannot_match_exactly(self) -> None:
        """i = 4.27 = 327/100 needs Zs >= 100, which a 500 mm envelope forbids.

        Short decimal ratios such as 4.3 = 43/10 are reachable exactly once the
        sun is a multiple of 10 teeth, so only a ratio whose reduced denominator
        exceeds the available sun range forces a deviation.
        """
        result = gb.solve_planetary(2.0, 3, 4.27, 500.0)
        self.assertTrue(result.ok)
        self.assertLess(result.best.z_sun, 100)
        self.assertNotAlmostEqual(result.best.i_real, 4.27, places=6)
        self.assertGreater(result.best.ratio_deviation, 0)
        self.assertLessEqual(
            result.best.ratio_deviation, gb.DEFAULT_RATIO_TOLERANCE + 1e-12
        )

    def test_short_decimal_ratio_is_hit_exactly_when_the_sun_can_grow(self) -> None:
        """4.3 = 43/10 is reachable with Zs = 60, Zr = 198."""
        result = gb.solve_planetary(2.0, 3, 4.3, 500.0)
        self.assertTrue(result.ok)
        self.assertAlmostEqual(result.best.i_real, 4.3, places=9)
        self.assertAlmostEqual(result.best.ratio_deviation, 0.0, places=12)

    def test_assembly_refinement_keeps_the_ratio_close_to_the_target(self) -> None:
        for ratio in (2.5, 3.0, 4.0, 5.0, 7.0, 10.0):
            with self.subTest(ratio=ratio):
                result = gb.solve_planetary(2.0, 3, ratio, 2000.0)
                self.assertTrue(result.ok)
                self.assertLessEqual(
                    result.best.ratio_deviation, gb.DEFAULT_RATIO_TOLERANCE + 1e-12
                )

    def test_odd_planet_count_solution_is_exact(self) -> None:
        """N=5 forces Zs to a multiple of 5 for i=4; Zs=20 is the first usable one."""
        result = gb.solve_planetary(2.0, 5, 4.0, 200.0)
        self.assertEqual(result.best.z_sun, 20)
        self.assertEqual(result.best.z_ring, 60)
        self.assertEqual(result.best.z_planet, 20)
        self.assertAlmostEqual(result.best.i_real, 4.0, places=9)


class ConfigurationTests(unittest.TestCase):
    """Swapping the driver changes the ratio law, not the geometry."""

    def test_default_configuration_is_the_classic_reducer(self) -> None:
        result = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0)
        self.assertEqual(result.configuration.key, gb.DEFAULT_CONFIGURATION)
        self.assertEqual(result.best.configuration.driver, "sun")
        self.assertEqual(result.best.configuration.driven, "carrier")
        self.assertEqual(result.best.configuration.fixed, "ring")

    def test_overdrive_configuration_inverts_the_same_train(self) -> None:
        """1:4 and 4:1 are the same tooth set with the driver swapped."""
        reducer = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0).best
        overdrive = gb.solve_planetary(
            2.0, 3, 1.0 / 4.0, 120.0, configuration="ring_fixed_carrier_drive"
        ).best

        self.assertEqual(
            (overdrive.z_sun, overdrive.z_planet, overdrive.z_ring),
            (reducer.z_sun, reducer.z_planet, reducer.z_ring),
        )
        self.assertAlmostEqual(overdrive.i_real, 0.25, places=9)
        self.assertEqual(overdrive.configuration.driver, "carrier")
        self.assertEqual(overdrive.configuration.driven, "sun")

    def test_reducer_configuration_rejects_a_ratio_below_one(self) -> None:
        with self.assertRaises(ValueError) as caught:
            gb.solve_planetary(2.0, 3, 0.25, 120.0)
        self.assertIn("greater than 1", str(caught.exception))

    def test_overdrive_configuration_rejects_a_ratio_above_one(self) -> None:
        with self.assertRaises(ValueError) as caught:
            gb.solve_planetary(
                2.0, 3, 4.0, 120.0, configuration="ring_fixed_carrier_drive"
            )
        self.assertIn("smaller than 1", str(caught.exception))

    def test_ratio_error_names_the_swapped_configuration(self) -> None:
        with self.assertRaises(ValueError) as caught:
            gb.solve_planetary(2.0, 3, 4.0, 120.0, configuration="ring_fixed_carrier_drive")
        self.assertIn("i = 0.25", str(caught.exception))

    def test_sun_fixed_train_reaches_a_small_reduction(self) -> None:
        """Sun fixed, carrier drives, ring driven: i = 1 + Zs/Zr stays near 1."""
        result = gb.solve_planetary(2.0, 3, 1.5, 200.0, configuration="sun_fixed_carrier_drive")
        self.assertTrue(result.ok)
        self.assertTrue(result.best.valid)
        self.assertAlmostEqual(result.best.i_real, 1.5, places=9)
        self.assertEqual(
            (result.best.z_sun, result.best.z_planet, result.best.z_ring), (34, 17, 68)
        )

    def test_sun_fixed_overdrive_reaches_this_example(self) -> None:
        result = gb.solve_planetary(2.0, 3, 0.8, 200.0, configuration="sun_fixed_ring_drive")
        self.assertTrue(result.best.valid)
        self.assertAlmostEqual(result.best.i_real, 0.8, places=9)

    def test_ring_fixed_reduction_cannot_go_down_to_two(self) -> None:
        """With the ring fixed, adjacency floors the ratio near 2.5 at this size."""
        result = gb.solve_planetary(2.0, 3, 2.0, 200.0)
        self.assertTrue(result.ok)
        self.assertFalse(result.best.valid)
        self.assertIn("Ratio tolerance", [c.label for c in result.best.failed_checks])

    def test_unknown_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as caught:
            gb.solve_planetary(2.0, 3, 4.0, 120.0, configuration="not_a_train")
        self.assertIn("unknown configuration", str(caught.exception))

    def test_configuration_is_reported_in_the_serialised_result(self) -> None:
        payload = gb.solve_planetary(
            2.0, 3, 0.25, 120.0, configuration="ring_fixed_carrier_drive"
        ).to_dict()
        self.assertEqual(payload["configuration"], "ring_fixed_carrier_drive")
        self.assertEqual(payload["best"]["driver"], "carrier")


class LanguageTests(unittest.TestCase):
    """The solver reports in the requested language, numbers unchanged."""

    def test_english_is_the_default(self) -> None:
        result = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0)
        self.assertIn("Solution found", result.message)

    def test_spanish_message_is_translated(self) -> None:
        result = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0, language="es")
        self.assertIn("Solución encontrada", result.message)

    def test_spanish_keeps_the_same_numbers(self) -> None:
        english = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0)
        spanish = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0, language="es")
        self.assertEqual(
            (english.best.z_sun, english.best.z_ring), (spanish.best.z_sun, spanish.best.z_ring)
        )
        self.assertAlmostEqual(english.best.i_real, spanish.best.i_real)

    def test_spanish_check_labels_are_translated(self) -> None:
        result = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0, language="es")
        labels = [check.label for check in result.best.checks]
        self.assertIn("Concentricidad (montaje coaxial)", labels)
        self.assertIn("Envolvente de diámetro", labels)

    def test_spanish_diagnostics_are_translated(self) -> None:
        result = gb.solve_planetary(**REFERENCE_ARGS, d_max=100.0, language="es")
        self.assertIn("envolvente", result.diagnosis)
        self.assertTrue(any("D_máx" in text for text in result.suggestions))

    def test_invalid_language_falls_back_instead_of_crashing(self) -> None:
        result = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0, language="fr")
        self.assertIn("Solution found", result.message)


class AlternativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0)

    def test_alternatives_are_sorted_by_ratio_closeness(self) -> None:
        deviations = [
            solution.ratio_deviation
            for solution in (self.result.best, *self.result.alternatives)
        ]
        self.assertEqual(deviations, sorted(deviations))
        self.assertLessEqual(len(self.result.alternatives), 3)

    def test_alternatives_are_distinct_designs(self) -> None:
        tooth_sets = [
            (solution.z_sun, solution.z_ring)
            for solution in (self.result.best, *self.result.alternatives)
        ]
        self.assertEqual(len(tooth_sets), len(set(tooth_sets)))

    def test_alternatives_respect_the_requested_count(self) -> None:
        result = gb.solve_planetary(2.0, 3, 6.0, 2000.0, max_alternatives=1)
        self.assertLessEqual(len(result.alternatives), 1)


class InputValidationTests(unittest.TestCase):
    INVALID_CASES = (
        dict(module=0.0, n_planets=3, i_requested=4.0, d_max=100.0),
        dict(module=-2.0, n_planets=3, i_requested=4.0, d_max=100.0),
        dict(module=2.0, n_planets=1, i_requested=4.0, d_max=100.0),
        dict(module=2.0, n_planets=3, i_requested=1.0, d_max=100.0),
        dict(module=2.0, n_planets=3, i_requested=0.5, d_max=100.0),
        dict(module=2.0, n_planets=3, i_requested=4.0, d_max=0.0),
    )

    def test_invalid_inputs_raise_value_error(self) -> None:
        for case in self.INVALID_CASES:
            with self.subTest(**case):
                with self.assertRaises(ValueError):
                    gb.solve_planetary(**case)

    def test_ratio_at_or_below_one_is_rejected_with_an_explanation(self) -> None:
        with self.assertRaises(ValueError) as caught:
            gb.solve_planetary(2.0, 3, 1.0, 100.0)
        self.assertIn("greater than 1", str(caught.exception))


class SerialisationTests(unittest.TestCase):
    def test_result_serialises_to_a_plain_dict(self) -> None:
        payload = gb.solve_planetary(**REFERENCE_ARGS, d_max=120.0).to_dict()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["best"]["z_sun"], 18)
        self.assertAlmostEqual(payload["best"]["i_real"], 4.0)
        self.assertEqual(len(payload["best"]["checks"]), 6)
        self.assertTrue(payload["alternatives"])

    def test_infeasible_result_serialises_without_a_best_design(self) -> None:
        payload = gb.solve_planetary(**REFERENCE_ARGS, d_max=100.0).to_dict()
        self.assertFalse(payload["ok"])
        self.assertIsNone(payload["best"])
        self.assertTrue(payload["suggestions"])
        self.assertTrue(payload["diagnosis"])


class ToothSpaceHelperTests(unittest.TestCase):
    def test_ring_teeth_for_ratio_inverts_the_ratio_equation(self) -> None:
        self.assertAlmostEqual(gb.ring_teeth_for_ratio(18, 4.0), 54.0)
        self.assertAlmostEqual(gb.planet_teeth_from_concentricity(18, 54), 18.0)

    def test_next_ring_teeth_satisfies_parity_and_assembly(self) -> None:
        z_ring = gb.next_ring_teeth(17, 3, 51)
        self.assertIsNotNone(z_ring)
        self.assertEqual((z_ring - 17) % 2, 0)
        self.assertEqual((17 + z_ring) % 3, 0)

    def test_ring_step_matches_both_periods(self) -> None:
        self.assertEqual(gb.ring_step(3), 6)
        self.assertEqual(gb.ring_step(4), 4)
        self.assertEqual(gb.ring_step(5), 10)


class InternalConsistencyTests(unittest.TestCase):
    def test_fast_scan_filter_agrees_with_full_check_evaluation(self) -> None:
        """The scan's cheap filter and the displayed checks must never disagree."""
        disagreements = []
        for module in (1.0, 2.0):
            for n_planets in (2, 3, 4, 5):
                for z_sun in range(15, 40):
                    for z_ring in range(z_sun + 30, z_sun + 80):
                        candidate = gb._candidate(
                            module, n_planets, 4.0, z_sun, z_ring, 500.0
                        )
                        solution = gb._evaluate(
                            module, n_planets, 4.0, 500.0, z_sun, z_ring, 0.05
                        )
                        if (candidate is not None) != solution.geometry_valid:
                            disagreements.append(
                                (module, n_planets, z_sun, z_ring)
                            )

        self.assertEqual(disagreements, [])

    def test_worst_case_failure_path_stays_fast(self) -> None:
        """A wide search that finds nothing must still answer promptly."""
        start = time.perf_counter()
        gb.solve_planetary(0.5, 6, 12.0, 5000.0)
        self.assertLess(time.perf_counter() - start, 1.0)


if __name__ == "__main__":
    unittest.main()
