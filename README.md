# Solubility & Dissolution Screening Calculator

A browser-based and Python physicochemical calculator for exploratory pharmaceutical research. The browser application runs locally without a backend, external models, or uploading inputs.

## Capabilities

- Idealized pH-dependent solubility at pH 1.2, 4.5, and 6.8 for monoprotic weak acids, weak bases, and neutral solutes.
- Dose number from the highest single dose, 250 mL and minimum modeled solubility.
- Provisional BCS quadrant I–IV only when independent high/low permeability evidence is supplied. Log Kow is never used to infer permeability.
- Optional log10 octanol/water concentration ratio from measured equilibrium concentrations (not necessarily intrinsic log Kow for ionizable solutes).
- Optional instantaneous Noyes–Whitney dissolution rate from diffusion coefficient, area, boundary-layer thickness, and independently supplied bulk and saturation concentrations in the dissolution medium.
- CSV export and equivalent Python calculations exposed through FastAPI.
- The earlier generic task-audit APIs and CLIs remain available for compatibility, but their fixed thresholds are not physicochemical BCS criteria.

## Browser application

Serve the repository root using:

    python -m http.server 8080

Then open http://localhost:8080/docs/ in a modern browser. The alternative top-level index.html redirects to the calculator. An HTTP server is recommended because some browsers restrict JavaScript modules on file:// URLs.

Enter intrinsic solubility (mg/mL) and highest single dose (mg). Choose ionization and enter pKa for monoprotic weak acids/bases. Optional octanol/water and dissolution fields can be left empty or entered as complete groups. Dissolution Cs and Cb must refer to the same medium. Select Calculate, then Export CSV.

GitHub Pages can deploy the docs directory through the included GitHub Actions workflow when repository Pages settings use GitHub Actions as the source.

## Python / API

Requires Python 3.9+. Install and test:

    python -m pip install -e . pytest
    python -m pytest -q
    node --test tests/test_browser.mjs

Run the FastAPI service with:

    python cli.py serve --host 127.0.0.1 --port 8000

The server serves the same browser calculator at /docs/. POST /api/chemistry accepts JSON with fields named as in the browser form, for example:

    curl -X POST http://127.0.0.1:8000/api/chemistry -H 'Content-Type: application/json' -d '{"intrinsic_solubility_mg_ml":0.5,"dose_mg":100,"permeability":"unknown"}'

The legacy service endpoints are /api/audit, /api/chat, /api/audit/logs, /health and JSON /metrics. For legacy CLI compatibility:

    python cli.py audit --primary 29.4 --secondary 14.8
    python cli.py batch -i sample.csv -o results.csv
    python cli.py verify-audit
    python -m solubility_mind.cli audit

The installed solubility-dissolution-kows-agent command runs the solubility_mind legacy CLI. Neither legacy task workflow produces a validated BCS classification.

## Scientific limitations

**Screening only, not a regulatory BCS determination.** ICH M9 requires experimental equilibrium solubility over the relevant pH range at 37 ± 1 °C, using the highest single therapeutic dose in 250 mL or less, and separately justified permeability evidence. The model here provides theoretical monoprotic pH profiles, not experimental measurements. It omits activity coefficients, salts, complex ionization, polymorphism, solubility in actual biorelevant media, temperature, kinetic precipitation, and human pharmacokinetics.

Permeability evidence must be supplied externally. The provisional BCS quadrant is therefore an illustrative screening combination, not a biowaiver eligibility decision. Do not use the result for therapeutic decisions, regulated release, or clinical recommendations.

Scientific reference: [ICH M9 guideline](https://database.ich.org/sites/default/files/M9_Guideline_Step4_2019_1116.pdf).

## Privacy, security and technology

The static browser app performs calculations entirely on-device and sends no input data to any service. It has no analytics or user accounts. It uses dependency-free ES modules; Pyodide is unnecessary because the models are lightweight and can execute faster in native JavaScript. Suitable for current Chromium, Firefox and Safari browsers.

The optional legacy Python API stores dossiers and the audit chain in process memory. HMAC-SHA256 signatures protect logged metadata against modification while the secret remains protected; the log does not persist across restarts. If AUDIT_SECRET_KEY is omitted, an ephemeral random key is used. Existing regex-based identifier checks are limited and are not a substitute for de-identification. Do not submit patient-identifiable data to the legacy API.

For local Docker usage:

    docker build -t solubility-dissolution-kows-agent .
    docker run -p 8000:8000 solubility-dissolution-kows-agent

Docker Compose allows an optional AUDIT_SECRET_KEY; there is no fixed default signing key.

License: [MIT](LICENSE).
