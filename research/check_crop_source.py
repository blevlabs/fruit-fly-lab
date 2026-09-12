"""Source-equation replay only; not a crop organ, storage law or feeding policy.

python data/research/m2/internal-state/check_crop_source.py
No MuJoCo, live state, fitted motor parameter or runtime module is imported.
"""
import hashlib
import json
import math
from pathlib import Path


def conductance(radius_m, length_m, viscosity_pa_s):
    if not all(math.isfinite(v) and v > 0 for v in (radius_m, length_m, viscosity_pa_s)):
        raise ValueError("Positive finite radius, length and viscosity required")
    return math.pi * radius_m**4 / (8 * viscosity_pa_s * length_m)


def main():
    folder = Path(__file__).resolve().parents[1] / 'data/research/m2/internal-state'
    inputs = json.loads((folder / "crop-source-inputs.json").read_text())
    assert hashlib.sha256((folder / inputs["workbook_name"]).read_bytes()).hexdigest() == inputs["workbook_sha256"]
    cells = inputs["source_values"]
    val = lambda cell: cells[cell]["cached_value"]
    ko = conductance(val("D306"), val("D309"), val("D312"))
    kc = conductance(val("D307"), val("D310"), val("D312"))
    q = val("E318") / val("D318")
    pressure = -q * (1/ko + 1/kc)  # Authors' Methods equation; not a measured load.
    source_wrong = -q * (1/val("D311") + 1/val("D310"))
    assert math.isclose(source_wrong, val("G318"), rel_tol=1e-12)
    assert cells["G318"]["formula_or_value"] == "=-F318*(1/D311+1/D310)"
    assert math.isclose(-pressure / (1/ko + 1/kc), q, rel_tol=1e-12)
    assert math.isclose(conductance(2*val("D306"), val("D309"), val("D312")), 16*ko, rel_tol=1e-12)
    for invalid in [(0, 1, 1), (1, -1, 1), (1, 1, math.nan)]:
        try:
            conductance(*invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid physical dimensions accepted")
    result = {
        "implementation": "PASS: source values, units, resistance arithmetic and invalid-input rejection",
        "source_workbook_sha256": inputs["workbook_sha256"],
        "input_sha256": hashlib.sha256((folder / "crop-source-inputs.json").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reported_dimensions": {"oesophagus_radius_um": val("D306")*1e6, "oesophagus_length_mm": val("D309")*1e3,
                                "crop_duct_radius_um": val("D307")*1e6, "crop_duct_length_mm": val("D310")*1e3},
        "model_replay": {"oesophagus_conductance_m3_Pa_s": ko, "crop_duct_conductance_m3_Pa_s": kc,
                         "input_flow_nL_s": q*1e12, "pressure_Pa": pressure,
                         "virgin_relative_sip_factor": val("F321"),
                         "virgin_pressure_Pa": pressure*val("F321")},
        "source_formula_issue": {"formula": cells["G318"]["formula_or_value"], "cached_value": source_wrong,
                                 "actual_dimensions": "(m3/s)*(1/m) = m2/s, not Pa",
                                 "methods_relation": "-Q*(1/K_oesophagus + 1/K_crop_duct)"},
        "biological_validation": "OPEN: pressure is inferred from geometry, assumed viscosity and imposed sip; no independent pressure or P(V) observation",
        "physical_extension": "NOT IMPLEMENTED: no calibrated crop capacity/compliance, dry filling or salivary supply relation",
        "capability": "NOT TESTED", "runtime_mutations": False}
    (folder / "crop-source-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
