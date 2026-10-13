from agents.chemistry_api import ChemistryRequest
from agents.api import chemistry_analysis
from pydantic import ValidationError
import pytest


def test_chemistry_endpoint_logic():
    model = ChemistryRequest(intrinsic_solubility_mg_ml=0.5, dose_mg=100)
    result = chemistry_analysis(model)
    assert result["dose_number"] == pytest.approx(0.8)
    assert result["bcs_screen"] is None


def test_chemistry_endpoint_rejects_nonfinite():
    with pytest.raises(ValidationError):
        ChemistryRequest(intrinsic_solubility_mg_ml=float("nan"), dose_mg=100)
