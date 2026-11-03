"""Schematic top view of the planetary train, drawn with matplotlib only."""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure
from matplotlib.patches import Circle  # noqa: E402  (after backend selection)

SUN_COLOR = "#f2b134"
PLANET_COLOR = "#4a7fd9"
RING_COLOR = "#3f4a56"
ENVELOPE_COLOR = "#d64545"


def draw_train(
    module: float,
    n_planets: int,
    z_sun: int,
    z_planet: int,
    z_ring: int,
    d_ext: float | None = None,
    d_max: float | None = None,
) -> Figure:
    """Return a schematic figure with pitch circles and the diameter envelope.

    Only pitch circles are drawn: it keeps the schematic readable and it is what
    the tooth-count geometry actually defines. An optional dashed circle shows
    the allowed outside diameter so the user can see how much room is left.
    """
    figure = Figure(figsize=(6.0, 6.0), dpi=110)
    axes = figure.add_subplot(111)
    axes.set_aspect("equal")

    r_sun = module * z_sun / 2.0
    r_planet = module * z_planet / 2.0
    r_ring = module * z_ring / 2.0
    r_carrier = r_sun + r_planet  # planet centres sit on the carrier circle

    # Ring gear: pitch circle (dashed) plus the outside diameter (solid).
    axes.add_patch(
        Circle(
            (0.0, 0.0),
            r_ring,
            fill=False,
            linestyle="--",
            linewidth=1.6,
            edgecolor=RING_COLOR,
            label=f"Ring pitch circle, Zr={z_ring} (Ø{r_ring * 2:.1f} mm)",
        )
    )
    if d_ext:
        axes.add_patch(
            Circle(
                (0.0, 0.0),
                d_ext / 2.0,
                fill=False,
                linewidth=2.0,
                edgecolor=RING_COLOR,
                label=f"Ring outside, Ø{d_ext:.1f} mm",
            )
        )

    # Sun.
    axes.add_patch(
        Circle(
            (0.0, 0.0),
            r_sun,
            facecolor=SUN_COLOR,
            edgecolor="#8a5f10",
            alpha=0.9,
            label=f"Sun, Zs={z_sun} (Ø{r_sun * 2:.1f} mm)",
        )
    )

    # Planets.
    for index in range(n_planets):
        angle = 2.0 * math.pi * index / n_planets
        cx = r_carrier * math.cos(angle)
        cy = r_carrier * math.sin(angle)
        axes.add_patch(
            Circle(
                (cx, cy),
                r_planet,
                facecolor=PLANET_COLOR,
                edgecolor="#22406e",
                alpha=0.85,
                label=f"Planet, Zp={z_planet} (Ø{r_planet * 2:.1f} mm)" if index == 0 else None,
            )
        )
        axes.plot([0.0, cx], [0.0, cy], color="#aaaaaa", linewidth=0.6, linestyle=":")

    # Carrier circle through the planet centres.
    axes.add_patch(
        Circle(
            (0.0, 0.0),
            r_carrier,
            fill=False,
            linestyle=":",
            linewidth=1.0,
            edgecolor="#888888",
            label=f"Carrier, Ø{r_carrier * 2:.1f} mm",
        )
    )

    # Allowed envelope.
    if d_max:
        axes.add_patch(
            Circle(
                (0.0, 0.0),
                d_max / 2.0,
                fill=False,
                linestyle="-.",
                linewidth=1.4,
                edgecolor=ENVELOPE_COLOR,
                label=f"D_max = {d_max:g} mm",
            )
        )

    radii = [r_ring * 1.05, (d_ext or 0.0) / 2.0 * 1.05, (d_max or 0.0) / 2.0 * 1.05]
    limit = max(radii)
    axes.set_xlim(-limit, limit)
    axes.set_ylim(-limit, limit)
    axes.axis("off")
    axes.legend(loc="upper left", fontsize=7, framealpha=0.9)
    figure.tight_layout()
    return figure
