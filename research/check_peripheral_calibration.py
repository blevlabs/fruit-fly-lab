"""Independent adult material references and frozen-drive audit; no body/runtime writes.

Run: MUJOCO_GL=disable .venv/bin/python -B check_peripheral_calibration.py
Reported fit reconstruction is not independent biological validation. Force-clamp
and slack comparisons preserve assay identity; neither is a whole-animal outcome.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import mujoco as mj

from neuromuscular import NeuromuscularJunction

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "runtime/neural-motor/peripheral-calibration-data.json"


def probe_assay(reference):
    """Replay original measured balance matrix and source preprocessing exactly."""
    matrix = reference["matrix"]
    points = []
    for col in range(1, 6):  # Source MATLAB columns 2..6; column 7 is excluded.
        baseline = matrix[0][col] if col in [1, 2, 4, 5] else 0
        if baseline is None:
            continue  # Preserve the author's NaN-baseline loss of column 3.
        points.extend((row[0] * 1e-6, (row[col] - baseline) * 1e-7 * 9.8, col)
                      for row in matrix if row[col] is not None)

    def fit(rows):
        xm = math.fsum(x for x, _, _ in rows) / len(rows)
        ym = math.fsum(y for _, y, _ in rows) / len(rows)
        slope = math.fsum((x - xm) * (y - ym) for x, y, _ in rows) / math.fsum(
            (x - xm)**2 for x, _, _ in rows)
        return slope, ym - slope * xm

    k, intercept = fit(points)
    assert len(points) == 42
    assert math.isclose(k, .22341945095875296, abs_tol=1e-12)
    residual = math.fsum((y - k*x - intercept)**2 for x, y, _ in points)
    ym = math.fsum(y for _, y, _ in points) / len(points)
    r2 = 1 - residual / math.fsum((y - ym)**2 for _, y, _ in points)
    calibration = [p for p in points if p[2] != 5]
    holdout = [p for p in points if p[2] == 5]
    kc, ic = fit(calibration)
    rmse = math.sqrt(math.fsum((y - kc*x - ic)**2 for x, y, _ in holdout) / len(holdout))
    mass, damping = reference["dynamic_mass_kg"], reference["dynamic_damping_kg_s"]
    zeta = damping / (2 * math.sqrt(mass * reference["source_reported_stiffness_N_m"]))
    return {"implementation": "PASS: 42-point source calibration replay",
            "measured_data_fit": {"stiffness_N_m": k, "intercept_N": intercept, "R_squared": r2},
            "instrument_column_holdout": {"calibration_points": len(calibration), "held_out_points": len(holdout),
                                           "calibration_stiffness_N_m": kc, "rmse_N": rmse,
                                           "status": "diagnostic only, no acceptance margin; not muscle/specimen holdout"},
            "source_dynamic_consistency": {"mass_kg": mass, "damping_kg_s": damping,
                                           "relaxation_s": 2*mass/damping,
                                           "damped_period_s": 2*math.pi/math.sqrt(reference["source_reported_stiffness_N_m"]/mass*(1-zeta*zeta))},
            "biological_validation": "OPEN: instrument calibration is not spike-to-force validation; zero motor-unit trial bytes obtained",
            "capability": "NOT TESTED"}


def tdt_material(pca, shortening_ML_s, calibration):
    """Skinned TDT at reference length; positive velocity means shortening.

    Domain excludes length changes, eccentric contractions and activation kinetics.
    pCa is -log10(free calcium in mol/L), never the NMJ's dimensionless excitation.
    """
    c = {k: v["mean"] for k, v in calibration.items()}
    vmax = c["hill_b_ML_s"] / c["hill_a_over_F0"]
    if not (math.isfinite(pca) and 5 <= pca <= 8
            and math.isfinite(shortening_ML_s) and 0 <= shortening_ML_s <= vmax):
        raise ValueError("Reference domain: pCa 5..8, shortening 0..Hill vmax")
    fraction = 1 / (1 + 10 ** (c["hill_n"] * (pca - c["pCa50"])))
    saturated = 1 / (1 + 10 ** (c["hill_n"] * (5 - c["pCa50"])))
    fv = (c["hill_b_ML_s"] - c["hill_a_over_F0"] * shortening_ML_s) / (
        c["hill_b_ML_s"] + shortening_ML_s)
    return c["active_stress_Pa"] * fraction / saturated * fv


def material_assay(reference):
    c = reference["calibration"]
    alpha, b = c["hill_a_over_F0"]["mean"], c["hill_b_ML_s"]["mean"]
    vmax = b / alpha
    vopt = b * (math.sqrt(1 + 1 / alpha) - 1)
    fopt = tdt_material(5, vopt, c) / c["active_stress_Pa"]["mean"]
    assert math.isclose(tdt_material(5, 0, c), 37000, abs_tol=1e-9)
    assert abs(tdt_material(5, vmax, c)) < 1e-9
    assert tdt_material(8, 0, c) < 1e-15
    assert math.isclose(tdt_material(c["pCa50"]["mean"], 0, c) / 37000, .5,
                        abs_tol=3e-7)  # Source normalization is exactly pCa 5.
    for invalid in [(4, 0), (9, 0), (5, -1), (5, vmax + .01), (math.nan, 0)]:
        try:
            tdt_material(*invalid, c)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid material input accepted")
    # Native scalar law with unit L0 and F0; no XML/body/scene is instantiated.
    # Set speed to source Hill vmax only to isolate the shape comparison.
    prm = [.25, 1.25, 1., 200., .5, 1.6, vmax, 1.3, 1.2]
    native = lambda v: -mj.mju_muscleGain(1.25, -v, [.5, 1.5], 1., prm)
    shape_error = max(abs(native(vmax * i / 1000) - (1 - i / 1000)**2)
                      for i in range(1001))
    assert shape_error < 1e-12
    grid_peaks = []
    for intervals in [1000, 2000]:
        velocities = [vmax * i / intervals for i in range(intervals + 1)]
        peak = max(velocities, key=lambda v: v * tdt_material(5, v, c))
        assert abs(peak - vopt) <= vmax / intervals
        grid_peaks.append(peak)
    published = reference["source_fit_checks_not_holdout"]
    slack = reference["reserved_comparison"]["slack_velocity_ML_s"]
    geom = reference["representative_bundle_geometry_not_whole_muscle"]
    return {
        "implementation": "PASS: units, endpoints, domain rejection, native shape identity",
        "numerical": {"native_shape_max_abs_error": shape_error,
                      "peak_velocity_grid_ML_s": grid_peaks,
                      "peak_velocity_exact_ML_s": vopt},
        "source_fit_reconstruction_not_validation": {
            "Ca50_uM": 10**(-c["pCa50"]["mean"]) * 1e6,
            "Hill_vmax_ML_s": vmax, "Hill_peak_power_velocity_ML_s": vopt,
            "Hill_peak_power_force_fraction": fopt,
            "Hill_peak_power_normalized_s_inv": vopt * fopt,
            "published_derived_quantities": published,
            "representative_bundle_capacity_uN_not_individual_force":
                c["active_stress_Pa"]["mean"] * geom["width_um"] * geom["depth_um"] * 1e-6},
        "comparisons": {
            "native_peak_power_force_fraction": native(vmax / 3),
            "measured_peak_power_force_fraction": published["peak_power_force_fraction"],
            "shape_verdict": "INCOMPATIBLE with source mean: native 4/9 vs TDT .26; gain or vmax scaling cannot change the dimensionless optimum. Descriptive comparison, not prespecified biological equivalence test.",
            "reserved_slack_measured": slack,
            "Hill_minus_slack_ML_s": vmax - slack["mean"],
            "holdout_status": "OPEN: separate assay was not used for constants; individual overlap and covariance unavailable; not an untouched prospective biological validation set"},
        "biological_validation": "OPEN: source-fitted material reference only; raw specimens, transfer conditions and living excitation-force link absent",
        "capability": "NOT TESTED",
        "curves": [{"pCa": pca, "shortening_ML_s": v, "active_stress_Pa": tdt_material(pca, v, c)}
                   for pca in [8, 6, 5.7, 5.62, 5.5, 5] for v in [0, vopt, vmax]]}


def activation_rate(u, a, timeconst):
    rise, fall = timeconst
    tau = rise * (.5 + 1.5 * a) if u > a else fall / (.5 + 1.5 * a)
    return (u - a) / tau


def periodic_assay(rate, dt, params, timeconst):
    period = round(1 / (rate * dt))
    assert math.isclose(period * dt, 1 / rate, abs_tol=1e-12)
    R, E = math.exp(-period * dt / params["tau_recovery_s"]), math.exp(-period * dt / params["tau_exc_s"])
    x = (1 - R) / (1 - (1 - params["depression"]) * R)
    amplitude = params["spike_gain"] * x / (1 - E)
    nmj = NeuromuscularJunction(dt, params)
    start = round(2 / dt) + nmj.delay_steps + 1
    a = worst = sum_u = sum_a = peak_a = 0.
    for step in range(start + period):
        u = nmj.advance(step % period == 0)
        a += dt * activation_rate(u, a, timeconst)
        if step >= start:
            phase = (step - nmj.delay_steps - 1) % period
            z = amplitude * math.exp(-(phase + .5) * dt / params["tau_exc_s"])
            worst = max(worst, abs(u - z / (1 + z)))
            sum_u += u
            sum_a += a
            peak_a = max(peak_a, a)
    assert worst < 1e-10
    return {"dt_s": dt, "rate_Hz": rate, "periodic_formula_max_abs_error": worst,
            "mean_control": sum_u / period, "mean_activation": sum_a / period,
            "peak_activation": peak_a, "stationary_event_efficacy": x}


def drive_assay(config, cm9):
    p, tc = config["nmj"], config["leg_activation_time_s"]
    for u in [0, .05, .2, 1]:
        for a in [0, .03, .1, .9]:
            assert math.isclose(activation_rate(u, a, tc),
                                mj.mju_muscleDynamics(u, a, [*tc, 0]), abs_tol=1e-12)
    rows, errors = [], []
    for rate in [20, 40, 100, 500]:
        coarse = periodic_assay(rate, config["timestep_s"], p, tc)
        fine = periodic_assay(rate, config["timestep_s"] / 2, p, tc)
        errors.append(abs(coarse["mean_activation"] - fine["mean_activation"]))
        rows.extend([coarse, fine])
    assert max(errors) < 2e-5
    release_dt = .05
    nmj = NeuromuscularJunction(config["timestep_s"], p)
    increments = []
    spacing = round(release_dt / nmj.dt)
    for step in range(spacing + nmj.delay_steps + 2):
        before, delivered = nmj.excitation, nmj.delivered
        nmj.advance(step in [0, spacing])
        if nmj.delivered != delivered:
            increments.append(nmj.excitation / nmj.decay - before)
    ratio = increments[1] / increments[0]
    exact = 1 - p["depression"] * math.exp(-release_dt / p["tau_recovery_s"])
    assert math.isclose(ratio, exact, abs_tol=1e-12)
    return {"implementation": "PASS: actual NMJ event increments, periodic controls, native activation primitive",
            "numerical": {"max_abs_half_step_activation_error": max(errors)},
            "parameters": p, "parameter_status": "unchanged effective-drive estimates; not voltage or calcium",
            "model_output": rows, "model_50_ms_increment_ratio": ratio,
            "CM9_measured_electrical_reference": cm9["calibration_reference"],
            "CM9_reserved_protocol": cm9["reserved_protocol"],
            "biological_validation": "OPEN: non-significant train depression is not a zero-depression datum; EPSP/mEPSP means do not identify force or both depression/recovery constants",
            "capability": "NOT TESTED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/research/m2/results.json")
    args = parser.parse_args()
    started = time.perf_counter()
    reference = json.loads(DATA.read_text())
    config = json.loads((ROOT / "runtime/cns-model.json").read_text())
    identities = [DATA, Path(__file__), ROOT / "runtime/neuromuscular.py", ROOT / "runtime/cns-model.json",
                  ROOT / "runtime/neural-motor/malecns-motor-map.json"]
    result = {"kind": "isolated-independent-reference-assays", "mujoco": mj.__version__,
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in identities},
              "initial_state": "fresh scalar states, x=1 e=a=0; no RNG/body/scene/individual",
              "foreleg_probe": probe_assay(reference["foreleg_probe"]),
              "TDT": material_assay(reference["tdt"]),
              "NMJ_CM9": drive_assay(config, reference["cm9"])}
    result["wall_time_s"] = time.perf_counter() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "implementation": "PASS", "numerical": "PASS",
                      "biological_validation": "OPEN; native TDT shape mismatch retained",
                      "capability": "NOT TESTED", "wall_time_s": result["wall_time_s"]}))


if __name__ == "__main__":
    main()
