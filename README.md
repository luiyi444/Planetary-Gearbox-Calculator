# Planetary Gearbox Calculator

Desktop calculator for a **single-stage planetary (epicyclic) gear train**: sun,
ring, planet carrier and the planets between them. You choose which member is
fixed and which one drives — the classic reducer (ring fixed, sun in, carrier
out) is only one of the four useful arrangements — and the program returns the
complete tooth geometry with the verdict of every design condition, individually
explained.

You enter four parameters, you get the design. The interface speaks **English and
Spanish**, switched from the header without losing what you typed.

**It runs fully local and has no external dependencies.** It is Python and its
standard library only: no `pip install`, no virtual environment, no web server, no
browser, no internet connection. The window is drawn with Tkinter, which ships
inside the standard Python installer.

| Input | Meaning |
| --- | --- |
| `m` (mm) | Gear module, from the standard metric series |
| `N` | Number of equally spaced planets (2–6) |
| `i` | Requested ratio, defined as `i = ω driver / ω driven` |
| `D_max` (mm) | Maximum allowed outside diameter of the ring gear |
| Configuration | Which member is fixed, which one drives, which one is driven |

| Output | Meaning |
| --- | --- |
| `Zs`, `Zp`, `Zr` | Tooth counts of sun, planets and ring |
| `i_real` | Real ratio of the rounded tooth set, with its deviation from `i` |
| Kinematics line | Names who drives, who is driven, who is fixed, and whether the train reduces or multiplies speed |
| Pitch diameters | `ds = m·Zs`, `dp = m·Zp`, `dr = m·Zr`, carrier, ring outside |
| Checks | PASS/FAIL for concentricity, assembly, adjacency, envelope, tooth limits, ratio tolerance |
| Schematic | Top view of the train against the allowed envelope, with the fixed member ground-hatched |
| Alternatives | Up to three other trains, closest ratio first, with the condition each one fails |

Two optional fields sit under **Advanced**: the ratio tolerance in percent
(5 % by default) and how many alternatives to list (3 by default). Everything
recalculates as you type.

## Who drives: `4:1` is not `1:4`

This is the part that is easy to get wrong, and getting it wrong silently
inverts the answer. A planetary train has three rotating members and **exactly
one of them is held fixed**, which leaves four arrangements. They do **not**
share the same ratio law:

| Configuration | Ratio law | Range |
| --- | --- | --- |
| Ring fixed · sun drives · carrier driven | `i = 1 + Zr/Zs` | `i > 1` (reduction) |
| Ring fixed · carrier drives · sun driven | `i = Zs/(Zs + Zr)` | `i < 1` (speed increase) |
| Sun fixed · carrier drives · ring driven | `i = 1 + Zs/Zr` | `i > 1` (reduction) |
| Sun fixed · ring drives · carrier driven | `i = Zr/(Zs + Zr)` | `i < 1` (speed increase) |

The same tooth set gives `i = 4` in one direction and `i = 0.25` in the other,
because `i` is defined as `ω_driver / ω_driven` and swapping the driver with the
driven member inverts it. So `4:1` and `1:4` are **different machines**.

The program never decides that for you: you pick the configuration, and it
validates the ratio against it. Ask for `i = 4` in a speed-increase configuration
and it answers with the ratio that configuration would need instead:

> With «Ring fixed · carrier drives · sun driven» the ratio is
> `i = Zs/(Zs + Zr)`, so i must be smaller than 1 (a speed increase). For the
> inverse (i > 1) pick the configuration where the driver and the driven member
> are swapped: `i = 0.25`.

The read-out always states the roles in plain words — *"Carrier is the driver,
sun the driven member, ring stays fixed… the driven runs 4.00 times faster"* —
and the schematic legend labels every member `driver`, `driven`, `fixed` or
`idle`, with the ground hatch on the fixed one.

## Language

The `EN` / `ES` pill in the header switches the whole window: field labels,
section titles, the check list, the diagnosis, the suggestions and the schematic
legend. Your inputs and the selected configuration survive the switch.

