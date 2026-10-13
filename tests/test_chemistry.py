"""Reference-value and error-path checks for physicochemical screening."""
import math
import pytest
from solubility_mind.chemistry import calculate


def test_neutral_solubility_and_dose_number():
    data = calculate(0.5, 100, permeability="high")
    assert data["dose_number"] == pytest.approx(0.8)
    assert data["minimum_solubility_mg_ml"] == 0.5
    assert data["bcs_screen"] == "I"
    assert [p["ph"] for p in data["ph_profile"]] == [1.2, 4.5, 6.8]


def test_weak_acid_and_base_profile():
    a = calculate(0.01, 10, ionization="acid", pka=4.5, permeability="low")
    assert a["ph_profile"][1]["solubility_mg_ml"] == pytest.approx(0.02)
    assert a["dose_number"] > 1
    assert a["bcs_screen"] == "IV"
    b = calculate(0.01, 10, ionization="base", pka=4.5)
    assert b["ph_profile"][0]["solubility_mg_ml"] > b["ph_profile"][2]["solubility_mg_ml"]
    assert b["bcs_screen"] is None


def test_partition_and_noyes_whitney():
    result = calculate(2.0, 100,
                       octanol_concentration_mg_ml=10,
                       water_concentration_mg_ml=1,
                       diffusion_cm2_s=1e-5,
                       surface_area_cm2=10,
                       diffusion_layer_cm=0.01,
                       bulk_concentration_mg_ml=0.5,
                       saturation_concentration_mg_ml=2.0)
    assert result["log_kow"] == pytest.approx(1)
    assert result["dissolution_rate_mg_s"] == pytest.approx(0.015)


@pytest.mark.parametrize("kwargs", [
    {"intrinsic_solubility_mg_ml": 0, "dose_mg": 10},
    {"intrinsic_solubility_mg_ml": 1, "dose_mg": float("nan")},
    {"intrinsic_solubility_mg_ml": 1, "dose_mg": float("inf")},
    {"intrinsic_solubility_mg_ml": 1, "dose_mg": True},
    {"intrinsic_solubility_mg_ml": 1, "dose_mg": 2, "ionization": "acid"},
    {"intrinsic_solubility_mg_ml": 1, "dose_mg": 2, "permeability": "guessed"},
    {"intrinsic_solubility_mg_ml": 1, "dose_mg": 2, "octanol_concentration_mg_ml": 1},
    {"intrinsic_solubility_mg_ml": 1, "dose_mg": 2, "diffusion_cm2_s": 1},
    {"intrinsic_solubility_mg_ml": 1, "dose_mg": 2, "ionization": "base", "pka": -100},
])
def test_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        calculate(**kwargs)


def test_extreme_numeric_inputs_are_not_silently_serialized_as_infinity():
    with pytest.raises(ValueError, match="Dose number"):
        calculate(1e-300, 1e300)
    r = calculate(0.5, 100, octanol_concentration_mg_ml=1e300,
                  water_concentration_mg_ml=1e-300)
    assert math.isfinite(r["log_kow"])
    assert r["log_kow"] == pytest.approx(600)
