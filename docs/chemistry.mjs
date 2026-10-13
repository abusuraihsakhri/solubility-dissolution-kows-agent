/** Idealized screening; corresponding Python implementation: solubility_mind/chemistry.py. */
function check(name, x, options = {}) {
  if (typeof x !== "number" || !Number.isFinite(x)) throw new Error(name + " must be finite");
  if (options.positive && x <= 0) throw new Error(name + " must be greater than zero");
  if (options.nonnegative && x < 0) throw new Error(name + " must not be negative");
  return x;
}
export function calculate({
  intrinsic_solubility_mg_ml: sol, dose_mg: dose,
  ionization = "neutral", pka = null, permeability = "unknown",
  octanol_concentration_mg_ml: co = null, water_concentration_mg_ml: cw = null,
  diffusion_cm2_s: d = null, surface_area_cm2: area = null,
  diffusion_layer_cm: layer = null, bulk_concentration_mg_ml: bulk = null
}) {
  check("Intrinsic solubility", sol, {positive:true});
  check("Dose", dose, {positive:true});
  if (!["neutral", "acid", "base"].includes(ionization)) throw new Error("Invalid ionization");
  if (!["unknown", "high", "low"].includes(permeability)) throw new Error("Invalid permeability evidence");
  if (ionization !== "neutral") {
    if (pka === null) throw new Error("pKa is required for acid/base");
    check("pKa", pka);
    if (pka < -10 || pka > 20) throw new Error("pKa must be between -10 and 20");
  } else if (pka !== null) check("pKa", pka);
  const ph_profile = [1.2, 4.5, 6.8].map(ph => {
    const factor = ionization === "acid" ? 1 + 10 ** (ph-pka)
      : ionization === "base" ? 1 + 10 ** (pka-ph) : 1;
    const solubility_mg_ml = sol * factor;
    if (!Number.isFinite(solubility_mg_ml) || solubility_mg_ml <= 0) {
      throw new Error("Solubility is outside the numeric range");
    }
    return {ph, solubility_mg_ml};
  });
  const minimum_solubility_mg_ml = Math.min(...ph_profile.map(x => x.solubility_mg_ml));
  const dose_number = dose / (250 * minimum_solubility_mg_ml);
  const high = dose_number <= 1;
  const bcs_screen = permeability === "unknown" ? null
    : permeability === "high" ? (high ? "I" : "II") : (high ? "III" : "IV");
  let log_kow = null;
  if (co !== null || cw !== null) {
    if (co === null || cw === null) throw new Error("Both octanol and water concentrations are required");
    check("Octanol concentration", co, {positive:true});
    check("Water concentration", cw, {positive:true});
    log_kow = Math.log10(co / cw);
  }
  let dissolution_rate_mg_s = null;
  if ([d,area,layer,bulk].some(x => x !== null)) {
    if ([d,area,layer,bulk].some(x => x === null)) throw new Error("All four dissolution fields are required");
    check("Diffusion coefficient", d, {nonnegative:true});
    check("Surface area", area, {positive:true});
    check("Diffusion-layer thickness", layer, {positive:true});
    check("Bulk concentration", bulk, {nonnegative:true});
    dissolution_rate_mg_s = d * area / layer * (minimum_solubility_mg_ml - bulk);
    if (!Number.isFinite(dissolution_rate_mg_s)) throw new Error("Dissolution rate is outside the numeric range");
  }
  return {
    ph_profile, minimum_solubility_mg_ml, dose_number,
    solubility_screen: high ? "high" : "low", bcs_screen,
    log_kow, dissolution_rate_mg_s,
    interpretation: "Model-based screening only; not a validated BCS classification or biowaiver assessment."
  };
}