Every user-facing sentence lives in `i18n.py`, used by both the interface and the
calculation core, so nothing is translated twice or left behind. The desktop app
starts in Spanish; a caller of `solve_planetary(..., language="es")` gets Spanish,
and an unsupported code falls back to the English reference wording instead of
silently picking a different language.

## Interface

A sunset palette: warm cream background (`#FFF8F3`), an orange→plum gradient
header (`#F2A03D` → `#E4572E` → `#6B2D5B`), white cards with a plum text
(`#3A2230`) and magenta section titles (`#B23A6F`).

On Windows the process declares per-monitor DPI awareness before creating the
window: without it the system renders the app at a virtual 1280×720 and stretches
it, which blurs every label on a scaled display. The window size is derived from
the actual monitor, and its minimum size is measured from the layout itself, so
no table row or label gets clipped in either language.

## Run it

**Double-click `run.bat`.** That is the whole installation procedure.

Requirements, both already included in the standard installer from
<https://www.python.org/downloads/>:

- Python 3.9 or newer
- Tkinter (the "tcl/tk and IDLE" component, selected by default)

`run.bat` checks both before starting and tells you exactly what is missing if
either is absent. From a terminal it is just as short:

```powershell
python desktop.py
```

> **Why not `run.ps1`?** Windows has no file association for `.ps1`, so a
> double-click opens the script in Notepad instead of running it. That is by
> design: PowerShell scripts are protected from accidental execution. Use
> `run.bat`, or call the script explicitly with
> `powershell -ExecutionPolicy Bypass -File .\run.ps1`.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Standard library only, so this also needs nothing installed:

- `tests/test_gearbox.py` — the calculation core: the reference train, one test
  per design condition, rounding behaviour, infeasible inputs, input validation,
  alternative ordering, the agreement between the fast scan filter and the
  displayed checks, the four kinematic configurations (including that the same
  tooth set gives `i` and `1/i` when the driver swaps) and the solver's language.
- `tests/test_desktop.py` — the real Tk widgets, driven with a withdrawn window:
  default state, impossible envelope, garbage input, decimal comma, the schematic
  drawing, the driver/role read-out, the language switch and the window sizing.
- `tests/test_i18n.py` — that every key exists in both languages, that no prose
  entry is accidentally left untranslated, and that placeholders are formatted.

## The math being coded

