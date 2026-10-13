"""Validation for the optional server-side version of the physicochemical screen."""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ChemistryRequest(BaseModel):
    intrinsic_solubility_mg_ml: float = Field(gt=0, allow_inf_nan=False)
    dose_mg: float = Field(gt=0, allow_inf_nan=False)
    ionization: Literal["neutral", "acid", "base"] = "neutral"
    pka: Optional[float] = Field(default=None, allow_inf_nan=False)
    permeability: Literal["unknown", "high", "low"] = "unknown"
    octanol_concentration_mg_ml: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    water_concentration_mg_ml: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    diffusion_cm2_s: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    surface_area_cm2: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    diffusion_layer_cm: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    bulk_concentration_mg_ml: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    saturation_concentration_mg_ml: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
