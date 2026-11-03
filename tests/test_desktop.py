"""Tests for the Tkinter interface. Standard library only.

The window is never shown: a withdrawn root plus a mocked canvas size is enough
to drive the real widgets and assert what a user would see.
"""

from __future__ import annotations

import tkinter as tk
import unittest
from unittest import mock

try:
    import desktop
    from desktop import PlanetaryCalculatorApp, _default_geometry

    TK_AVAILABLE = True
except Exception:  # pragma: no cover - Tk is missing on some minimal installs
    TK_AVAILABLE = False


class _Screen:
    """Stand-in for a root window: only the screen metrics are needed."""

    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height

    def winfo_screenwidth(self) -> int:
        return self._width

    def winfo_screenheight(self) -> int:
        return self._height


class WindowGeometryTests(unittest.TestCase):
    """The window must fit the monitor it is opened on, whatever that is."""

    def test_a_large_screen_gets_the_preferred_size(self) -> None:
        """On a screen with room, the window opens at the size we designed for."""
        geometry, minimum = _default_geometry(_Screen(1920, 1080))
        self.assertEqual(
            tuple(int(value) for value in geometry.split("x")), desktop.WINDOW_PREFERRED
        )
        self.assertEqual(minimum, desktop.WINDOW_MIN)

    def test_a_small_laptop_screen_gets_a_window_that_fits(self) -> None:
        geometry, minimum = _default_geometry(_Screen(1366, 768))
        width, height = (int(value) for value in geometry.split("x"))
        self.assertLessEqual(width, 1366)
        self.assertLessEqual(height, 768)
        # The minimum must never be larger than the window itself.
        self.assertLessEqual(minimum[0], width)
        self.assertLessEqual(minimum[1], height)

    def test_a_tiny_screen_still_gets_a_usable_window(self) -> None:
        geometry, _minimum = _default_geometry(_Screen(1024, 600))
        width, height = (int(value) for value in geometry.split("x"))
        self.assertGreaterEqual(width, 900)
        self.assertGreaterEqual(height, 560)