Geometry is independent of **who drives**, so it is shared by every configuration
(Willis' equation):

```
Zr           = Zs + 2 · Zp              concentricity (coaxial mounting)
(Zs + Zr) mod N = 0                     assembly of N equally spaced planets
(Zs + Zp)·sin(π/N) > Zp + 2             adjacency (planets do not touch)
D_ext        = m · (Zr + 2.5) ≤ D_max   outside diameter, rim included
Zp           = (Zr − Zs) / 2            must be an integer (parity)
```

Only the law that turns the requested ratio into a ring tooth count depends on the
configuration (`i = ...` column of the table above). Each of those laws is
**linear in `Zs`**, which is what lets one exact sweep bound serve all four.

Assumed limits: standard 20° full-depth involute, so `Zs ≥ 17` and `Zp ≥ 17` to
avoid undercut; a 2-tooth-equivalent gap between neighbouring planets; and
2.5 modules added to the ring pitch diameter for the outside dimension
(two addenda plus one rim).

### How the tooth counts are solved

1. Sweep the sun tooth count `Zs` upwards from 17.
2. The ideal ring for that sun follows the configuration's law — for the default
   reducer, `Zr = Zs·(i − 1)`.
3. Round `Zr` up to the first integer that satisfies **parity**
   (`Zr − Zs` even) and **assembly** (`(Zs + Zr) mod N = 0`). Those two
   congruences always have a solution, so the rounding step never dead-ends by
   itself.
4. `Zp` follows from concentricity.
5. Check adjacency, envelope and tooth limits. Keep every structurally valid
   combination, sort by `|i_real − i|`, present the closest as the design and the
   next ones as alternatives.
6. The module stays out of the search: it only scales the diameters, exactly as
   the theory requires.

Because tooth counts are integers, `i_real` almost never equals the requested
`i`. The difference is always reported, and the tolerance field (5 % by default)
decides whether an otherwise valid train is flagged.

When nothing satisfies all conditions, the window does not show a fake result: it
names the **binding constraint** and lists concrete changes that would make the
design possible.

## Reference case: why `D_max = 100` cannot work

The original acceptance criterion asked for **m = 2, N = 3, i = 4, D_max = 100**
to return `Zs = 18, Zr = 54, Zp = 18`.

Those tooth counts are correct — they satisfy every kinematic condition. But:

```
dr     = m · Zr        = 2 · 54        = 108 mm   (pitch diameter alone)
D_ext  = m · (Zr + 2.5) = 2 · 56.5     = 113 mm
```

**113 mm > 100 mm**, and even the bare pitch circle of the ring (108 mm) is
already larger than the envelope. No usable train at `i = 4`, `m = 2` fits in
100 mm, with any sun size: the envelope needs `Zr ≤ 47`, while the minimum planet
tooth count forces `Zr ≥ Zs + 34 ≥ 51`.

So the reference case is documented and tested with **`D_max = 120 mm`**, where it
returns exactly `Zs = 18, Zp = 18, Zr = 54, i_real = 4.000`, and the 100 mm case is
tested as an **infeasible input that must answer with guidance instead of
crashing**. That is the behaviour the third acceptance criterion actually asks
for.

If a 100 mm outer diameter is a hard requirement, the way out is a smaller module
(the calculator suggests it: `m = 1.5` puts the same tooth set at 85 mm).

## Acceptance criteria status

| Criterion | Status |
| --- | --- |
| `m = 2, N = 3, i = 4` gives `Zs = 18, Zr = 54, Zp = 18` | ✅ at `D_max ≥ 113 mm` (see above) |
| Impossible combinations answer clearly, never crash | ✅ |
| The four conditions shown individually with their state | ✅ |
| `i_real` shown next to the requested `i` | ✅ |
| Calculation tests pass without the UI | ✅ |
| English/Spanish interface switch | ✅ |
| The driver is stated explicitly, `4:1` and `1:4` are different machines | ✅ four configurations, each with its own ratio law |
| Modern interface with a sunset palette | ✅ |
| Runs with no external dependency | ✅ |

## Project layout

```
Planetary-Gearbox-Calculator/
├── gearbox.py            calculation core (pure, UI-free, stdlib only)
├── i18n.py               every user-facing sentence, in English and Spanish
├── desktop.py            Tkinter window — the application
├── run.bat               double-click launcher (checks Python and Tkinter)
├── run.ps1               same, from a terminal
├── README.md
├── tests/
│   ├── test_gearbox.py   unit tests of the solver and every design condition
│   ├── test_desktop.py   tests driving the real widgets
│   └── test_i18n.py      translation table and coverage tests
└── web-legacy/           optional Streamlit version (needs third-party packages)
```

## Out of scope (documented, not implemented)

- Tooth strength and durability (AGMA / ISO): bending, pitting, safety factors
- Materials, heat treatment, face width, backlash selection
- Helical or double-helical gearing, profile shifts, non-standard pressure angles
- Load sharing between planets, shaft and bearing sizing
- CAD export, tolerances and manufacturing drawings
- Multi-stage trains (this is a single stage)

`web-legacy/` is kept only for reference; nothing in the main path imports it.
See its own README if you ever want the browser version.

## References

- R. L. Norton, *Design of Machinery* — gear trains, Willis' equation
- R. L. Norton, *Machine Design* — planetary trains, tooth-count conditions
- G. Budynas & J. K. Nisbett, *Shigley's Mechanical Engineering Design* — gear
  tooth geometry and the minimum tooth count for a 20° involute
- *Gear Geometry and Applied Theory* (Litvin & Fuentes) — tooth-count limits
