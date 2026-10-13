import test from "node:test";
import assert from "node:assert/strict";
import {calculate} from "../docs/chemistry.mjs";
const approx=(x,y)=>assert.ok(Math.abs(x-y)<1e-10);
test("neutral dose number and class",()=>{
  const d=calculate({intrinsic_solubility_mg_ml:0.5,dose_mg:100,permeability:"high"});
  approx(d.dose_number,0.8);assert.equal(d.bcs_screen,"I");
});
test("weak acid/base profile",()=>{
  const a=calculate({intrinsic_solubility_mg_ml:0.01,dose_mg:10,ionization:"acid",pka:4.5,permeability:"low"});
  approx(a.ph_profile[1].solubility_mg_ml,0.02);assert.equal(a.bcs_screen,"IV");
  const b=calculate({intrinsic_solubility_mg_ml:0.01,dose_mg:10,ionization:"base",pka:4.5});
  assert.ok(b.ph_profile[0].solubility_mg_ml>b.ph_profile[2].solubility_mg_ml);
  assert.equal(b.bcs_screen,null);
});
test("partition and dissolution",()=>{
  const d=calculate({intrinsic_solubility_mg_ml:2,dose_mg:100,octanol_concentration_mg_ml:10,
    water_concentration_mg_ml:1,diffusion_cm2_s:1e-5,surface_area_cm2:10,
    diffusion_layer_cm:0.01,bulk_concentration_mg_ml:0.5,
    saturation_concentration_mg_ml:2.0});
  approx(d.log_kow,1);approx(d.dissolution_rate_mg_s,0.015);
});
test("invalid data",()=>{
  const b={intrinsic_solubility_mg_ml:1,dose_mg:10};
  for(const extra of [{dose_mg:NaN},{dose_mg:Infinity},{dose_mg:0},{ionization:"acid"},
    {pka:100,ionization:"base"},{octanol_concentration_mg_ml:10},{diffusion_cm2_s:1}]) {
    assert.throws(()=>calculate({...b,...extra}));
  }
});

test("extreme partition ratios stay finite and overflowed dose numbers are rejected",()=>{
  assert.throws(()=>calculate({intrinsic_solubility_mg_ml:1e-300,dose_mg:1e300}));
  const p=calculate({intrinsic_solubility_mg_ml:0.5,dose_mg:100,
    octanol_concentration_mg_ml:1e300,water_concentration_mg_ml:1e-300});
  approx(p.log_kow,600);
});