@unittest.skipUnless(TK_AVAILABLE, "Tkinter is not available")
class DesktopAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = PlanetaryCalculatorApp(self.root, language="en")
        self.root.update_idletasks()

    # -- helpers -------------------------------------------------------------

    def metric(self, index: int) -> str:
        return self.app.metric_values[index].cget("text")

    def verification_text(self) -> str:
        return self.app.checks_text.get("1.0", "end")

    def type_into(self, attribute: str, value: str) -> None:
        getattr(self.app, attribute).set(value)
        self.app._calculate()

    def select_configuration(self, key: str) -> None:
        labels = {value: label for label, value in self.app._configuration_labels.items()}
        self.app.configuration_var.set(labels[key])
        self.app._on_configuration_change()

    # -- default state -------------------------------------------------------

    def test_defaults_show_the_reference_design(self) -> None:
        self.assertEqual(self.metric(0), "18")
        self.assertEqual(self.metric(1), "18")
        self.assertEqual(self.metric(2), "54")
        self.assertTrue(self.metric(3).startswith("4.0"))

    def test_defaults_show_every_condition_as_passing(self) -> None:
        text = self.verification_text()
        self.assertEqual(text.count("PASS"), 6)
        self.assertNotIn("FAIL", text)

    def test_diameters_and_envelope_are_reported(self) -> None:
        self.assertIn("ring outside 113.00 mm", self.app.diameters_label.cget("text"))
        self.assertIn("113.0 of 120.0 mm", self.app.envelope_label.cget("text"))
        self.assertAlmostEqual(self.app.envelope_bar.cget("value"), 113.0 / 120.0 * 100)

    def test_alternatives_are_listed(self) -> None:
        rows = self.app.alternatives_tree.get_children()
        self.assertGreaterEqual(len(rows), 1)

    def test_alternative_status_names_the_failing_condition(self) -> None:
        rows = self.app.alternatives_tree.get_children()
        for row in rows:
            status = self.app.alternatives_tree.item(row, "values")[6]
            self.assertIn(status, {"all conditions pass", "Ratio tolerance"})

    # -- reacting to inputs --------------------------------------------------

    def test_impossible_envelope_reports_and_clears_the_numbers(self) -> None:
        self.type_into("d_max_var", "100")
        self.assertEqual(self.metric(0), "—")
        self.assertIn("No valid train", self.app.message_label.cget("text"))
        text = self.verification_text()
        self.assertIn("Binding constraint", text)
        self.assertIn("What to change", text)
        self.assertIn("D_max", text)

    def test_impossible_design_hides_the_empty_geometry_card(self) -> None:
        """An empty white card reads as a rendering bug, so it goes away."""
        self.assertEqual(self.app.report_card.winfo_manager(), "grid")
        self.type_into("d_max_var", "100")
        self.assertEqual(self.app.report_card.winfo_manager(), "")

    def test_impossible_design_says_there_is_no_alternative(self) -> None:
        self.type_into("d_max_var", "100")
        rows = self.app.alternatives_tree.get_children()
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            self.app.alternatives_tree.item(rows[0], "values")[6], "no other design"
        )

    def test_a_possible_design_brings_the_geometry_card_back(self) -> None:
        self.type_into("d_max_var", "100")
        self.type_into("module_var", "1.5")
        self.assertEqual(self.app.report_card.winfo_manager(), "grid")
        self.assertIn("Envelope used", self.app.envelope_label.cget("text"))

    def test_smaller_module_rescues_the_same_train(self) -> None:
        self.type_into("d_max_var", "100")
        self.type_into("module_var", "1.5")
        self.assertEqual(self.metric(0), "18")
        self.assertNotIn("No valid train", self.app.message_label.cget("text"))

    def test_six_planets_at_ratio_four_is_explained_not_crashed(self) -> None:
        self.type_into("planets_var", "6")
        self.assertIn("No valid train", self.app.message_label.cget("text"))
        self.assertIn("planets", self.verification_text())

    def test_non_numeric_input_is_reported_without_crashing(self) -> None:
        self.type_into("ratio_var", "abc")
        self.assertIn("number", self.app.message_label.cget("text"))
        self.assertEqual(self.metric(0), "—")

    def test_ratio_below_one_is_rejected_with_the_reason(self) -> None:
        self.type_into("ratio_var", "0.5")
        self.assertIn("greater than 1", self.app.message_label.cget("text"))

    def test_decimal_comma_is_accepted(self) -> None:
        self.type_into("module_var", "1,5")
        self.assertEqual(self.metric(0), "18")

    # -- schematic -----------------------------------------------------------

    def test_schematic_draws_the_train(self) -> None:
        with mock.patch.object(tk.Canvas, "winfo_width", return_value=400), \
                mock.patch.object(tk.Canvas, "winfo_height", return_value=400):
            self.app._draw()
        drawn = self.app.canvas.find_all()
        self.assertGreaterEqual(len(drawn), 8)

    def test_schematic_says_so_when_there_is_nothing_to_draw(self) -> None:
        self.type_into("d_max_var", "10")
        with mock.patch.object(tk.Canvas, "winfo_width", return_value=400), \
                mock.patch.object(tk.Canvas, "winfo_height", return_value=400):
            self.app._draw()
        texts = [
            self.app.canvas.itemcget(item, "text")
            for item in self.app.canvas.find_all()
            if self.app.canvas.type(item) == "text"
        ]
        self.assertIn("No feasible train to draw", texts)

    # -- recalculating through the real widgets ------------------------------

    def test_arrows_on_the_spinbox_recalculate(self) -> None:
        self.app.planets_var.set("4")
        self.app._calculate()
        self.assertNotEqual(self.metric(0), "—")

    # -- who drives ----------------------------------------------------------

    def test_default_configuration_names_the_sun_as_driver(self) -> None:
        text = self.app.kinematics_label.cget("text")
        self.assertIn("Sun is the driver", text)
        self.assertIn("carrier", text)
        self.assertIn("reduction", text)

    def test_switching_the_driver_turns_the_reduction_into_a_speed_increase(self) -> None:
        self.select_configuration("ring_fixed_carrier_drive")
        self.type_into("ratio_var", "0.25")

        self.assertEqual(self.metric(0), "18")
        self.assertEqual(self.metric(2), "54")
        self.assertTrue(self.metric(3).startswith("0.25"))
        text = self.app.kinematics_label.cget("text")
        self.assertIn("Carrier is the driver", text)
        self.assertIn("speed increase", text)

    def test_overdrive_configuration_explains_a_reduction_ratio_instead_of_using_it(self) -> None:
        self.select_configuration("ring_fixed_carrier_drive")
        message = self.app.message_label.cget("text")
        self.assertIn("smaller than 1", message)
        self.assertIn("i = 0.25", message)
        self.assertEqual(self.metric(0), "—")

    def test_configuration_choice_survives_a_language_switch(self) -> None:
        self.select_configuration("sun_fixed_carrier_drive")
        self.app.set_language("es")
        self.assertEqual(self.app.configuration_key, "sun_fixed_carrier_drive")
        self.assertIn("Solar fijo", self.app.configuration_var.get())

    def test_legend_states_the_role_of_each_member(self) -> None:
        entries = [
            text
            for _, text in self.app._legend_entries(self.app._solution, 120.0)
        ]
        self.assertIn("driver", entries[0])
        self.assertIn("idle", entries[1])
        self.assertIn("fixed", entries[2])
        self.assertIn("envelope", entries[3])

    # -- language ------------------------------------------------------------

    def test_switching_to_spanish_translates_the_whole_window(self) -> None:
        self.app.set_language("es")

        self.assertIn("Concentricidad", self.verification_text())
        self.assertIn("Solución encontrada", self.app.message_label.cget("text"))
        self.assertEqual(self.app.metric_values[0].cget("text"), "18")
        self.assertIn("Diámetros primitivos", self.app.diameters_label.cget("text"))
        self.assertEqual(
            self.app.configuration_var.get(),
            "Corona fija · solar motriz · portasatélites conducido",
        )

    def test_spanish_reports_an_impossible_envelope_with_guidance(self) -> None:
        self.app.set_language("es")
        self.type_into("d_max_var", "100")
        text = self.verification_text()
        self.assertIn("Restricción activa", text)
        self.assertIn("Qué cambiar", text)
        self.assertIn("D_máx", text)

    def test_switching_back_to_english_restores_the_wording(self) -> None:
        self.app.set_language("es")
        self.app.set_language("en")
        self.assertIn("Concentricity", self.verification_text())
        self.assertIn("Solution found", self.app.message_label.cget("text"))

    def test_language_switch_keeps_the_entered_values(self) -> None:
        self.type_into("d_max_var", "200")
        self.app.set_language("es")
        self.assertEqual(self.app.d_max_var.get(), "200")
        self.assertNotEqual(self.metric(0), "—")

    def test_spanish_alternative_status_names_the_failing_condition(self) -> None:
        self.app.set_language("es")
        rows = self.app.alternatives_tree.get_children()
        statuses = {self.app.alternatives_tree.item(row, "values")[6] for row in rows}
        self.assertLessEqual(statuses, {"todas las condiciones se cumplen", "Tolerancia de relación"})


if __name__ == "__main__":
    unittest.main()
