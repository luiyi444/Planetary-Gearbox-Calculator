"""Pure calculation core for a single-stage planetary (epicyclic) gear set.

A single-stage epicyclic train has three rotating members (sun, ring, carrier)
and exactly one of them must be held fixed. That leaves four useful kinematic
configurations, and **they do not share the same ratio law**: swapping the
driver and the driven member turns a reduction into a speed increase and
inverts the ratio. All four are modelled here (`CONFIGURATIONS`):

    ring fixed, sun drives, carrier driven .... i = 1 + Zr/Zs      (i > 1)
    ring fixed, carrier drives, sun driven .... i = Zs/(Zs + Zr)   (i < 1)
    sun fixed, carrier drives, ring driven .... i = 1 + Zs/Zr      (i > 1)
    sun fixed, ring drives, carrier driven .... i = Zr/(Zs + Zr)   (i < 1)

The first one is the classic reducer and remains the default.

Geometry is independent of who drives, so it is shared by every configuration
(Willis' equation / standard epicyclic train theory, see Norton "Design of
Machinery" gear-train chapter and the gear-geometry literature for the
tooth-count limits):

    Zr           = Zs + 2 * Zp           concentricity (coaxial mounting)
    (Zs + Zr) mod N == 0                 assembly of N equally spaced planets
    (Zs + Zp)*sin(pi/N) > Zp + clearance adjacency: planets must not touch
    D_ext        = m * (Zr + 2.5)        ring outside diameter (addendum + rim)

The module is deliberately kept out of the tooth-count search: Zs, Zp and Zr
depend only on the ratio, the planet count and the tooth limits, so the geometry
is solved in tooth space first and converted to millimetres afterwards.

Every user-facing sentence comes from `i18n`, so the same solve can report in
English or in Spanish. This module has no UI dependency and no side effects,
which is what makes it unit-testable on its own.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Iterator

from i18n import normalize_language, tr

# --- Design constants -------------------------------------------------------

STANDARD_MODULES: tuple[float, ...] = (
    0.5, 0.8, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0,
)
"""Preferred metric modules offered to the user (ISO 54 series 1 and 2 mix)."""

MIN_TEETH_SUN: int = 17
"""Minimum sun teeth to avoid undercut in a 20 deg full-depth involute gear."""

MIN_TEETH_PLANET: int = 17
"""Minimum planet teeth (external mesh with the sun, same undercut limit)."""

ADJACENCY_CLEARANCE: float = 2.0
"""Teeth-equivalent gap kept between neighbouring planets (backlash + rim)."""

RING_RIM_FACTOR: float = 2.5
"""D_ext = m * (Zr + 2.5): two addenda plus half a module of rim wall."""

DEFAULT_RATIO_TOLERANCE: float = 0.05
"""Accepted relative deviation between the requested and the real ratio."""

MAX_SEARCH_TEETH: int = 2000
"""Hard bound on any tooth count, so a pathological query cannot hang the solver."""

MAX_RING_CANDIDATES: int = 3
"""Ring tooth counts evaluated per sun tooth count (nearest to the target)."""

NO_SOLUTION_MESSAGE: str = tr("en", "core.message.no_solution")
"""English wording of the "nothing fits" answer, kept for callers and tests."""


# --- Kinematic configurations -----------------------------------------------


@dataclass(frozen=True)
class TrainConfiguration:
    """One way of holding a member fixed and driving another.

    A planetary train has three members and one of them must be fixed, which
    leaves four useful arrangements. `ratio` and `ring_teeth` are exact inverses
    of each other, so the same tooth search serves every configuration: only the
    law that turns a ratio into a target ring tooth count changes.
    """

    key: str
    """Stable identifier, also the suffix of its translation keys."""

    fixed: str
    """Element key of the member held fixed: sun, ring or carrier."""

    driver: str
    """Element key of the input member (the one that receives the torque)."""

    driven: str
    """Element key of the output member (the one that turns the load)."""

    ratio: Callable[[int, int], float]
    """i = f(Zs, Zr), as omega_driver / omega_driven."""

    ring_teeth: Callable[[int, float], float]
    """Zr = g(Zs, i): the ideal non-integer ring count for a sun count."""

    @property
    def reduction(self) -> bool:
        """True when i > 1 (the output turns slower than the input)."""
        return self.ratio(1, 2) > 1.0

    def label(self, language: str) -> str:
        return tr(language, f"config.{self.key}.label")

    def formula(self, language: str) -> str:
        return tr(language, f"config.{self.key}.formula")

    def accepts(self, i_requested: float) -> bool:
        """Whether a ratio belongs to this configuration's valid range."""
        if not math.isfinite(i_requested) or i_requested <= 0.0:
            return False
        return i_requested > 1.0 if self.reduction else i_requested < 1.0


