"""Self-contained desktop interface for the planetary gearbox calculator.

Standard library only. Tkinter ships with CPython, so this program needs no
package installation, no virtual environment, no internet connection, no web
server and no browser:

    python desktop.py

Three things it makes explicit, because they are easy to get wrong:

* **Who is the driver.** A planetary train has three members and one of them is
  fixed, which leaves four useful arrangements. Swapping the driver and the
  driven member turns a reduction into a speed increase and inverts the ratio,
  so the configuration selector decides which ratio law applies and the read-out
  names the driver, the driven member and the fixed one.
* **Language.** English and Spanish, switched from the header; every sentence
  comes from `i18n`, including the ones produced by the solver.
* **Colour.** A sunset palette: warm cream background, orange to plum gradient
  header, white cards.

Every number shown comes from `gearbox.py`, which is pure Python too.
"""

from __future__ import annotations

import ctypes
import math
import tkinter as tk
import tkinter.font as tkinter_font
from tkinter import messagebox, ttk

import gearbox as gb
import i18n
from i18n import tr

# --- Sunset palette ---------------------------------------------------------

BG = "#FFF8F3"
"""Window background: warm cream, the paper the whole design sits on."""

SURFACE = "#FFFFFF"
"""Card background."""

SURFACE_ALT = "#FCEFE6"
"""Card header strip and table heading background."""

BORDER = "#F3D5C4"
"""Hairline around cards and inputs."""

TEXT = "#3A2230"
"""Primary text: deep plum, never pure black, to keep the palette warm."""

MUTED = "#8A6B77"
"""Secondary text."""

PRIMARY = "#E4572E"
"""Sunset orange: the main accent."""

SECONDARY = "#F2A03D"
"""Sunset amber: the start of the header gradient."""

ACCENT = "#B23A6F"
"""Sunset magenta: section titles and headings."""

PLUM = "#6B2D5B"
"""Deep plum: the end of the header gradient."""

PASS_COLOR = "#1F7A5C"
FAIL_COLOR = "#C0392B"
GRID = "#E8CFC0"

COLOR_SUN = "#F2A03D"
COLOR_SUN_EDGE = "#A9670F"
COLOR_PLANET = "#B23A6F"
COLOR_PLANET_EDGE = "#7C2650"
COLOR_RING = "#6B2D5B"
COLOR_ENVELOPE = "#E4572E"

# --- Typography -------------------------------------------------------------

FONT_FAMILY = "Segoe UI"
FONT_BASE = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_BOLD = (FONT_FAMILY, 9, "bold")
FONT_NAME = (FONT_FAMILY, 10, "bold")
FONT_MONO = ("Consolas", 9)
FONT_METRIC = (FONT_FAMILY, 20, "bold")
FONT_CARD_TITLE = (FONT_FAMILY, 9, "bold")
FONT_TITLE = (FONT_FAMILY, 15, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 9)

WINDOW_MIN = (1180, 700)
"""Smallest useful window: below this the two columns and the schematic clash."""

WINDOW_PREFERRED = (1460, 940)
"""Preferred window size; clamped to whatever the monitor actually offers."""

HEADER_HEIGHT = 74
LEGEND_ROW_HEIGHT = 22
"""Row pitch of the legend: it must exceed the 9 pt text height at high DPI."""

CONFIGURATION_ORDER: tuple[str, ...] = (
    "ring_fixed_sun_drive",
    "ring_fixed_carrier_drive",
    "sun_fixed_carrier_drive",
    "sun_fixed_ring_drive",
)
"""Configurations offered in the selector, reducer first."""


def _default_geometry(root: tk.Misc) -> tuple[str, tuple[int, int]]:
    """Preferred window size, clamped so it always fits the real monitor.

    A fixed `1440x880` is fine on a 1920x1080 screen and hangs off the edge of a
    1366x768 laptop, so the window and its own minimum both derive from what the
    screen offers.
    """
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    width = max(min(WINDOW_PREFERRED[0], screen_width - 80), 900)
    height = max(min(WINDOW_PREFERRED[1], screen_height - 90), 560)

    min_width = min(WINDOW_MIN[0], width)
    min_height = min(WINDOW_MIN[1], height)
    return f"{width}x{height}", (min_width, min_height)


def _parse_number(text: str) -> float:
    """Parse a user field, accepting a decimal comma and stray spaces."""
    cleaned = str(text).strip().replace("%", "").replace(" ", "").replace(",", ".")
    if not cleaned:
        raise ValueError("empty field")
    return float(cleaned)


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _gradient_color(stops: list[tuple[float, str]], position: float) -> str:
    """Colour at `position` (0..1) along a multi-stop gradient."""
    position = min(max(position, 0.0), 1.0)
    for index in range(len(stops) - 1):
        start, start_color = stops[index]
        end, end_color = stops[index + 1]
        if start <= position <= end:
            span = end - start
            local = 0.0 if span == 0 else (position - start) / span
            r1, g1, b1 = _hex_to_rgb(start_color)
            r2, g2, b2 = _hex_to_rgb(end_color)
            return "#{:02x}{:02x}{:02x}".format(
                round(r1 + (r2 - r1) * local),
                round(g1 + (g2 - g1) * local),
                round(b1 + (b2 - b1) * local),
            )
    return stops[-1][1]


