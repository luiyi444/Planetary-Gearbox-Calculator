"""Smoke tests for the Streamlit layer: it must render, and never crash."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest
from streamlit.testing.v1 import AppTest

# AppTest resolves relative paths against this file, so build an absolute one.
APP = str(Path(__file__).resolve().parent / "app_streamlit.py")


@pytest.fixture(scope="module")
def app():
    instance = AppTest.from_file(APP, default_timeout=60)
    instance.run()
    return instance


def test_app_renders_without_exceptions(app):
    assert not app.exception


def test_default_inputs_produce_the_reference_tooth_set(app):
    values = [metric.value for metric in app.metric]
    assert values[0] == "18"  # sun
    assert values[1] == "18"  # planet
    assert values[2] == "54"  # ring
    assert values[3].startswith("4.0")  # real ratio


def test_default_design_reports_success(app):
    assert len(app.success) == 1
    assert not app.error


def test_every_check_row_is_rendered(app):
    table = app.dataframe[0].value
    assert len(table) == 6
    assert set(table["Status"]) == {"✅ pass"}


def test_diameter_table_columns_are_arrow_safe(app):
    """A mixed int/str column makes Arrow serialisation fail on the server."""
    table = app.dataframe[1].value
    assert list(table["Element"]) == [
        "Sun",
        "Planet",
        "Ring",
        "Carrier",
        "Ring outside",
    ]
    assert all(isinstance(value, str) for value in table["Teeth"])


def test_every_rendered_table_serialises_to_arrow(app):
    """Reproduces the server-side serialisation Streamlit performs per table."""
    assert app.dataframe
    for element in app.dataframe:
        pa.Table.from_pandas(element.value, preserve_index=False)


def test_impossible_envelope_warns_instead_of_crashing(app):
    app.sidebar.number_input[1].set_value(100.0).run()
    assert not app.exception
    assert len(app.error) == 1
    assert "No valid train exists" in app.error[0].value


def test_impossible_envelope_offers_concrete_alternatives():
    instance = AppTest.from_file(APP, default_timeout=60)
    instance.run()
    instance.sidebar.number_input[1].set_value(100.0).run()
    assert instance.info  # the binding-constraint diagnosis
    assert instance.markdown  # the suggestion bullets
    assert any("D_max" in block.value for block in instance.markdown)


def test_planet_slider_extremes_do_not_crash(app):
    for n_planets in (2, 4, 5, 6):
        instance = AppTest.from_file(APP, default_timeout=60)
        instance.run()
        instance.sidebar.slider[0].set_value(n_planets).run()
        assert not instance.exception, f"N={n_planets} crashed the page"