CONFIGURATIONS: dict[str, TrainConfiguration] = {
    config.key: config
    for config in (
        TrainConfiguration(
            key="ring_fixed_sun_drive",
            fixed="ring",
            driver="sun",
            driven="carrier",
            ratio=lambda z_sun, z_ring: 1.0 + z_ring / z_sun,
            ring_teeth=lambda z_sun, i: z_sun * (i - 1.0),
        ),
        TrainConfiguration(
            key="ring_fixed_carrier_drive",
            fixed="ring",
            driver="carrier",
            driven="sun",
            ratio=lambda z_sun, z_ring: z_sun / (z_sun + z_ring),
            ring_teeth=lambda z_sun, i: z_sun * (1.0 - i) / i,
        ),
        TrainConfiguration(
            key="sun_fixed_carrier_drive",
            fixed="sun",
            driver="carrier",
            driven="ring",
            ratio=lambda z_sun, z_ring: 1.0 + z_sun / z_ring,
            ring_teeth=lambda z_sun, i: z_sun / (i - 1.0),
        ),
        TrainConfiguration(
            key="sun_fixed_ring_drive",
            fixed="sun",
            driver="ring",
            driven="carrier",
            ratio=lambda z_sun, z_ring: z_ring / (z_sun + z_ring),
            ring_teeth=lambda z_sun, i: z_sun * i / (1.0 - i),
        ),
    )
}

DEFAULT_CONFIGURATION: str = "ring_fixed_sun_drive"
"""The classic reducer: ring fixed, sun driving, carrier driven."""


def get_configuration(
    key: str | TrainConfiguration | None,
) -> TrainConfiguration:
    """Resolve a configuration by key, passing an instance through unchanged."""
    if isinstance(key, TrainConfiguration):
        return key
    if key is None:
        return CONFIGURATIONS[DEFAULT_CONFIGURATION]
    try:
        return CONFIGURATIONS[key]
    except KeyError as error:
        known = ", ".join(CONFIGURATIONS)
        raise ValueError(f"unknown configuration {key!r}; expected one of {known}") from error


# --- Result types -----------------------------------------------------------


@dataclass(frozen=True)
class Check:
    """One design condition, evaluated and ready to be displayed."""

    key: str
    label: str
    passed: bool
    expression: str
    detail: str
    hint: str = ""


