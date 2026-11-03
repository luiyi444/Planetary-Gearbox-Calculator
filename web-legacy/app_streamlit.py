"""Streamlit interface for the single-stage planetary gearbox calculator.

Optional legacy UI. It lives in web-legacy/ because it needs third-party
packages (streamlit, matplotlib), while the primary desktop app needs nothing
beyond the standard library.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The calculation core stays at the project root, shared with the desktop app.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

import gearbox as gb
from diagram import draw_train

st.set_page_config(
    page_title="Planetary Gearbox Calculator",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ Planetary gearbox calculator")
st.caption(
    "Single stage · ring gear fixed · sun input · carrier output · metric module. "
    "Tooth counts are solved in integer space; the module only scales the sizes."
)

# --- Inputs -----------------------------------------------------------------

with st.sidebar:
    st.header("Inputs")

    module = st.selectbox(
        "Module m (mm)",
        options=gb.STANDARD_MODULES,
        index=gb.STANDARD_MODULES.index(2.0),
        help="Standard metric module. Bigger module = bigger, stronger teeth.",
    )
    n_planets = st.slider(
        "Number of planets N",
        min_value=2,
        max_value=6,
        value=3,
        help="More planets share the load, but leave less room between them.",
    )
    i_requested = st.number_input(
        "Requested ratio i",
        min_value=1.5,
        max_value=20.0,
        value=4.0,
        step=0.1,
        format="%.2f",
        help="Ring fixed, sun in, carrier out: i = 1 + Zr/Zs.",
    )
    d_max = st.number_input(
        "Maximum outside diameter D_max (mm)",
        min_value=10.0,
        max_value=5000.0,
        value=120.0,
        step=5.0,
        format="%.1f",
        help="Outer diameter of the ring gear, rim included.",
    )

    with st.expander("Advanced"):
        tolerance_pct = st.number_input(
            "Allowed ratio deviation (%)",
            min_value=0.1,
            max_value=20.0,
            value=gb.DEFAULT_RATIO_TOLERANCE * 100,
            step=0.5,
            format="%.1f",
            help="Tooth counts are integers, so i_real rarely equals i exactly.",
        )
        max_alternatives = st.number_input(
            "Alternative designs to show",
            min_value=0,
            max_value=10,
            value=3,
            step=1,
        )

    st.divider()
    st.caption(
        f"Assumed limits: Zs, Zp ≥ {gb.MIN_TEETH_SUN} teeth (20° involute), "
        f"planet gap of {gb.ADJACENCY_CLEARANCE:g} teeth, "
        f"D_ext = m·(Zr + {gb.RING_RIM_FACTOR:g})."
    )

tolerance = tolerance_pct / 100.0

# --- Solve ------------------------------------------------------------------

try:
    result = gb.solve_planetary(
        module=module,
        n_planets=n_planets,
        i_requested=i_requested,
        d_max=d_max,
        max_alternatives=int(max_alternatives),
        tolerance=tolerance,
    )
except ValueError as error:
    st.error(f"Invalid input: {error}")
    st.stop()

# --- No feasible design -----------------------------------------------------

if not result.ok:
    st.error(result.message)
    if result.diagnosis:
        st.info(result.diagnosis)
    st.subheader("What to change")
    for suggestion in result.suggestions:
        st.markdown(f"- {suggestion}")
    st.caption(
        "The four conditions are not negotiable independently: the ratio fixes "
        "the tooth ratio, concentricity fixes the planets, and the envelope then "
        "decides whether the train fits."
    )
    st.stop()

# --- Feasible design --------------------------------------------------------

best = result.best
assert best is not None  # guaranteed by result.ok

if best.valid:
    st.success(result.message)
else:
    st.warning(result.message)

headline = st.columns(4)
headline[0].metric("Sun teeth Zs", best.z_sun)
headline[1].metric("Planet teeth Zp", best.z_planet)
headline[2].metric("Ring teeth Zr", best.z_ring)
headline[3].metric(
    "Real ratio i_real",
    f"{best.i_real:.4f}",
    delta=f"{best.ratio_deviation:+.2%} vs requested",
    delta_color="inverse",
    help="i_real = 1 + Zr/Zs. Integer teeth make an exact match unlikely.",
)

left, right = st.columns([1.15, 1.0], gap="large")

with left:
    st.subheader("Design conditions")
    rows = [
        {
            "Condition": check.label,
            "Expression": check.expression,
            "Status": "✅ pass" if check.passed else "❌ fail",
            "Evaluation": check.detail,
        }
        for check in best.checks
    ]
    st.dataframe(rows, hide_index=True, width="stretch")

    for check in best.failed_checks:
        st.warning(f"**{check.label} fails.** {check.detail}. {check.hint}")

with right:
    st.subheader("Schematic")
    figure = draw_train(
        module=best.module,
        n_planets=best.n_planets,
        z_sun=best.z_sun,
        z_planet=best.z_planet,
        z_ring=best.z_ring,
        d_ext=best.d_ext,
        d_max=result.d_max,
    )
    st.pyplot(figure, width="stretch")

st.subheader("Pitch diameters")
# Every value in this table is a string on purpose: mixing integers with a
# placeholder breaks Arrow serialisation on the server side.
diameters = [
    {"Element": "Sun", "Teeth": str(best.z_sun), "Pitch diameter (mm)": f"{best.d_sun:.2f}"},
    {"Element": "Planet", "Teeth": str(best.z_planet), "Pitch diameter (mm)": f"{best.d_planet:.2f}"},
    {"Element": "Ring", "Teeth": str(best.z_ring), "Pitch diameter (mm)": f"{best.d_ring:.2f}"},
    {"Element": "Carrier", "Teeth": "—", "Pitch diameter (mm)": f"{best.d_carrier:.2f}"},
    {"Element": "Ring outside", "Teeth": "—", "Pitch diameter (mm)": f"{best.d_ext:.2f}"},
]
st.dataframe(diameters, hide_index=True, width="stretch")

usage = min(best.d_ext / result.d_max, 1.0) if result.d_max else 0.0
st.progress(
    usage,
    text=f"Envelope used: {best.d_ext:.1f} mm of {result.d_max:.1f} mm "
    f"({usage:.0%}) · {result.d_max - best.d_ext:.1f} mm free",
)

# --- Alternatives -----------------------------------------------------------

if result.alternatives:
    st.subheader("Alternative designs")
    st.caption(
        "Structurally valid trains ordered by how close their real ratio is to "
        "the one you asked for."
    )
    st.dataframe(
        [
            {
                "Zs": alt.z_sun,
                "Zp": alt.z_planet,
                "Zr": alt.z_ring,
                "i_real": f"{alt.i_real:.4f}",
                "Deviation": f"{alt.ratio_deviation:.2%}",
                "D_ext (mm)": f"{alt.d_ext:.1f}",
                "Status": "✅ all pass" if alt.valid else "⚠️ ratio too far",
            }
            for alt in result.alternatives
        ],
        hide_index=True,
        width="stretch",
    )

with st.expander("How these tooth counts were found"):
    st.markdown(
        f"""
1. For each sun tooth count from **Zs = {gb.MIN_TEETH_SUN}** upwards, the ideal ring
   is `Zr = Zs·(i − 1)`.
2. `Zr` is rounded up to the first integer that satisfies both the parity
   (`Zr − Zs` even, so `Zp = (Zr − Zs)/2` is an integer) and the assembly
   condition `(Zs + Zr) mod N = 0`.
3. `Zp` follows from concentricity: `Zr = Zs + 2·Zp`.
4. The adjacency and envelope conditions are then checked. Every structurally
   valid combination is kept, sorted by `|i_real − i|`, and the closest one is
   shown as the design with the next ones as alternatives.
5. The module never enters the search: it only multiplies the diameters.
"""
    )
