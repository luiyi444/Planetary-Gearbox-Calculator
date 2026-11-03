"""Translations for the planetary gearbox calculator.

Both the calculation core and the desktop interface take every user-facing
sentence from here, so one language setting switches the whole application.
Keys are stable identifiers; the English text is the reference and Spanish is a
translation of it, never a rewrite of the engineering content.
"""

from __future__ import annotations

LANGUAGES: tuple[str, ...] = ("en", "es")
"""Languages offered by the interface, in display order."""

DEFAULT_LANGUAGE: str = "es"
"""Language the desktop app starts in."""

FALLBACK_LANGUAGE: str = "en"
"""Language used when a caller passes a code we do not support.

It is the language every entry of `MESSAGES` is written in first, so an unknown
code degrades to the reference wording instead of silently switching the caller
into a different language than the one it asked for. The app's start-up
language is `DEFAULT_LANGUAGE`, which is a separate decision.
"""

MESSAGES: dict[str, dict[str, str]] = {
    # --- application shell --------------------------------------------------
    "ui.window.title": {
        "en": "Planetary gearbox calculator",
        "es": "Calculadora de tren planetario",
    },
    "ui.header.title": {
        "en": "Planetary gearbox calculator",
        "es": "Calculadora de tren planetario",
    },
    "ui.header.subtitle": {
        "en": "Single stage · ring, sun, planets and carrier",
        "es": "Una etapa · corona, solar, satélites y portasatélites",
    },
    "ui.language": {"en": "Language", "es": "Idioma"},
    # --- sections and fields ------------------------------------------------
    "ui.section.inputs": {"en": " Inputs ", "es": " Entradas "},
    "ui.section.advanced": {"en": " Advanced ", "es": " Avanzado "},
    "ui.section.verification": {"en": " Verification ", "es": " Verificación "},
    "ui.section.schematic": {"en": " Schematic ", "es": " Esquema "},
    "ui.section.alternatives": {
        "en": " Alternative designs ",
        "es": " Diseños alternativos ",
    },
    "ui.field.module": {"en": "Module m (mm)", "es": "Módulo m (mm)"},
    "ui.field.planets": {"en": "Planets N", "es": "Satélites N"},
    "ui.field.configuration": {"en": "Configuration", "es": "Configuración"},
    "ui.field.ratio": {"en": "Ratio i", "es": "Relación i"},
    "ui.field.d_max": {"en": "D max (mm)", "es": "D máx (mm)"},
    "ui.field.tolerance": {"en": "Ratio tol. (%)", "es": "Tol. relación (%)"},
    "ui.field.alternatives": {"en": "Alternatives", "es": "Alternativas"},
    "ui.hint.ratio": {
        "en": "i = ω driver / ω driven",
        "es": "i = ω motriz / ω conducido",
    },
    # --- result readout -----------------------------------------------------
    "ui.caption.zs": {"en": "Sun teeth Zs", "es": "Dientes del solar Zs"},
    "ui.caption.zp": {"en": "Planet teeth Zp", "es": "Dientes del satélite Zp"},
    "ui.caption.zr": {"en": "Ring teeth Zr", "es": "Dientes de corona Zr"},
    "ui.caption.i_real": {"en": "Real ratio i_real", "es": "Relación real i_real"},
    "ui.caption.deviation": {
        "en": "{value} deviation",
        "es": "{value} de desviación",
    },
    "ui.diameters": {
        "en": (
            "Pitch diameters   sun {d_sun:.2f} mm  ·  planet {d_planet:.2f} mm  ·  "
            "ring {d_ring:.2f} mm\ncarrier {d_carrier:.2f} mm  ·  "
            "ring outside {d_ext:.2f} mm"
        ),
        "es": (
            "Diámetros primitivos   solar {d_sun:.2f} mm  ·  satélite "
            "{d_planet:.2f} mm  ·  corona {d_ring:.2f} mm\nportasatélites "
            "{d_carrier:.2f} mm  ·  exterior de corona {d_ext:.2f} mm"
        ),
    },
    "ui.envelope": {
        "en": "Envelope used: {used:.1f} of {total:.1f} mm ({percent:.0%})  ·  {free:.1f} mm free",
        "es": (
            "Envolvente usada: {used:.1f} de {total:.1f} mm ({percent:.0%})  ·  "
            "{free:.1f} mm libres"
        ),
    },
    "ui.kinematics.reduction": {
        "en": (
            "{driver} is the driver, {driven} the driven member, {fixed} stays fixed.\n"
            "i = {ratio:.3f}: the driver turns {ratio:.2f} times per turn of the "
            "driven shaft (reduction)."
        ),
        "es": (
            "{driver} es el elemento motriz, {driven} el conducido y {fixed} queda fijo.\n"
            "i = {ratio:.3f}: el motriz da {ratio:.2f} vueltas por cada vuelta del "
            "conducido (reducción)."
        ),
    },
    "ui.kinematics.overdrive": {
        "en": (
            "{driver} is the driver, {driven} the driven member, {fixed} stays fixed.\n"
            "i = {ratio:.3f}: the driver turns {ratio:.3f} times per turn of the "
            "driven shaft, so the driven runs {speed:.2f} times faster (speed increase)."
        ),
        "es": (
            "{driver} es el elemento motriz, {driven} el conducido y {fixed} queda fijo.\n"
            "i = {ratio:.3f}: el motriz da {ratio:.3f} vueltas por cada vuelta del "
            "conducido, es decir, el conducido gira {speed:.2f} veces más rápido "
            "(multiplicación)."
        ),
    },
    "ui.kinematics.invalid": {
        "en": "Configuration: {driver} drives, {driven} is driven, {fixed} fixed.",
        "es": "Configuración: {driver} motriz, {driven} conducido, {fixed} fijo.",
    },
    # --- table --------------------------------------------------------------
    "ui.table.zs": {"en": "Zs", "es": "Zs"},
    "ui.table.zp": {"en": "Zp", "es": "Zp"},
    "ui.table.zr": {"en": "Zr", "es": "Zr"},
    "ui.table.i_real": {"en": "i_real", "es": "i_real"},
    "ui.table.deviation": {"en": "Deviation", "es": "Desviación"},
    "ui.table.d_ext": {"en": "D_ext (mm)", "es": "D_ext (mm)"},
    "ui.table.status": {"en": "Status", "es": "Estado"},
    "ui.status.pass_all": {
        "en": "all conditions pass",
        "es": "todas las condiciones se cumplen",
    },
    "ui.status.no_alternative": {"en": "no other design", "es": "no hay otro diseño"},
    # --- schematic ----------------------------------------------------------
    "ui.schematic.empty": {
        "en": "No feasible train to draw",
        "es": "No hay un tren válido que dibujar",
    },
    "ui.legend.sun": {
        "en": "{name} Zs={teeth}  Ø{diameter:.1f} mm{role}",
        "es": "{name} Zs={teeth}  Ø{diameter:.1f} mm{role}",
    },
    "ui.legend.planet": {
        "en": "{name} Zp={teeth}  Ø{diameter:.1f} mm{role}",
        "es": "{name} Zp={teeth}  Ø{diameter:.1f} mm{role}",
    },
    "ui.legend.ring": {
        "en": "{name} Zr={teeth}  Ø{diameter:.1f} mm{role}",
        "es": "{name} Zr={teeth}  Ø{diameter:.1f} mm{role}",
    },
    "ui.legend.envelope": {
        "en": "envelope D_max={d_max:g} mm",
        "es": "envolvente D_máx={d_max:g} mm",
    },
    "ui.legend.role": {"en": "  ·  {role}", "es": "  ·  {role}"},
    # --- input errors shown by the interface --------------------------------
    "ui.error.fields": {
        "en": "Every field needs a number.",
        "es": "Todos los campos necesitan un número.",
    },
    "ui.diag.binding": {"en": "Binding constraint", "es": "Restricción activa"},
    "ui.diag.change": {"en": "What to change", "es": "Qué cambiar"},
    "ui.check.fix": {"en": "Fix: {hint}", "es": "Solución: {hint}"},
    # --- elements, roles, configurations ------------------------------------
    "element.sun": {"en": "sun", "es": "solar"},
    "element.planets": {"en": "planets", "es": "satélites"},
    "element.carrier": {"en": "carrier", "es": "portasatélites"},
    "element.ring": {"en": "ring", "es": "corona"},
    "role.driver": {"en": "driver", "es": "motriz"},
    "role.driven": {"en": "driven", "es": "conducido"},
    "role.fixed": {"en": "fixed", "es": "fijo"},
    "role.idle": {"en": "idle", "es": "loco"},
    "config.ring_fixed_sun_drive.label": {
        "en": "Ring fixed · sun drives · carrier driven",
        "es": "Corona fija · solar motriz · portasatélites conducido",
    },
    "config.ring_fixed_carrier_drive.label": {
        "en": "Ring fixed · carrier drives · sun driven",
        "es": "Corona fija · portasatélites motriz · solar conducido",
    },
    "config.sun_fixed_carrier_drive.label": {
        "en": "Sun fixed · carrier drives · ring driven",
        "es": "Solar fijo · portasatélites motriz · corona conducida",
    },
    "config.sun_fixed_ring_drive.label": {
        "en": "Sun fixed · ring drives · carrier driven",
        "es": "Solar fijo · corona motriz · portasatélites conducido",
    },
    "config.ring_fixed_sun_drive.formula": {"en": "i = 1 + Zr/Zs", "es": "i = 1 + Zr/Zs"},
    "config.ring_fixed_carrier_drive.formula": {
        "en": "i = Zs/(Zs + Zr)",
        "es": "i = Zs/(Zs + Zr)",
    },
    "config.sun_fixed_carrier_drive.formula": {
        "en": "i = 1 + Zs/Zr",
        "es": "i = 1 + Zs/Zr",
    },
    "config.sun_fixed_ring_drive.formula": {
        "en": "i = Zr/(Zs + Zr)",
        "es": "i = Zr/(Zs + Zr)",
    },
    # --- core: validation ---------------------------------------------------
    "core.error.module": {
        "en": "The module m must be a positive number of millimetres.",
        "es": "El módulo m debe ser un número positivo en milímetros.",
    },
    "core.error.planets": {
        "en": "The number of planets N must be an integer of at least 2.",
        "es": "El número de satélites N debe ser un entero de al menos 2.",
    },
    "core.error.d_max": {
        "en": "The maximum diameter D_max must be a positive length.",
        "es": "El diámetro máximo D_máx debe ser una longitud positiva.",
    },
    "core.error.max_alternatives": {
        "en": "max_alternatives must be zero or greater.",
        "es": "max_alternatives debe ser cero o mayor.",
    },
    "core.error.tolerance": {
        "en": "tolerance must be zero or greater.",
        "es": "la tolerancia debe ser cero o mayor.",
    },
    "core.error.ratio.reduction": {
        "en": (
            "With {configuration} the ratio is {formula}, so i must be greater "
            "than 1. For the inverse (i < 1) pick the configuration where the "
            "driver and the driven member are swapped: i = {reciprocal:.4g}."
        ),
        "es": (
            "Con «{configuration}» la relación es {formula}, así que i debe ser "
            "mayor que 1. Para la inversa (i < 1) elige la configuración con "
            "motriz y conducido intercambiados: i = {reciprocal:.4g}."
        ),
    },
    "core.error.ratio.overdrive": {
        "en": (
            "With {configuration} the ratio is {formula}, so i must be smaller "
            "than 1 (a speed increase). For the inverse (i > 1) pick the "
            "configuration where the driver and the driven member are swapped: "
            "i = {reciprocal:.4g}."
        ),
        "es": (
            "Con «{configuration}» la relación es {formula}, así que i debe ser "
            "menor que 1 (multiplicación). Para la inversa (i > 1) elige la "
            "configuración con motriz y conducido intercambiados: i = {reciprocal:.4g}."
        ),
    },
    # --- core: design conditions -------------------------------------------
    "core.check.concentricity.label": {
        "en": "Concentricity (coaxial mounting)",
        "es": "Concentricidad (montaje coaxial)",
    },
    "core.check.concentricity.hint": {
        "en": (
            "Zp is derived from Zr and Zs, so this only fails when the planet "
            "count is not an integer."
        ),
        "es": (
            "Zp se deduce de Zr y Zs, así que solo falla cuando el número de "
            "satélites no es entero."
        ),
    },
    "core.check.assembly.label": {
        "en": "Assembly of equally spaced planets",
        "es": "Montaje de satélites equidistantes",
    },
    "core.check.assembly.hint": {
        "en": (
            "Zr is incremented until the planets can be inserted, so this fails "
            "only when no aligned tooth count fits inside D_max."
        ),
        "es": (
            "Zr se incrementa hasta que los satélites pueden insertarse, así que "
            "solo falla si ningún número de dientes alineado cabe en D_máx."
        ),
    },
    "core.check.adjacency.label": {
        "en": "Adjacency (planets do not touch)",
        "es": "Adyacencia (los satélites no se tocan)",
    },
    "core.check.adjacency.hint": {
        "en": (
            "Reduce N, reduce the module, or lower the ratio: with more planets "
            "the same tooth counts leave no room between them."
        ),
        "es": (
            "Reduce N, reduce el módulo o baja la relación: con más satélites los "
            "mismos dientes no dejan sitio entre ellos."
        ),
    },
    "core.check.envelope.label": {
        "en": "Diameter envelope",
        "es": "Envolvente de diámetro",
    },
    "core.check.envelope.hint": {
        "en": "Increase D_max or choose a smaller module.",
        "es": "Aumenta D_máx o elige un módulo menor.",
    },
    "core.check.min_teeth.label": {
        "en": "Minimum tooth count",
        "es": "Número mínimo de dientes",
    },
    "core.check.min_teeth.hint": {
        "en": (
            "Raise the ratio or the module so the sun and the planets can carry "
            "at least 17 teeth each."
        ),
        "es": (
            "Sube la relación o el módulo para que el solar y los satélites "
            "tengan al menos 17 dientes cada uno."
        ),
    },
    "core.check.ratio.label": {
        "en": "Ratio tolerance",
        "es": "Tolerancia de relación",
    },
    "core.check.ratio.hint": {
        "en": (
            "Tooth counts are integers, so the real ratio never matches exactly: "
            "accept a wider tolerance or a different module."
        ),
        "es": (
            "Los dientes son enteros, así que la relación real nunca coincide "
            "exactamente: acepta una tolerancia mayor o cambia el módulo."
        ),
    },
    # --- core: outcome messages ---------------------------------------------
    "core.message.solution": {
        "en": "Solution found: Zs={zs}, Zp={zp}, Zr={zr} (i_real={i:.3f}).",
        "es": "Solución encontrada: Zs={zs}, Zp={zp}, Zr={zr} (i_real={i:.3f}).",
    },
    "core.message.best_partial": {
        "en": (
            "Best achievable design: Zs={zs}, Zp={zp}, Zr={zr}. "
            "Still failing: {failed}."
        ),
        "es": (
            "Mejor diseño alcanzable: Zs={zs}, Zp={zp}, Zr={zr}. "
            "Todavía fallan: {failed}."
        ),
    },
    "core.message.no_solution": {
        "en": (
            "No valid train exists for these inputs: concentricity, planet "
            "assembly, planet adjacency and the diameter envelope cannot be "
            "satisfied at the same time."
        ),
        "es": (
            "No existe ningún tren válido para estas entradas: la "
            "concentricidad, el montaje de los satélites, su adyacencia y la "
            "envolvente de diámetro no pueden cumplirse a la vez."
        ),
    },
    # --- core: diagnosis and suggestions ------------------------------------
    "core.diag.ratio": {
        "en": (
            "No tooth combination reaches i={i:.2f} within {tol:.1%} with N={n} "
            "planets, at any size: the planet spacing and the minimum tooth "
            "count cap this ratio."
        ),
        "es": (
            "Ninguna combinación de dientes alcanza i={i:.2f} dentro del {tol:.1%} "
            "con N={n} satélites, sea cual sea el tamaño: la separación entre "
            "satélites y el mínimo de dientes limitan esa relación."
        ),
    },
    "core.diag.envelope": {
        "en": (
            "The binding constraint is the diameter envelope: the smallest valid "
            "train at this ratio measures {needed:.1f} mm outside, against the "
            "{d_max:.1f} mm allowed."
        ),
        "es": (
            "La restricción activa es la envolvente de diámetro: el tren válido "
            "más pequeño para esta relación mide {needed:.1f} mm por fuera, "
            "frente a los {d_max:.1f} mm disponibles."
        ),
    },
    "core.diag.generic": {
        "en": "The requested ratio is not reachable with these inputs.",
        "es": "La relación pedida no es alcanzable con estas entradas.",
    },
    "core.sugg.d_max": {
        "en": "Raise D_max to at least {needed:.1f} mm at m={module:g}.",
        "es": "Sube D_máx a al menos {needed:.1f} mm con m={module:g}.",
    },
    "core.sugg.module": {
        "en": (
            "Reduce the module to m={module:g}: Zs={zs}, Zp={zp}, Zr={zr}, "
            "i_real={i:.3f}, D_ext={d_ext:.1f} mm."
        ),
        "es": (
            "Reduce el módulo a m={module:g}: Zs={zs}, Zp={zp}, Zr={zr}, "
            "i_real={i:.3f}, D_ext={d_ext:.1f} mm."
        ),
    },
    "core.sugg.planets": {
        "en": (
            "Use N={n} planets instead of {old}: Zs={zs}, Zp={zp}, Zr={zr}, "
            "i_real={i:.3f}, D_ext={d_ext:.1f} mm."
        ),
        "es": (
            "Usa N={n} satélites en lugar de {old}: Zs={zs}, Zp={zp}, Zr={zr}, "
            "i_real={i:.3f}, D_ext={d_ext:.1f} mm."
        ),
    },
    "core.sugg.move_ratio": {
        "en": (
            "Move the requested ratio toward 1, to about {ratio:.2f}: Zs={zs}, "
            "Zp={zp}, Zr={zr}, i_real={i:.3f}, D_ext={d_ext:.1f} mm."
        ),
        "es": (
            "Acerca la relación pedida a 1, a unos {ratio:.2f}: Zs={zs}, "
            "Zp={zp}, Zr={zr}, i_real={i:.3f}, D_ext={d_ext:.1f} mm."
        ),
    },
    "core.sugg.relax": {
        "en": (
            "Relax at least one constraint: a larger D_max, a smaller module, "
            "fewer planets, or a different ratio."
        ),
        "es": (
            "Relaja al menos una restricción: mayor D_máx, módulo menor, menos "
            "satélites o una relación distinta."
        ),
    },
}


def normalize_language(value: str | None) -> str:
    """Return a supported language code, falling back to `FALLBACK_LANGUAGE`."""
    return value if value in LANGUAGES else FALLBACK_LANGUAGE


def app_language(value: str | None) -> str:
    """Language the interface should start in: the requested one, or the default.

    Separate from `normalize_language` because "the user asked for a language we
    do not have" and "the user did not pick a language yet" are different
    questions. The first falls back to the reference wording, the second to the
    interface default.
    """
    return normalize_language(value if value is not None else DEFAULT_LANGUAGE)


def language_name(value: str) -> str:
    """Short label for the language switcher (EN / ES)."""
    return normalize_language(value).upper()


def tr(language: str, key: str, **values: object) -> str:
    """Translate `key` into `language`, formatting the placeholders.

    A missing key is a programming error: it would silently show raw identifiers
    in the interface, so it raises instead of degrading.
    """
    try:
        entry = MESSAGES[key]
    except KeyError as error:  # pragma: no cover - guards typos during edits
        raise KeyError(f"unknown translation key: {key}") from error

    text = entry.get(normalize_language(language), entry["en"])
    return text.format(**values) if values else text