@dataclass(frozen=True)
class Solution:
    """A complete tooth/geometry solution plus the verdict of every condition."""

    module: float
    n_planets: int
    i_requested: float
    z_sun: int
    z_planet: int
    z_ring: int
    checks: tuple[Check, ...]
    configuration: TrainConfiguration = CONFIGURATIONS[DEFAULT_CONFIGURATION]

    # -- derived kinematics --------------------------------------------------

    @property
    def i_real(self) -> float:
        """Real ratio for the rounded tooth counts, i = w_driver / w_driven."""
        return self.configuration.ratio(self.z_sun, self.z_ring)

    @property
    def ratio_deviation(self) -> float:
        """Relative deviation of the real ratio from the requested one."""
        return abs(self.i_real - self.i_requested) / self.i_requested

    # -- derived geometry ----------------------------------------------------

    @property
    def d_sun(self) -> float:
        return self.module * self.z_sun

    @property
    def d_planet(self) -> float:
        return self.module * self.z_planet

    @property
    def d_ring(self) -> float:
        return self.module * self.z_ring

    @property
    def d_carrier(self) -> float:
        """Pitch diameter of the planet carrier (sun + planet pitch circles)."""
        return self.d_sun + self.d_planet

    @property
    def d_ext(self) -> float:
        """Outside diameter of the ring gear."""
        return self.module * (self.z_ring + RING_RIM_FACTOR)

    # -- verdicts ------------------------------------------------------------

    @property
    def geometry_valid(self) -> bool:
        """True when every structural condition holds (ratio deviation aside)."""
        return all(c.passed for c in self.checks if c.key != "ratio")

    @property
    def valid(self) -> bool:
        """True when every displayed condition holds, ratio tolerance included."""
        return all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> tuple[Check, ...]:
        return tuple(c for c in self.checks if not c.passed)

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "n_planets": self.n_planets,
            "configuration": self.configuration.key,
            "driver": self.configuration.driver,
            "driven": self.configuration.driven,
            "fixed": self.configuration.fixed,
            "i_requested": self.i_requested,
            "i_real": self.i_real,
            "ratio_deviation": self.ratio_deviation,
            "z_sun": self.z_sun,
            "z_planet": self.z_planet,
            "z_ring": self.z_ring,
            "d_sun": self.d_sun,
            "d_planet": self.d_planet,
            "d_ring": self.d_ring,
            "d_carrier": self.d_carrier,
            "d_ext": self.d_ext,
            "valid": self.valid,
            "checks": [
                {
                    "key": c.key,
                    "label": c.label,
                    "passed": c.passed,
                    "expression": c.expression,
                    "detail": c.detail,
                }
                for c in self.checks
            ],
        }


@dataclass(frozen=True)
class SolveResult:
    """Outcome of a full solve: best design, near alternatives, or guidance."""

    ok: bool
    best: Solution | None
    alternatives: tuple[Solution, ...]
    message: str
    suggestions: tuple[str, ...]
    d_max: float
    tolerance: float
    diagnosis: str = ""
    configuration: TrainConfiguration = CONFIGURATIONS[DEFAULT_CONFIGURATION]

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "message": self.message,
            "diagnosis": self.diagnosis,
            "configuration": self.configuration.key,
            "suggestions": list(self.suggestions),
            "d_max": self.d_max,
            "tolerance": self.tolerance,
            "best": self.best.to_dict() if self.best else None,
            "alternatives": [s.to_dict() for s in self.alternatives],
        }


# --- Input validation -------------------------------------------------------


def validate_inputs(
    module: float,
    n_planets: int,
    i_requested: float,
    d_max: float,
    configuration: TrainConfiguration | None = None,
    language: str = "en",
) -> None:
    """Raise ValueError with an actionable message for unusable inputs."""
    config = configuration or CONFIGURATIONS[DEFAULT_CONFIGURATION]

    if not math.isfinite(module) or module <= 0:
        raise ValueError(tr(language, "core.error.module"))
    if not isinstance(n_planets, int) or n_planets < 2:
        raise ValueError(tr(language, "core.error.planets"))
    if not config.accepts(i_requested):
        # Direction matters: 4:1 and 1:4 are different machines. Say so, and
        # name the configuration that turns the requested ratio into a valid one.
        reciprocal = 1.0 / i_requested if i_requested else float("inf")
        raise ValueError(
            tr(
                language,
                f"core.error.ratio.{'reduction' if config.reduction else 'overdrive'}",
                configuration=config.label(language),
                formula=config.formula(language),
                reciprocal=reciprocal,
            )
        )
    if not math.isfinite(d_max) or d_max <= 0:
        raise ValueError(tr(language, "core.error.d_max"))


# --- Tooth-space helpers ----------------------------------------------------


def ring_teeth_for_ratio(
    z_sun: int,
    i_requested: float,
    configuration: TrainConfiguration | None = None,
) -> float:
    """Ideal (non-integer) ring tooth count for a given sun count and ratio."""
    config = configuration or CONFIGURATIONS[DEFAULT_CONFIGURATION]
    return config.ring_teeth(z_sun, i_requested)


def planet_teeth_from_concentricity(z_sun: int, z_ring: int) -> float:
    """Planet tooth count forced by the concentricity condition."""
    return (z_ring - z_sun) / 2.0


