import {calculate} from "./chemistry.mjs";
const form=document.querySelector("#calculator");
const result=document.querySelector("#result");
const error=document.querySelector("#error");
const empty=document.querySelector("#empty");
const exportButton=document.querySelector("#export");
const pkaField=form.elements.namedItem("pka");
let last=null;

function value(name) { return form.elements.namedItem(name).value; }
function number(name) {
  const input=form.elements.namedItem(name);
  return input.value.trim() === "" ? null : input.valueAsNumber;
}
function fmt(n) { return n===null ? "Not calculated" : Number(n.toPrecision(6)).toString(); }
function inputs() {
  return {
    intrinsic_solubility_mg_ml:number("intrinsic_solubility_mg_ml"),
    dose_mg:number("dose_mg"),
    ionization:value("ionization"),
    pka:value("ionization")==="neutral" ? null : number("pka"),
    permeability:value("permeability"),
    octanol_concentration_mg_ml:number("octanol_concentration_mg_ml"),
    water_concentration_mg_ml:number("water_concentration_mg_ml"),
    diffusion_cm2_s:number("diffusion_cm2_s"),
    surface_area_cm2:number("surface_area_cm2"),
    diffusion_layer_cm:number("diffusion_layer_cm"),
    bulk_concentration_mg_ml:number("bulk_concentration_mg_ml"),
    saturation_concentration_mg_ml:number("saturation_concentration_mg_ml")
  };
}
function updateIonization() {
  const show=value("ionization")!=="neutral";
  document.querySelector("#pka-group").hidden=!show;
  pkaField.disabled=!show;
}
form.elements.namedItem("ionization").addEventListener("change",updateIonization);
updateIonization();
form.addEventListener("submit",event=>{
  event.preventDefault();
  error.hidden=true;
  try {
    const input=inputs(), output=calculate(input);
    last={input,output};
    document.querySelector("#solubility-result").textContent=output.solubility_screen.toUpperCase()+" (model screen)";
    document.querySelector("#dose-result").textContent=fmt(output.dose_number);
    document.querySelector("#bcs-result").textContent=output.bcs_screen===null
      ? "Undetermined — permeability evidence required" : "Provisional Class "+output.bcs_screen;
    document.querySelector("#min-result").textContent=fmt(output.minimum_solubility_mg_ml)+" mg/mL";
    document.querySelector("#kow-result").textContent=fmt(output.log_kow);
    document.querySelector("#rate-result").textContent=output.dissolution_rate_mg_s===null
      ? "Not calculated" : fmt(output.dissolution_rate_mg_s)+" mg/s";
    const body=document.querySelector("#ph-data");
    body.replaceChildren();
    for (const point of output.ph_profile) {
      const tr=document.createElement("tr");
      for (const v of [point.ph,fmt(point.solubility_mg_ml)]) {
        const td=document.createElement("td"); td.textContent=String(v); tr.append(td);
      }
      body.append(tr);
    }
    result.hidden=false;empty.hidden=true;exportButton.disabled=false;
  } catch (e) {
    last=null; result.hidden=true;empty.hidden=false;exportButton.disabled=true;
    error.textContent=e.message||"Calculation failed";error.hidden=false;
  }
});
const csv=(v)=>'"'+String(v??"").replace(/"/g,'""')+'"';
exportButton.addEventListener("click",()=>{
  if(!last)return;
  const fields=[...Object.entries(last.input),
    ...Object.entries(last.output).filter(([key])=>key!=="ph_profile")];
  for(const x of last.output.ph_profile)fields.push(["solubility_at_pH_"+x.ph,x.solubility_mg_ml]);
  const text="parameter,value\r\n"+fields.map(([k,v])=>csv(k)+","+csv(v)).join("\r\n")+"\r\n";
  const url=URL.createObjectURL(new Blob([text],{type:"text/csv;charset=utf-8"}));
  const a=document.createElement("a");a.href=url;a.download="solubility-screen.csv";
  document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
