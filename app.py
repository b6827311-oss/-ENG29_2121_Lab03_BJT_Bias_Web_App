from flask import Flask, render_template, request

from dc_bias import (
    calculate_dc_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
)

app = Flask(__name__)


class FormError(ValueError):
    """Raised when the submitted form cannot be mapped to a bias model."""


# Field metadata shared by the form and the validation messages.
FIELD_META = {
    "vcc": {"label": "VCC", "hint": "Supply Voltage [V]"},
    "r1": {"label": "R1", "hint": "Upper Divider [kΩ]"},
    "r2": {"label": "R2", "hint": "Lower Divider [kΩ]"},
    "rb": {"label": "RB", "hint": "Base Resistor [kΩ]"},
    "rc": {"label": "RC", "hint": "Collector Resistor [kΩ]"},
    "re": {"label": "RE", "hint": "Emitter Resistor [kΩ]"},
    "beta": {"label": "β", "hint": "Current Gain [–]"},
    "vbe": {"label": "VBE", "hint": "Base-Emitter Voltage [V]"},
}

MODE_OPTIONS = [
    ("divider", "Voltage Divider Bias"),
    ("fixed", "Fixed Bias"),
    ("emitter", "Emitter Bias"),
]

MODES = {
    "divider": {
        "label": "Voltage Divider Bias",
        "note": "R1 จาก VCC ไป Base · R2 จาก Base ลงกราวด์ · RE จาก Emitter ลงกราวด์",
        "fields": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
        "resistors": ("r1", "r2", "rc", "re"),
        "defaults": {
            "vcc": "12",
            "r1": "100",
            "r2": "22",
            "rc": "2.2",
            "re": "1",
            "beta": "100",
            "vbe": "0.70",
        },
        "calculator": calculate_dc_bias,
    },
    "fixed": {
        "label": "Fixed Bias",
        "note": "RB จาก VCC ไป Base · Emitter ต่อลงกราวด์โดยตรง (VE = 0 V)",
        "fields": ("vcc", "rb", "rc", "beta", "vbe"),
        "resistors": ("rb", "rc"),
        "defaults": {
            "vcc": "12",
            "rb": "1000",
            "rc": "2.2",
            "beta": "100",
            "vbe": "0.70",
        },
        "calculator": calculate_fixed_bias,
    },
    "emitter": {
        "label": "Emitter Bias",
        "note": "RB จาก VCC ไป Base · RE จาก Emitter ลงกราวด์",
        "fields": ("vcc", "rb", "rc", "re", "beta", "vbe"),
        "resistors": ("rb", "rc", "re"),
        "defaults": {
            "vcc": "12",
            "rb": "1000",
            "rc": "2.2",
            "re": "1",
            "beta": "100",
            "vbe": "0.70",
        },
        "calculator": calculate_emitter_bias,
    },
}

DEFAULT_MODE = "divider"

WARNING_MESSAGES = {
    "cutoff": "Cutoff: IB ≤ 0 — Forward-Active approximation ใช้ไม่ได้",
    "near_saturation": "Near Saturation: VCE ≤ 0.2 V — ผลอาจไม่แม่นยำ",
}


def _requested_mode(raw_mode):
    """Map the submitted mode to a known model.

    An empty value means the Lab 02 form (no mode field), which is still the
    voltage-divider circuit. Any other unknown value is an error: guessing
    Divider here would hide a broken form.
    """
    mode = (raw_mode or "").strip()
    if not mode:
        return DEFAULT_MODE
    if mode not in MODES:
        raise FormError(
            f"ไม่รู้จักโหมดวงจรที่เลือก ({mode}) — "
            "กรุณาเลือก Voltage Divider, Fixed หรือ Emitter"
        )
    return mode


def _mode_fields(mode, values):
    return [
        {
            "name": name,
            "label": FIELD_META[name]["label"],
            "hint": FIELD_META[name]["hint"],
            "value": values.get(name, ""),
        }
        for name in MODES[mode]["fields"]
    ]


def _float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _render(mode, values, result=None, error=None, warning_messages=None):
    return render_template(
        "index.html",
        mode=mode,
        modes=MODE_OPTIONS,
        mode_label=MODES[mode]["label"] if mode else None,
        mode_note=MODES[mode]["note"] if mode else None,
        fields=_mode_fields(mode, values) if mode else [],
        values=values,
        result=result,
        error=error,
        warning_messages=warning_messages or [],
        vbe=_float_or_none(values.get("vbe")),
    )


def _read_known_fields(mode):
    return {
        name: request.form.get(name, "").strip()
        for name in MODES[mode]["fields"]
    }


def _parse_inputs(mode, values):
    """Convert the form strings to SI units (kΩ -> Ω happens only here)."""
    config = MODES[mode]
    parsed = {}
    for name in config["fields"]:
        try:
            value = float(values[name])
        except ValueError:
            raise FormError("กรุณากรอกค่าตัวเลขให้ครบทุกช่อง") from None
        if name in config["resistors"]:
            value *= 1000  # form unit is kΩ, the engineering core uses Ω
        parsed[name] = value
    return parsed


@app.get("/")
def index():
    values = {}
    error = None
    try:
        mode = _requested_mode(request.args.get("mode"))
    except FormError as exc:
        return _render(None, values, error=str(exc))

    # Keep values the user already typed when switching mode.
    for name in MODES[mode]["fields"]:
        values[name] = (
            request.args.get(name, "").strip() or MODES[mode]["defaults"][name]
        )
    return _render(mode, values)


@app.post("/calculate")
def calculate():
    try:
        mode = _requested_mode(request.form.get("mode"))
    except FormError as exc:
        return _render(None, {}, error=str(exc))

    values = _read_known_fields(mode)

    try:
        parsed = _parse_inputs(mode, values)
    except FormError as exc:
        return _render(mode, values, error=str(exc))

    try:
        result = MODES[mode]["calculator"](**parsed)
    except ValueError as exc:
        return _render(mode, values, error=str(exc))

    warning_messages = [WARNING_MESSAGES[code] for code in result["warnings"]]
    return _render(
        mode,
        values,
        result=result,
        warning_messages=warning_messages,
    )


if __name__ == "__main__":
    app.run(debug=True)