def max_ring_teeth(module: float, d_max: float) -> int:
    """Largest ring tooth count whose outside diameter still fits in d_max."""
    if math.isinf(d_max):
        return MAX_SEARCH_TEETH
    return int(math.floor(d_max / module - RING_RIM_FACTOR))


def ring_step(n_planets: int) -> int:
    """Period after which both the parity and the assembly condition repeat."""
    return 2 * n_planets // math.gcd(2, n_planets)


def next_ring_teeth(z_sun: int, n_planets: int, start: int) -> int | None:
    """Smallest ring count >= start that satisfies parity and assembly.

    Returns None only for degenerate inputs; the two congruences
    Zr = Zs (mod 2) and Zr = -Zs (mod N) are always simultaneously solvable
    because gcd(2, N) divides 2*Zs.
    """
    step = ring_step(n_planets)
    candidate = start
    for _ in range(step):
        if (candidate - z_sun) % 2 == 0 and (z_sun + candidate) % n_planets == 0:
            return candidate
        candidate += 1
    return None


# --- Evaluation of a single tooth combination -------------------------------


@dataclass(frozen=True)
class _Candidate:
    """Check-free evaluation used while scanning the tooth space.

    The public `Solution` carries six formatted `Check` objects; building them
    for every combination the scan walks through is what makes a wide search
    slow. The scan only needs the numbers, so it works with this instead and the
    finalists are expanded into a full `Solution` afterwards.
    """

    z_sun: int
    z_planet: int
    z_ring: int
    i_real: float
    ratio_deviation: float
    d_ext: float


def _candidate(
    module: float,
    n_planets: int,
    i_requested: float,
    z_sun: int,
    z_ring: int,
    d_max: float,
    configuration: TrainConfiguration | None = None,
) -> _Candidate | None:
    """Structural filter applied to every tooth combination.

    Mirrors the conditions that `_evaluate` reports, in the same order, so the
    two can never disagree about whether a combination is usable.
    """
    config = configuration or CONFIGURATIONS[DEFAULT_CONFIGURATION]

    if z_sun < MIN_TEETH_SUN:
        return None
    if (z_ring - z_sun) % 2 != 0:
        return None
    if (z_sun + z_ring) % n_planets != 0:
        return None

    z_planet = (z_ring - z_sun) // 2
    if z_planet < MIN_TEETH_PLANET:
        return None
    if (z_sun + z_planet) * math.sin(math.pi / n_planets) <= (
        z_planet + ADJACENCY_CLEARANCE
    ):
        return None

    d_ext = module * (z_ring + RING_RIM_FACTOR)
    if d_ext > d_max + 1e-9:
        return None

    i_real = config.ratio(z_sun, z_ring)
    return _Candidate(
        z_sun=z_sun,
        z_planet=z_planet,
        z_ring=z_ring,
        i_real=i_real,
        ratio_deviation=abs(i_real - i_requested) / i_requested,
        d_ext=d_ext,
    )


