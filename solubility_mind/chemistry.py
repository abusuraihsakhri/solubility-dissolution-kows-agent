"""Deterministic physicochemical *screening* calculations (not a BCS biowaiver determination)."""
import math
from typing import Optional


def _number(name: str, value, *, positive: bool = False, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if positive and value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def calculate(
    intrinsic_solubility_mg_ml: float,
    dose_mg: float,
    ionization: str = "neutral",
    pka: Optional[float] = None,
    permeability: str = "unknown",
    octanol_concentration_mg_ml: Optional[float] = None,
    water_concentration_mg_ml: Optional[float] = None,
    diffusion_cm2_s: Optional[float] = None,
    surface_area_cm2: Optional[float] = None,
    diffusion_layer_cm: Optional[float] = None,
    bulk_concentration_mg_ml: Optional[float] = None,
):
    """Calculate idealized Henderson–Hasselbalch, dose-number, partition and Noyes–Whitney quantities.

    pH profile is evaluated at 1.2, 4.5 and 6.8, for illustrative screening only.
    A regulatory BCS determination requires experimentally measured equilibrium solubility
    across relevant pHs at 37 ± 1 °C and justified human permeability evidence.
    """
    s0 = _number("intrinsic_solubility_mg_ml", intrinsic_solubility_mg_ml, positive=True)
    dose = _number("dose_mg", dose_mg, positive=True)
    if ionization not in ("neutral", "acid", "base"):
        raise ValueError("ionization must be neutral, acid, or base")
    if permeability not in ("unknown", "high", "low"):
        raise ValueError("permeability must be unknown, high, or low")
    if ionization != "neutral":
        if pka is None:
            raise ValueError("pka is required for a weak acid or base")
        pka = _number("pka", pka)
        if not -10 <= pka <= 20:
            raise ValueError("pka must be between -10 and 20")
    elif pka is not None:
        _number("pka", pka)

    profile = []
    for ph in (1.2, 4.5, 6.8):
        factor = (1 + 10 ** (ph - pka)) if ionization == "acid" else (
            (1 + 10 ** (pka - ph)) if ionization == "base" else 1
        )
        s = s0 * factor
        if not math.isfinite(s) or s <= 0:
            raise ValueError("Predicted solubility is outside the numeric range")
        profile.append({"ph": ph, "solubility_mg_ml": s})
    minimum_s = min(x["solubility_mg_ml"] for x in profile)
    dose_number = dose / (250 * minimum_s)
    high_solubility = dose_number <= 1
    bcs = None
    if permeability != "unknown":
        bcs = ({True: "I", False: "II"} if permeability == "high" else
               {True: "III", False: "IV"})[high_solubility]

    optional_partition = (octanol_concentration_mg_ml, water_concentration_mg_ml)
    if any(x is not None for x in optional_partition) and not all(x is not None for x in optional_partition):
        raise ValueError("Both octanol and water concentrations are required for log Kow")
    log_kow = None
    if all(x is not None for x in optional_partition):
        co = _number("octanol_concentration_mg_ml", optional_partition[0], positive=True)
        cw = _number("water_concentration_mg_ml", optional_partition[1], positive=True)
        log_kow = math.log10(co / cw)

    optional_dissolution = (diffusion_cm2_s, surface_area_cm2, diffusion_layer_cm,
                            bulk_concentration_mg_ml)
    if any(x is not None for x in optional_dissolution) and not all(x is not None for x in optional_dissolution):
        raise ValueError("Dissolution rate requires D, area, layer thickness, and bulk concentration")
    dissolution_rate = None
    if all(x is not None for x in optional_dissolution):
        d = _number("diffusion_cm2_s", diffusion_cm2_s, nonnegative=True)
        area = _number("surface_area_cm2", surface_area_cm2, positive=True)
        h = _number("diffusion_layer_cm", diffusion_layer_cm, positive=True)
        cb = _number("bulk_concentration_mg_ml", bulk_concentration_mg_ml, nonnegative=True)
        # 1 mL = 1 cm^3; this rate has units mg/s.
        dissolution_rate = d * area / h * (minimum_s - cb)
        if not math.isfinite(dissolution_rate):
            raise ValueError("Dissolution rate is outside the numeric range")

    return {
        "ph_profile": profile,
        "minimum_solubility_mg_ml": minimum_s,
        "dose_number": dose_number,
        "solubility_screen": "high" if high_solubility else "low",
        "bcs_screen": bcs,
        "log_kow": log_kow,
        "dissolution_rate_mg_s": dissolution_rate,
        "interpretation": "Model-based screening only; not a validated BCS classification or biowaiver assessment.",
    }