class PlanetaryCalculatorApp:
    """Main window: inputs on the left, design report and schematic on the right."""

    def __init__(self, root: tk.Tk, language: str | None = None) -> None:
        self.root = root
        self.language = i18n.app_language(language)
        self.configuration_key = gb.DEFAULT_CONFIGURATION
        self._result: gb.SolveResult | None = None
        self._solution: gb.Solution | None = None
        self._configuration_labels: dict[str, str] = {}

        geometry, minimum = _default_geometry(root)
        root.title(tr(self.language, "ui.window.title"))
        root.minsize(*minimum)
        root.geometry(geometry)
        root.configure(bg=BG)
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        self._create_variables()
        self._configure_styles()
        self._build_layout()
        self._calculate()
        self._fit_window()

    def _fit_window(self) -> None:
        """Never let the window shrink below the size its own content needs.

        A hard-coded minimum always drifts once a label grows or a translation
        gets longer, and a clipped table looks like a bug. Asking the layout
        what it needs keeps the minimum honest on every language.
        """
        self.root.update_idletasks()

        needed_width = self.root.winfo_reqwidth()
        needed_height = self.root.winfo_reqheight()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        min_width = min(max(needed_width, WINDOW_MIN[0]), screen_width - 40)
        min_height = min(max(needed_height, WINDOW_MIN[1]), screen_height - 60)
        self.root.minsize(min_width, min_height)

        # If the layout needs more room than the preferred size, honour it,
        # unless that would push the window off the monitor.
        geometry, _minimum = _default_geometry(self.root)
        preferred_width, preferred_height = (
            int(value) for value in geometry.split("x")
        )
        width = min(max(preferred_width, min_width), screen_width - 40)
        height = min(max(preferred_height, min_height), screen_height - 60)
        self.root.geometry(f"{width}x{height}")

    # -- state ---------------------------------------------------------------

    def _create_variables(self) -> None:
        self.module_var = tk.StringVar(value="2")
        self.planets_var = tk.StringVar(value="3")
        self.ratio_var = tk.StringVar(value="4")
        self.d_max_var = tk.StringVar(value="120")
        self.tolerance_var = tk.StringVar(value=f"{gb.DEFAULT_RATIO_TOLERANCE * 100:g}")
        self.alternatives_var = tk.StringVar(value="3")
        self.configuration_var = tk.StringVar(value="")

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG, foreground=TEXT, font=FONT_BASE)
        style.configure("App.TFrame", background=BG)
        style.configure("Card.TFrame", background=SURFACE)

        style.configure(
            "Card.TLabelframe",
            background=SURFACE,
            bordercolor=BORDER,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=SURFACE,
            foreground=ACCENT,
            font=FONT_NAME,
        )

        style.configure("Body.TLabel", background=BG, foreground=TEXT)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=FONT_SMALL)
        style.configure("Pass.TLabel", background=BG, foreground=PASS_COLOR, font=FONT_NAME)
        style.configure("Fail.TLabel", background=BG, foreground=FAIL_COLOR, font=FONT_NAME)
        style.configure("Warn.TLabel", background=BG, foreground="#9A6200", font=FONT_NAME)

        style.configure(
            "Sunset.TEntry",
            fieldbackground=SURFACE,
            foreground=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            insertcolor=TEXT,
            padding=(4, 3),
        )
        for name in ("Sunset.TCombobox", "Sunset.TSpinbox"):
            style.configure(
                name,
                fieldbackground=SURFACE,
                background=SURFACE,
                foreground=TEXT,
                arrowcolor=PRIMARY,
                bordercolor=BORDER,
                lightcolor=SURFACE,
                darkcolor=SURFACE,
                padding=(4, 3),
            )
            style.map(
                name,
                fieldbackground=[("readonly", SURFACE), ("focus", SURFACE)],
                background=[("readonly", SURFACE)],
                foreground=[("readonly", TEXT)],
                selectbackground=[("readonly", SURFACE)],
                selectforeground=[("readonly", TEXT)],
                bordercolor=[("focus", PRIMARY)],
            )

        style.configure(
            "Sunset.Horizontal.TProgressbar",
            background=PRIMARY,
            troughcolor=SURFACE_ALT,
            bordercolor=BORDER,
            lightcolor=PRIMARY,
            darkcolor=PRIMARY,
            thickness=8,
        )

        style.configure(
            "Sunset.Treeview",
            background=SURFACE,
            fieldbackground=SURFACE,
            foreground=TEXT,
            bordercolor=BORDER,
            rowheight=22,
        )
        style.configure(
            "Sunset.Treeview.Heading",
            background=SURFACE_ALT,
            foreground=ACCENT,
            font=FONT_BOLD,
            relief="flat",
        )
        style.map("Sunset.Treeview.Heading", background=[("active", SURFACE_ALT)])

        style.configure(
            "Sunset.Vertical.TScrollbar",
            background=SURFACE_ALT,
            troughcolor=SURFACE,
            bordercolor=SURFACE,
            arrowcolor=ACCENT,
        )

    # -- layout --------------------------------------------------------------

    def _build_layout(self) -> None:
        self._build_header()

        content = ttk.Frame(self.root, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 12))
        content.columnconfigure(0, weight=0, minsize=380)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        left = ttk.Frame(content, style="App.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        right = ttk.Frame(content, style="App.TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        # The schematic is the part that must never collapse: minimum height
        # first, then whatever extra the window has.
        right.rowconfigure(4, weight=1, minsize=230)

        self._build_inputs(left)
        self._build_verification(left)
        self._build_readout(right)
        self._build_diagram(right)
        self._build_alternatives(right)

    # -- header --------------------------------------------------------------

    def _build_header(self) -> None:
        self.header = tk.Canvas(
            self.root,
            height=HEADER_HEIGHT,
            highlightthickness=0,
            borderwidth=0,
            background=SECONDARY,
        )
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.bind("<Configure>", self._draw_header)
        self._small_font = tkinter_font.Font(font=FONT_SUBTITLE)

    def _draw_header(self, event=None) -> None:  # noqa: ARG002 - Tk passes an event
        canvas = self.header
        canvas.delete("all")

        width = canvas.winfo_width()
        height = HEADER_HEIGHT
        if width < 100:
            return

        stops = [(0.0, SECONDARY), (0.55, PRIMARY), (1.0, PLUM)]
        band = 4
        for x in range(0, width, band):
            canvas.create_rectangle(
                x,
                0,
                min(x + band, width),
                height,
                fill=_gradient_color(stops, x / max(width - 1, 1)),
                outline="",
            )

        canvas.create_text(
            20,
            26,
            text=tr(self.language, "ui.header.title"),
            anchor="w",
            fill="#FFFFFF",
            font=FONT_TITLE,
        )
        canvas.create_text(
            20,
            52,
            text=tr(self.language, "ui.header.subtitle"),
            anchor="w",
            fill="#FFE6D2",
            font=FONT_SUBTITLE,
        )

        self._draw_language_switch(canvas, width, height)

    def _draw_language_switch(self, canvas: tk.Canvas, width: int, height: int) -> None:
        """Two pill segments on the right of the header: one per language."""
        pad = 12
        pill_height = 26
        gap = 2
        measure = self._small_font.measure

        segments = [
            (language, i18n.language_name(language), measure(i18n.language_name(language)) + 2 * pad)
            for language in i18n.LANGUAGES
        ]
        total = sum(segment[2] for segment in segments) + gap * (len(segments) - 1)
        x = width - 18 - total
        y = (height - pill_height) / 2

        for language, label, segment_width in segments:
            tag = f"language-{language}"
            active = language == self.language
            canvas.create_rectangle(
                x,
                y,
                x + segment_width,
                y + pill_height,
                fill="#FFFFFF" if active else "",
                outline="#FFFFFF" if not active else "",
                width=1,
                tags=(tag,),
            )
            canvas.create_text(
                x + segment_width / 2,
                y + pill_height / 2,
                text=label,
                fill=PRIMARY if active else "#FFFFFF",
                font=FONT_BOLD,
                tags=(tag,),
            )
            canvas.tag_bind(
                tag, "<Button-1>", lambda _event, code=language: self.set_language(code)
            )
            canvas.tag_bind(tag, "<Enter>", lambda _event: canvas.configure(cursor="hand2"))
            canvas.tag_bind(tag, "<Leave>", lambda _event: canvas.configure(cursor=""))
            x += segment_width + gap

    # -- language ------------------------------------------------------------

    def set_language(self, language: str) -> None:
        """Switch language and rebuild the window, keeping every entered value."""
        language = i18n.normalize_language(language)
        if language == self.language:
            return
        self.language = language
        self.root.title(tr(language, "ui.window.title"))
        for child in self.root.winfo_children():
            child.destroy()
        self._build_layout()
        self._calculate()
        self._fit_window()

    # -- left column ---------------------------------------------------------

    def _build_inputs(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(
            parent, text=tr(self.language, "ui.section.inputs"), style="Card.TLabelframe", padding=10
        )
        box.grid(row=0, column=0, sticky="ew", pady=(12, 0))
        box.columnconfigure(1, weight=1)
        box.columnconfigure(3, weight=1)

        ttk.Label(box, text=tr(self.language, "ui.field.module"), style="Body.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 6)
        )
        module_box = ttk.Combobox(
            box,
            textvariable=self.module_var,
            values=[f"{module:g}" for module in gb.STANDARD_MODULES],
            width=8,
            style="Sunset.TCombobox",
        )
        module_box.grid(row=0, column=1, sticky="ew", pady=(0, 6))
        self._bind_live(module_box)
        module_box.bind("<<ComboboxSelected>>", self._calculate)

        ttk.Label(box, text=tr(self.language, "ui.field.planets"), style="Body.TLabel").grid(
            row=0, column=2, sticky="w", padx=(12, 6), pady=(0, 6)
        )
        planets_box = ttk.Spinbox(
            box,
            from_=2,
            to=6,
            textvariable=self.planets_var,
            width=6,
            style="Sunset.TSpinbox",
        )
        planets_box.grid(row=0, column=3, sticky="ew", pady=(0, 6))
        self._bind_live(planets_box, command=self._calculate)

        ttk.Label(box, text=tr(self.language, "ui.field.ratio"), style="Body.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 6), pady=(0, 6)
        )
        ratio_entry = ttk.Entry(
            box, textvariable=self.ratio_var, width=8, style="Sunset.TEntry"
        )
        ratio_entry.grid(row=1, column=1, sticky="ew", pady=(0, 6))
        self._bind_live(ratio_entry)

        ttk.Label(box, text=tr(self.language, "ui.field.d_max"), style="Body.TLabel").grid(
            row=1, column=2, sticky="w", padx=(12, 6), pady=(0, 6)
        )
        d_max_entry = ttk.Entry(
            box, textvariable=self.d_max_var, width=8, style="Sunset.TEntry"
        )
        d_max_entry.grid(row=1, column=3, sticky="ew", pady=(0, 6))
        self._bind_live(d_max_entry)

        ttk.Label(
            box, text=tr(self.language, "ui.field.configuration"), style="Body.TLabel"
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(0, 3))
        self._configuration_labels = {
            tr(self.language, f"config.{key}.label"): key for key in CONFIGURATION_ORDER
        }
        self.configuration_var.set(
            tr(self.language, f"config.{self.configuration_key}.label")
        )
        configuration_box = ttk.Combobox(
            box,
            textvariable=self.configuration_var,
            values=list(self._configuration_labels),
            state="readonly",
            style="Sunset.TCombobox",
        )
        # Full card width: the labels name three members and get long in Spanish.
        configuration_box.grid(row=3, column=0, columnspan=4, sticky="ew")
        configuration_box.bind("<<ComboboxSelected>>", self._on_configuration_change)
        self.configuration_box = configuration_box

        ttk.Label(
            box,
            text=tr(self.language, "ui.hint.ratio"),
            style="Muted.TLabel",
        ).grid(row=4, column=0, columnspan=4, sticky="w", pady=(6, 0))

        advanced = ttk.LabelFrame(
            parent,
            text=tr(self.language, "ui.section.advanced"),
            style="Card.TLabelframe",
            padding=10,
        )
        advanced.grid(row=1, column=0, sticky="ew", pady=8)
        advanced.columnconfigure(1, weight=1)
        advanced.columnconfigure(3, weight=1)

        ttk.Label(
            advanced, text=tr(self.language, "ui.field.tolerance"), style="Body.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(
            advanced, textvariable=self.tolerance_var, width=8, style="Sunset.TEntry"
        ).grid(row=0, column=1, sticky="ew")

        ttk.Label(
            advanced, text=tr(self.language, "ui.field.alternatives"), style="Body.TLabel"
        ).grid(row=0, column=2, sticky="w", padx=(12, 6))
        alternatives_box = ttk.Spinbox(
            advanced,
            from_=0,
            to=10,
            textvariable=self.alternatives_var,
            width=6,
            style="Sunset.TSpinbox",
        )
        alternatives_box.grid(row=0, column=3, sticky="ew")
        self._bind_live(alternatives_box, command=self._calculate)

    def _build_verification(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(
            parent,
            text=tr(self.language, "ui.section.verification"),
            style="Card.TLabelframe",
            padding=(0, 6),
        )
        box.grid(row=2, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)

        self.checks_text = tk.Text(
            box,
            wrap="word",
            width=1,
            height=1,
            font=FONT_BASE,
            background=SURFACE,
            foreground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            padx=10,
            pady=8,
            borderwidth=0,
            cursor="arrow",
            selectbackground=SURFACE_ALT,
            selectforeground=TEXT,
        )
        self.checks_text.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=(0, 4))

        scrollbar = ttk.Scrollbar(
            box, orient="vertical", command=self.checks_text.yview, style="Sunset.Vertical.TScrollbar"
        )
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=(0, 4))
        self.checks_text.configure(yscrollcommand=scrollbar.set, state="disabled")

        self.checks_text.tag_configure("pass", foreground=PASS_COLOR, font=FONT_BOLD)
        self.checks_text.tag_configure("fail", foreground=FAIL_COLOR, font=FONT_BOLD)
        self.checks_text.tag_configure("name", font=FONT_NAME, foreground=TEXT)
        self.checks_text.tag_configure("mono", font=FONT_MONO, foreground=MUTED)
        self.checks_text.tag_configure("muted", foreground=MUTED, font=FONT_SMALL)
        self.checks_text.tag_configure("heading", font=FONT_NAME, foreground=ACCENT)
        self.checks_text.tag_configure("error", foreground=FAIL_COLOR, font=FONT_NAME)

    # -- right column --------------------------------------------------------

    def _build_readout(self, parent: ttk.Frame) -> None:
        self.kinematics_label = ttk.Label(
            parent,
            text="",
            style="Body.TLabel",
            justify="left",
            wraplength=760,
        )
        self.kinematics_label.grid(row=0, column=0, sticky="ew", pady=(12, 8))

        self.message_label = ttk.Label(
            parent, text="", style="Body.TLabel", wraplength=760, justify="left"
        )
        self.message_label.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        cards = ttk.Frame(parent, style="App.TFrame")
        cards.grid(row=2, column=0, sticky="ew")
        for column in range(4):
            cards.columnconfigure(column, weight=1, uniform="card")

        self.metric_values: list[tk.Label] = []
        self.metric_captions: list[tk.Label] = []
        captions = (
            "ui.caption.zs",
            "ui.caption.zp",
            "ui.caption.zr",
            "ui.caption.i_real",
        )

        for column, caption_key in enumerate(captions):
            card = tk.Frame(
                cards,
                background=SURFACE,
                highlightbackground=BORDER,
                highlightthickness=1,
                padx=10,
                pady=8,
            )
            card.grid(
                row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0)
            )
            card.columnconfigure(0, weight=1)

            tk.Label(
                card,
                text=tr(self.language, caption_key),
                background=SURFACE,
                foreground=ACCENT,
                font=FONT_CARD_TITLE,
                anchor="w",
            ).grid(row=0, column=0, sticky="ew")

            value = tk.Label(
                card,
                text="—",
                background=SURFACE,
                foreground=PRIMARY,
                font=FONT_METRIC,
                anchor="w",
            )
            value.grid(row=1, column=0, sticky="ew")

            caption_label = tk.Label(
                card,
                text="",
                background=SURFACE,
                foreground=MUTED,
                font=FONT_SMALL,
                anchor="w",
            )
            caption_label.grid(row=2, column=0, sticky="ew")

            self.metric_values.append(value)
            self.metric_captions.append(caption_label)

        # Diameters, envelope bar and the design report card.
        report = tk.Frame(
            parent,
            background=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        report.grid(row=3, column=0, sticky="ew", pady=(10, 8))
        report.columnconfigure(0, weight=1)
        self.report_card = report

        self.diameters_label = tk.Label(
            report,
            text="",
            background=SURFACE,
            foreground=MUTED,
            font=FONT_SMALL,
            justify="left",
            anchor="w",
        )
        self.diameters_label.grid(row=0, column=0, sticky="ew")

        self.envelope_bar = ttk.Progressbar(
            report, maximum=100.0, value=0.0, style="Sunset.Horizontal.TProgressbar"
        )
        self.envelope_bar.grid(row=1, column=0, sticky="ew", pady=(8, 4))

        self.envelope_label = tk.Label(
            report,
            text="",
            background=SURFACE,
            foreground=MUTED,
            font=FONT_SMALL,
            anchor="w",
        )
        self.envelope_label.grid(row=2, column=0, sticky="ew")

    def _build_diagram(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(
            parent,
            text=tr(self.language, "ui.section.schematic"),
            style="Card.TLabelframe",
            padding=(6, 4),
        )
        box.grid(row=4, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            box,
            background=SURFACE,
            highlightthickness=0,
            borderwidth=0,
            height=240,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _build_alternatives(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(
            parent,
            text=tr(self.language, "ui.section.alternatives"),
            style="Card.TLabelframe",
            padding=(6, 4),
        )
        box.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        box.columnconfigure(0, weight=1)

        columns = ("zs", "zp", "zr", "ratio", "deviation", "d_ext", "status")
        self.alternatives_tree = ttk.Treeview(
            box,
            columns=columns,
            show="headings",
            height=3,
            selectmode="none",
            style="Sunset.Treeview",
        )
        headings = (
            ("zs", "ui.table.zs", 55),
            ("zp", "ui.table.zp", 55),
            ("zr", "ui.table.zr", 55),
            ("ratio", "ui.table.i_real", 75),
            ("deviation", "ui.table.deviation", 85),
            ("d_ext", "ui.table.d_ext", 90),
            ("status", "ui.table.status", 170),
        )
        for key, label_key, width in headings:
            self.alternatives_tree.heading(key, text=tr(self.language, label_key))
            self.alternatives_tree.column(key, width=width, anchor="center", stretch=True)
        self.alternatives_tree.grid(row=0, column=0, sticky="ew")

    def _bind_live(self, widget: tk.Widget, command=None) -> None:
        """Recompute on every keystroke and on arrow clicks."""
        widget.bind("<KeyRelease>", self._calculate)
        if command is not None:
            widget.configure(command=command)

    # -- events --------------------------------------------------------------

    def _on_configuration_change(self, event=None) -> None:  # noqa: ARG002
        selected = self.configuration_var.get()
        key = self._configuration_labels.get(selected)
        if key is None:
            return
        self.configuration_key = key
        self._calculate()

    # -- calculation ---------------------------------------------------------

    def _calculate(self, event=None) -> None:  # noqa: ARG002 - Tk passes an event
        try:
            module = _parse_number(self.module_var.get())
            n_planets = int(_parse_number(self.planets_var.get()))
            ratio = _parse_number(self.ratio_var.get())
            d_max = _parse_number(self.d_max_var.get())
            tolerance = _parse_number(self.tolerance_var.get()) / 100.0
            alternatives = int(_parse_number(self.alternatives_var.get()))
        except ValueError:
            self._show_invalid(tr(self.language, "ui.error.fields"))
            return

        try:
            result = gb.solve_planetary(
                module=module,
                n_planets=n_planets,
                i_requested=ratio,
                d_max=d_max,
                max_alternatives=max(alternatives, 0),
                tolerance=max(tolerance, 0.0),
                configuration=self.configuration_key,
                language=self.language,
            )
        except ValueError as error:
            self._show_invalid(str(error))
            return

        self._result = result
        self._solution = result.best
        self._render_result(result)
        self._draw()

    # -- rendering -----------------------------------------------------------

    def _configuration_names(self) -> tuple[str, str, str]:
        config = gb.get_configuration(self.configuration_key)
        return (
            tr(self.language, f"element.{config.driver}").capitalize(),
            tr(self.language, f"element.{config.driven}"),
            tr(self.language, f"element.{config.fixed}"),
        )

    def _show_invalid(self, message: str) -> None:
        self._result = None
        self._solution = None
        driver, driven, fixed = self._configuration_names()
        self.kinematics_label.configure(
            text=tr(
                self.language,
                "ui.kinematics.invalid",
                driver=driver,
                driven=driven,
                fixed=fixed,
            ),
            foreground=MUTED,
        )
        self.message_label.configure(text=message, style="Fail.TLabel")
        for value, caption in zip(self.metric_values, self.metric_captions):
            value.configure(text="—")
            caption.configure(text="")
        # No geometry to report: an empty white card reads as a bug.
        self.report_card.grid_remove()
        self.diameters_label.configure(text="")
        self.envelope_bar.configure(value=0.0)
        self.envelope_label.configure(text="")
        self.alternatives_tree.delete(*self.alternatives_tree.get_children())
        self._write_error(message)
        self._draw()

    def _render_result(self, result: gb.SolveResult) -> None:
        if not result.ok:
            self._render_infeasible(result)
            return

        best = result.best
        assert best is not None
        self.report_card.grid()

        self._render_kinematics(best)

        if best.valid:
            self.message_label.configure(text=result.message, style="Pass.TLabel")
        else:
            self.message_label.configure(text=result.message, style="Warn.TLabel")

        values = (
            str(best.z_sun),
            str(best.z_planet),
            str(best.z_ring),
            f"{best.i_real:.4f}",
        )
        for widget, text in zip(self.metric_values, values):
            widget.configure(text=text)

        for widget, text in zip(
            self.metric_captions,
            (
                "",
                "",
                "",
                tr(
                    self.language,
                    "ui.caption.deviation",
                    value=f"{best.ratio_deviation:+.2%}",
                ),
            ),
        ):
            widget.configure(text=text)

        self.diameters_label.configure(
            text=tr(
                self.language,
                "ui.diameters",
                d_sun=best.d_sun,
                d_planet=best.d_planet,
                d_ring=best.d_ring,
                d_carrier=best.d_carrier,
                d_ext=best.d_ext,
            )
        )

        usage = min(best.d_ext / result.d_max, 1.0) if result.d_max else 0.0
        self.envelope_bar.configure(value=usage * 100.0)
        self.envelope_label.configure(
            text=tr(
                self.language,
                "ui.envelope",
                used=best.d_ext,
                total=result.d_max,
                percent=usage,
                free=result.d_max - best.d_ext,
            )
        )

        self._render_checks(best)
        self._render_alternatives(result)

    def _render_kinematics(self, solution: gb.Solution) -> None:
        """Name the driver, the driven member and the fixed one, and the sense."""
        config = solution.configuration
        driver = tr(self.language, f"element.{config.driver}").capitalize()
        driven = tr(self.language, f"element.{config.driven}")
        fixed = tr(self.language, f"element.{config.fixed}")
        ratio = solution.i_real

        key = "ui.kinematics.reduction" if config.reduction else "ui.kinematics.overdrive"
        self.kinematics_label.configure(
            text=tr(
                self.language,
                key,
                driver=driver,
                driven=driven,
                fixed=fixed,
                ratio=ratio,
                speed=1.0 / ratio if ratio else 0.0,
            ),
            foreground=ACCENT,
        )

    def _render_infeasible(self, result: gb.SolveResult) -> None:
        driver, driven, fixed = self._configuration_names()
        self.kinematics_label.configure(
            text=tr(
                self.language,
                "ui.kinematics.invalid",
                driver=driver,
                driven=driven,
                fixed=fixed,
            ),
            foreground=MUTED,
        )
        self.message_label.configure(text=result.message, style="Fail.TLabel")
        for value, caption in zip(self.metric_values, self.metric_captions):
            value.configure(text="—")
            caption.configure(text="")
        self.report_card.grid_remove()
        self.diameters_label.configure(text="")
        self.envelope_bar.configure(value=0.0)
        self.envelope_label.configure(text="")
        self.alternatives_tree.delete(*self.alternatives_tree.get_children())
        self.alternatives_tree.insert(
            "",
            "end",
            values=(
                "—",
                "",
                "",
                "",
                "",
                "",
                tr(self.language, "ui.status.no_alternative"),
            ),
        )

        text = self.checks_text
        text.configure(state="normal")
        text.delete("1.0", "end")
        text.insert("end", f"{tr(self.language, 'ui.diag.binding')}\n\n", "heading")
        text.insert("end", f"{result.diagnosis}\n\n", "muted")
        text.insert("end", f"{tr(self.language, 'ui.diag.change')}\n\n", "heading")
        for suggestion in result.suggestions:
            text.insert("end", f"•  {suggestion}\n\n", "muted")
        text.configure(state="disabled")

    def _render_checks(self, solution: gb.Solution) -> None:
        text = self.checks_text
        text.configure(state="normal")
        text.delete("1.0", "end")

        for check in solution.checks:
            status_tag = "pass" if check.passed else "fail"
            status_text = "PASS" if check.passed else "FAIL"
            text.insert("end", f"{status_text:4s}  ", status_tag)
            text.insert("end", f"{check.label}\n", "name")
            text.insert("end", f"      {check.expression}\n", "mono")
            text.insert("end", f"      {check.detail}\n", "muted")
            if not check.passed:
                text.insert(
                    "end",
                    f"      {tr(self.language, 'ui.check.fix', hint=check.hint)}\n",
                    "fail",
                )
            text.insert("end", "\n")

        text.configure(state="disabled")

    def _write_error(self, message: str) -> None:
        text = self.checks_text
        text.configure(state="normal")
        text.delete("1.0", "end")
        text.insert("end", message, "error")
        text.configure(state="disabled")

    def _render_alternatives(self, result: gb.SolveResult) -> None:
        self.alternatives_tree.delete(*self.alternatives_tree.get_children())
        for solution in result.alternatives:
            status = (
                tr(self.language, "ui.status.pass_all")
                if solution.valid
                else solution.failed_checks[0].label
            )
            self.alternatives_tree.insert(
                "",
                "end",
                values=(
                    solution.z_sun,
                    solution.z_planet,
                    solution.z_ring,
                    f"{solution.i_real:.4f}",
                    f"{solution.ratio_deviation:.2%}",
                    f"{solution.d_ext:.1f}",
                    status,
                ),
            )
        if not result.alternatives:
            self.alternatives_tree.insert(
                "",
                "end",
                values=(
                    "—",
                    "",
                    "",
                    "",
                    "",
                    "",
                    tr(self.language, "ui.status.no_alternative"),
                ),
            )

    # -- schematic -----------------------------------------------------------

    def _on_canvas_resize(self, event=None) -> None:  # noqa: ARG002
        self._draw()

    def _legend_entries(
        self, solution: gb.Solution, d_max: float
    ) -> list[tuple[str, str]]:
        config = solution.configuration

        def role(element: str) -> str:
            if element == config.driver:
                return tr(self.language, "role.driver")
            if element == config.driven:
                return tr(self.language, "role.driven")
            if element == config.fixed:
                return tr(self.language, "role.fixed")
            return tr(self.language, "role.idle")

        def suffix(element: str) -> str:
            return tr(self.language, "ui.legend.role", role=role(element))

        return [
            (
                COLOR_SUN,
                tr(
                    self.language,
                    "ui.legend.sun",
                    name=tr(self.language, "element.sun").capitalize(),
                    teeth=solution.z_sun,
                    diameter=solution.d_sun,
                    role=suffix("sun"),
                ),
            ),
            (
                COLOR_PLANET,
                tr(
                    self.language,
                    "ui.legend.planet",
                    name=tr(self.language, "element.planets").capitalize(),
                    teeth=solution.z_planet,
                    diameter=solution.d_planet,
                    role=suffix("planets"),
                ),
            ),
            (
                COLOR_RING,
                tr(
                    self.language,
                    "ui.legend.ring",
                    name=tr(self.language, "element.ring").capitalize(),
                    teeth=solution.z_ring,
                    diameter=solution.d_ring,
                    role=suffix("ring"),
                ),
            ),
            (
                COLOR_ENVELOPE,
                tr(self.language, "ui.legend.envelope", d_max=d_max),
            ),
        ]

    def _layout_legend(
        self, entries: list[tuple[str, str]], width: float, measure
    ) -> list[list[tuple[str, str, float]]]:
        """Split the legend into rows that fit the canvas width."""
        swatch = 10
        gap = 16
        rows: list[list[tuple[str, str, float]]] = []
        current: list[tuple[str, str, float]] = []
        used = 0.0

        for color, text in entries:
            entry_width = swatch + 5 + measure(text)
            extra = entry_width + (gap if current else 0.0)
            if current and used + extra > width - 12:
                rows.append(current)
                current, used = [], 0.0
                extra = entry_width
            current.append((color, text, entry_width))
            used += extra

        if current:
            rows.append(current)
        return rows

    def _draw(self) -> None:
        canvas = self.canvas
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 60 or height < 60:
            return

        solution = self._solution
        if solution is None:
            canvas.create_text(
                width / 2,
                height / 2,
                text=tr(self.language, "ui.schematic.empty"),
                fill=MUTED,
                font=FONT_BASE,
            )
            return

        d_max = self._result.d_max if self._result else 0.0
        measure = tkinter_font.Font(font=FONT_SMALL).measure
        legend = self._layout_legend(
            self._legend_entries(solution, d_max), width, measure
        )
        band = 6 + len(legend) * LEGEND_ROW_HEIGHT

        outer_diameter = max(solution.d_ext, d_max)
        margin = 12.0
        drawing_height = max(height - band, 40.0)
        scale = (min(width, drawing_height) / 2.0 - margin) / (outer_diameter / 2.0)
        cx, cy = width / 2.0, drawing_height / 2.0

        def circle(radius_mm: float, **options) -> None:
            radius = radius_mm * scale
            canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius, **options
            )

        # The envelope, then the ring (solid when it is the fixed member).
        if d_max:
            circle(d_max / 2.0, outline=COLOR_ENVELOPE, dash=(5, 4), width=1)
        circle(solution.d_ext / 2.0, outline=COLOR_RING, width=2)
        circle(solution.d_ring / 2.0, outline=COLOR_RING, dash=(4, 3), width=1)
        circle(solution.d_carrier / 2.0, outline=GRID, dash=(1, 3), width=1)

        config = solution.configuration
        if config.fixed == "ring":
            self._draw_ground_ticks(canvas, cx, cy, solution.d_ext / 2.0 * scale)
        elif config.fixed == "sun":
            self._draw_ground_ticks(canvas, cx, cy, solution.d_sun / 2.0 * scale, count=14)

        carrier_radius = solution.d_carrier / 2.0
        planet_radius = solution.d_planet / 2.0
        for index in range(solution.n_planets):
            angle = 2.0 * math.pi * index / solution.n_planets
            px = cx + carrier_radius * scale * math.cos(angle)
            py = cy + carrier_radius * scale * math.sin(angle)
            canvas.create_line(cx, cy, px, py, fill=GRID, dash=(2, 3))
            r = planet_radius * scale
            canvas.create_oval(
                px - r,
                py - r,
                px + r,
                py + r,
                fill=COLOR_PLANET,
                outline=COLOR_PLANET_EDGE,
            )

        sun_radius = solution.d_sun / 2.0 * scale
        canvas.create_oval(
            cx - sun_radius,
            cy - sun_radius,
            cx + sun_radius,
            cy + sun_radius,
            fill=COLOR_SUN,
            outline=COLOR_SUN_EDGE,
            width=2 if config.fixed == "sun" else 1,
        )

        self._draw_legend(canvas, legend, width, height)

    def _draw_ground_ticks(
        self, canvas: tk.Canvas, cx: float, cy: float, radius: float, count: int = 36
    ) -> None:
        """Hatch marks around the fixed member: the usual 'grounded' symbol."""
        for index in range(count):
            angle = 2.0 * math.pi * index / count
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            inner = radius + 2.0
            outer = radius + 7.0
            canvas.create_line(
                cx + inner * cos_a,
                cy + inner * sin_a,
                cx + outer * cos_a,
                cy + outer * sin_a,
                fill=COLOR_RING,
                width=1,
            )

    def _draw_legend(
        self,
        canvas: tk.Canvas,
        rows: list[list[tuple[str, str, float]]],
        width: float,
        height: float,
    ) -> None:
        """Draw the prepared legend rows along the bottom edge."""
        gap = 16
        swatch = 10
        first_row_y = height - 6 - (len(rows) - 1) * LEGEND_ROW_HEIGHT - LEGEND_ROW_HEIGHT / 2

        for row_index, row in enumerate(rows):
            total = sum(entry_width for _, _, entry_width in row) + gap * (len(row) - 1)
            x = max(6.0, (width - total) / 2.0)
            y = first_row_y + row_index * LEGEND_ROW_HEIGHT

            for color, text, entry_width in row:
                canvas.create_rectangle(x, y - 4, x + swatch, y + 4, fill=color, outline="")
                canvas.create_text(
                    x + swatch + 5,
                    y,
                    text=text,
                    anchor="w",
                    fill=MUTED,
                    font=FONT_SMALL,
                )
                x += entry_width + gap


def _enable_dpi_awareness() -> None:
    """Let Windows give us real pixels instead of a 150 %-upscaled bitmap.

    An unaware process is rendered at the logical resolution and then stretched,
    which blurs every label and hands the layout a screen far smaller than the
    one the user actually has. Best effort: a system without the API keeps the
    default behaviour.
    """
    if not hasattr(ctypes, "windll"):  # not Windows
        return
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2, available since Windows 8.1.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def main() -> int:
    _enable_dpi_awareness()
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"Tkinter could not start: {error}", flush=True)
        return 1

    try:
        PlanetaryCalculatorApp(root)
    except Exception as error:  # pragma: no cover - last-resort guard
        messagebox.showerror("Planetary gearbox calculator", f"Startup failed:\n{error}")
        return 1

    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