def _evaluate(
    module: float,
    n_planets: int,
    i_requested: float,
    d_max: float,
    z_sun: int,
    z_ring: int,
    tolerance: float,
    configuration: TrainConfiguration | None = None,
    language: str = "en",
) -> Solution:
    config = configuration or CONFIGURATIONS[DEFAULT_CONFIGURATION]
    language = normalize_language(language)

    z_planet = (z_ring - z_sun) // 2
    i_real = config.ratio(z_sun, z_ring)
    deviation = abs(i_real - i_requested) / i_requested

    concentric_sum = z_sun + 2 * z_planet
    assembly_rest = (z_sun + z_ring) % n_planets
    adjacency_lhs = (z_sun + z_planet) * math.sin(math.pi / n_planets)
    adjacency_rhs = z_planet + ADJACENCY_CLEARANCE
    d_ext = module * (z_ring + RING_RIM_FACTOR)

    checks = (
        Check(
            key="concentricity",
            label=tr(language, "core.check.concentricity.label"),
            passed=z_ring == concentric_sum,
            expression="Zr = Zs + 2·Zp",
            detail=f"{z_ring} = {z_sun} + 2·{z_planet} = {concentric_sum}",
            hint=tr(language, "core.check.concentricity.hint"),
        ),
        Check(
            key="assembly",
            label=tr(language, "core.check.assembly.label"),
            passed=assembly_rest == 0,
            expression="(Zs + Zr) mod N = 0",
            detail=(
                f"({z_sun} + {z_ring}) mod {n_planets} = "
                f"{(z_sun + z_ring)} mod {n_planets} = {assembly_rest}"
            ),
            hint=tr(language, "core.check.assembly.hint"),
        ),
        Check(
            key="adjacency",
            label=tr(language, "core.check.adjacency.label"),
            passed=adjacency_lhs > adjacency_rhs,
            expression="(Zs + Zp)·sin(π/N) > Zp + 2",
            detail=(
                f"({z_sun} + {z_planet})·sin({180.0 / n_planets:.1f}°) = "
                f"{adjacency_lhs:.2f} > {adjacency_rhs:.2f}"
            ),
            hint=tr(language, "core.check.adjacency.hint"),
        ),
        Check(
            key="envelope",
            label=tr(language, "core.check.envelope.label"),
            passed=d_ext <= d_max + 1e-9,
            expression="m·(Zr + 2.5) ≤ D_max",
            detail=f"{module:g}·({z_ring} + 2.5) = {d_ext:.2f} mm ≤ {d_max:g} mm",
            hint=tr(language, "core.check.envelope.hint"),
        ),
        Check(
            key="min_teeth",
            label=tr(language, "core.check.min_teeth.label"),
            passed=z_sun >= MIN_TEETH_SUN and z_planet >= MIN_TEETH_PLANET,
            expression=f"Zs ≥ {MIN_TEETH_SUN} and Zp ≥ {MIN_TEETH_PLANET}",
            detail=f"Zs = {z_sun}, Zp = {z_planet}",
            hint=tr(language, "core.check.min_teeth.hint"),
        ),
        Check(
            key="ratio",
            label=tr(language, "core.check.ratio.label"),
            passed=deviation <= tolerance + 1e-12,
            expression=f"|i_real − i| / i ≤ {tolerance:.1%}",
            detail=f"i_real = {i_real:.4f} vs i = {i_requested:.4f} → {deviation:.2%}",
            hint=tr(language, "core.check.ratio.hint"),
        ),
    )

    return Solution(
        module=module,
        n_planets=n_planets,
        i_requested=i_requested,
        z_sun=z_sun,
        z_planet=z_planet,
        z_ring=z_ring,
        checks=checks,
        configuration=config,
    )


# --- Search -----------------------------------------------------------------


def _candidate_pairs(
    module: float,
    n_planets: int,
    i_requested: float,
    d_max: float,
    configuration: TrainConfiguration | None = None,
) -> Iterator[tuple[int, int]]:
    """Yield (Zs, Zr) pairs that already satisfy parity and assembly."""
    config = configuration or CONFIGURATIONS[DEFAULT_CONFIGURATION]

    ring_max = max_ring_teeth(module, d_max)
    if ring_max < MIN_TEETH_SUN + 2 * MIN_TEETH_PLANET:
        return

    # Ring teeth per sun tooth for this configuration, so the sun sweep stops
    # where the ring would leave the envelope. Every configuration's ratio law
    # is linear in Zs, so this bound is exact for all of them.
    ring_per_sun = config.ring_teeth(1, i_requested)
    if not math.isfinite(ring_per_sun) or ring_per_sun <= 0:
        return

    sun_max = min(ring_max, MAX_SEARCH_TEETH, int(ring_max / ring_per_sun) + 1)
    if sun_max < MIN_TEETH_SUN:
        return

    step = ring_step(n_planets)
    for z_sun in range(MIN_TEETH_SUN, sun_max + 1):
        target = config.ring_teeth(z_sun, i_requested)
        lower = max(z_sun + 2 * MIN_TEETH_PLANET, int(math.floor(target)) - step)
        z_ring = next_ring_teeth(z_sun, n_planets, lower)

        tried = 0
        while z_ring is not None and z_ring <= ring_max and tried < MAX_RING_CANDIDATES:
            if tried == 0 or z_ring <= target + step:
                yield z_sun, z_ring
            z_ring += step
            tried += 1


def _search(
    module: float,
    n_planets: int,
    i_requested: float,
    d_max: float,
    configuration: TrainConfiguration | None = None,
) -> list[_Candidate]:
    """All structurally valid combinations, closest ratio first."""
    config = configuration or CONFIGURATIONS[DEFAULT_CONFIGURATION]

    found: list[_Candidate] = []
    for z_sun, z_ring in _candidate_pairs(
        module, n_planets, i_requested, d_max, config
    ):
        candidate = _candidate(
            module, n_planets, i_requested, z_sun, z_ring, d_max, config
        )
        if candidate is not None:
            found.append(candidate)

    found.sort(key=lambda c: (round(c.ratio_deviation, 9), c.d_ext, c.z_sun))
    return found


# --- Guidance for infeasible inputs -----------------------------------------


def _closest_workable_ratio(
    module: float,
    n_planets: int,
    i_requested: float,
    d_max: float,
    tolerance: float,
    configuration: TrainConfiguration | None = None,
    max_attempts: int = 25,
) -> tuple[float, _Candidate] | None:
    """Nearest reachable ratio, walking toward 1 from the request.

    Adjacency, the minimum tooth count and the envelope cap the ratio a given
    planet count can achieve. A reducer is capped above, so it walks down; a
    speed increase is capped below, so it walks up. Both directions move toward
    i = 1, which is the boundary the geometry always allows.
    """
    config = configuration or CONFIGURATIONS[DEFAULT_CONFIGURATION]

    if config.reduction:
        step = max(0.05, round(i_requested * 0.02, 2))
        candidate = i_requested - step
        limit = 1.02
        forward = -1
    else:
        step = max(0.005, round(i_requested * 0.02, 3))
        candidate = i_requested + step
        limit = 0.98
        forward = 1

    for _ in range(max_attempts):
        if (candidate <= limit) if forward < 0 else (candidate >= limit):
            return None
        hits = [
            s
            for s in _search(module, n_planets, candidate, d_max, config)
            if s.ratio_deviation <= tolerance
        ]
        if hits:
            return candidate, hits[0]
        candidate += step * forward

    return None


def _build_diagnostics(
    module: float,
    n_planets: int,
    i_requested: float,
    d_max: float,
    tolerance: float,
    configuration: TrainConfiguration | None = None,
    language: str = "en",
) -> tuple[str, tuple[str, ...]]:
    """Return (which constraint binds, what to change about it)."""
    config = configuration or CONFIGURATIONS[DEFAULT_CONFIGURATION]
    language = normalize_language(language)
    suggestions: list[str] = []

    # Same search, envelope removed: the only thing this drops is D_max.
    unconstrained = [
        s
        for s in _search(module, n_planets, i_requested, math.inf, config)
        if s.ratio_deviation <= tolerance
    ]

    if not unconstrained:
        diagnosis = tr(
            language,
            "core.diag.ratio",
            i=i_requested,
            tol=tolerance,
            n=n_planets,
        )
    else:
        needed = min(s.d_ext for s in unconstrained)
        if needed > d_max:
            diagnosis = tr(
                language, "core.diag.envelope", needed=needed, d_max=d_max
            )
            suggestions.append(
                tr(language, "core.sugg.d_max", needed=needed, module=module)
            )
        else:  # pragma: no cover - defensive, the search above is exhaustive
            diagnosis = tr(language, "core.diag.generic")

    for smaller in reversed([m for m in STANDARD_MODULES if m < module]):
        hits = [
            s
            for s in _search(smaller, n_planets, i_requested, d_max, config)
            if s.ratio_deviation <= tolerance
        ]
        if hits:
            best = min(hits, key=lambda s: (s.ratio_deviation, s.d_ext))
            suggestions.append(
                tr(
                    language,
                    "core.sugg.module",
                    module=smaller,
                    zs=best.z_sun,
                    zp=best.z_planet,
                    zr=best.z_ring,
                    i=best.i_real,
                    d_ext=best.d_ext,
                )
            )
            break

    for n_alt in range(n_planets - 1, 1, -1):
        hits = [
            s
            for s in _search(module, n_alt, i_requested, d_max, config)
            if s.ratio_deviation <= tolerance
        ]
        if hits:
            best = min(hits, key=lambda s: (s.ratio_deviation, s.d_ext))
            suggestions.append(
                tr(
                    language,
                    "core.sugg.planets",
                    n=n_alt,
                    old=n_planets,
                    zs=best.z_sun,
                    zp=best.z_planet,
                    zr=best.z_ring,
                    i=best.i_real,
                    d_ext=best.d_ext,
                )
            )
            break

    lowered = _closest_workable_ratio(
        module, n_planets, i_requested, d_max, tolerance, config
    )
    if lowered is not None:
        ratio, best = lowered
        suggestions.append(
            tr(
                language,
                "core.sugg.move_ratio",
                ratio=ratio,
                zs=best.z_sun,
                zp=best.z_planet,
                zr=best.z_ring,
                i=best.i_real,
                d_ext=best.d_ext,
            )
        )

    if not suggestions:
        suggestions.append(tr(language, "core.sugg.relax"))

    return diagnosis, tuple(suggestions)


# --- Public entry point -----------------------------------------------------


def solve_planetary(
    module: float,
    n_planets: int,
    i_requested: float,
    d_max: float,
    max_alternatives: int = 3,
    tolerance: float = DEFAULT_RATIO_TOLERANCE,
    configuration: str | TrainConfiguration | None = None,
    language: str = "en",
) -> SolveResult:
    """Solve the single-stage planetary train for the given inputs.

    Args:
        module: gear module m in millimetres (positive).
        n_planets: number of equally spaced planets N (integer >= 2).
        i_requested: requested ratio, i = w_driver / w_driven. Greater than 1 for
            a reducer, smaller than 1 for a speed increase; which one is valid
            depends on the configuration.
        d_max: maximum allowed outside diameter of the ring gear, in mm.
        max_alternatives: how many near-ratio alternatives to return.
        tolerance: accepted relative deviation between i_real and i_requested.
        configuration: key of a `CONFIGURATIONS` entry (or the entry itself).
            Decides which member is fixed, which is driven and which one turns
            the load, and therefore which ratio law applies.
        language: "en" or "es"; every user-facing sentence is reported in it.

    Returns:
        A SolveResult. When a solution exists, `best` is the closest ratio and
        `alternatives` holds the next closest designs. When none exists,
        `ok` is False and `suggestions` explains how to unblock it.
    """
    config = get_configuration(configuration)
    language = normalize_language(language)

    validate_inputs(module, n_planets, i_requested, d_max, config, language)
    if max_alternatives < 0:
        raise ValueError(tr(language, "core.error.max_alternatives"))
    if tolerance < 0:
        raise ValueError(tr(language, "core.error.tolerance"))

    found = _search(module, n_planets, i_requested, d_max, config)

    if not found:
        diagnosis, suggestions = _build_diagnostics(
            module, n_planets, i_requested, d_max, tolerance, config, language
        )
        return SolveResult(
            ok=False,
            best=None,
            alternatives=(),
            message=tr(language, "core.message.no_solution"),
            suggestions=suggestions,
            d_max=d_max,
            tolerance=tolerance,
            diagnosis=diagnosis,
            configuration=config,
        )

    def materialise(candidate: _Candidate) -> Solution:
        return _evaluate(
            module,
            n_planets,
            i_requested,
            d_max,
            candidate.z_sun,
            candidate.z_ring,
            tolerance,
            config,
            language,
        )

    best = materialise(found[0])
    alternatives = tuple(materialise(c) for c in found[1 : 1 + max_alternatives])

    if best.valid:
        message = tr(
            language,
            "core.message.solution",
            zs=best.z_sun,
            zp=best.z_planet,
            zr=best.z_ring,
            i=best.i_real,
        )
    else:
        failed = ", ".join(c.label for c in best.failed_checks)
        message = tr(
            language,
            "core.message.best_partial",
            zs=best.z_sun,
            zp=best.z_planet,
            zr=best.z_ring,
            failed=failed,
        )

    return SolveResult(
        ok=True,
        best=best,
        alternatives=alternatives,
        message=message,
        suggestions=(),
        d_max=d_max,
        tolerance=tolerance,
        configuration=config,
    )
