"""CPU-only geometry/constitutive assay; no connectome, NMJ or feeding policy.

Run: MUJOCO_GL=disable .venv/bin/python -B check_proboscis_muscles.py
Diagnostic poses/excitation below test mechanics only, never an importer policy.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

import mujoco as mj
import numpy as np
from flygym.anatomy import AxisOrder, JointPreset, Skeleton
from flygym.compose import KinematicPosePreset, NeuroMechFly, TetheredWorld
from flygym.utils.math import Rotation3D

from proboscis_muscles import JOINT_NAMES, LABELLUM_GEOMS, M9_CONFIG, MUSCLE_TARGETS, PUMP_TARGETS, ProboscisHydraulics, UNIMPLEMENTED_TARGETS, add_proboscis_muscles


def moments(model, data):
    matrix = np.zeros((model.nu, model.nv))
    for i in range(model.nu):
        start, count = data.moment_rowadr[i], data.moment_rownnz[i]
        matrix[i, data.moment_colind[start:start + count]] = data.actuator_moment[start:start + count]
    return matrix


def mesh_points_in_body(model, data, geom_name, body_name):
    geom = model.geom(geom_name).id
    mesh = model.geom_dataid[geom]
    start, count = model.mesh_vertadr[mesh], model.mesh_vertnum[mesh]
    world = model.mesh_vert[start:start + count] @ data.geom_xmat[geom].reshape(3, 3).T + data.geom_xpos[geom]
    body = data.body(body_name)
    return (world - body.xpos) @ body.xmat.reshape(3, 3)


def check_motor_bindings(records, subclasses=("pm",)):
    """Read-only canonical output-topology join, including bilateral and unpaired."""
    path = (Path(__file__).resolve().parents[1] / 'runtime') / "neural-motor/malecns-motor-map.json"
    raw = path.read_bytes()
    motors = json.loads(raw)["motors"]
    assert len({r["bodyId"] for r in motors}) == len(motors)
    physical = {(r["semantic_muscle_key"], "unpaired" if r["side"] == "unpaired" else r["peripheral_target_side"]): r for r in records}
    assert len(physical) == len(records)
    represented = {key for key, side in physical}
    bindings, gaps = [], []
    pm = [r for r in motors if r["subclass"] in subclasses]
    for row in pm:
        key = row["semantic_muscle_key"]
        sides = row["peripheral_target_sides"]
        topology = row["peripheral_target_topology"]
        outputs = ["unpaired"] if topology == "unpaired_organ_group" else sides
        reasons = []
        if key is None:
            reasons.append("unresolved_target")
        elif key not in represented:
            reasons.append("missing_geometry")
        if not outputs:
            reasons.append("unresolved_peripheral_side")
        if key is not None and row["evidence_status"] != "supported_at_stated_resolution":
            reasons.append("unsupported_target_evidence")
        record = dict(bodyId=row["bodyId"], semantic_muscle_key=key,
            peripheral_target_side=row["peripheral_target_side"], peripheral_target_sides=sides,
            peripheral_target_topology=topology)
        if reasons:
            gaps.append(dict(record, reasons=reasons))
        else:
            for side in outputs:
                assert (key, side) in physical, (key, side)
                bindings.append(dict(record, physical_side=side, actuator_name=physical[key, side]["actuator_name"]))
    assert len({b["bodyId"] for b in bindings}) + len(gaps) == len(pm)
    assert all(not gap["peripheral_target_sides"]
               for gap in gaps if "unresolved_peripheral_side" in gap["reasons"])
    mn9 = {r["bodyId"]: r["peripheral_target_side"] for r in bindings
           if r["semantic_muscle_key"] == "proboscis.m9"}
    if "proboscis.m9" in represented:
        assert mn9 == {10331: "L", 16949: "R"}
    bound_names = {r["actuator_name"] for r in bindings}
    return dict(source=str(path), sha256=hashlib.sha256(raw).hexdigest(),
        motor_rows=len(motors), selected_subclasses=list(subclasses), selected_motor_rows=len(pm),
        named_selected_motor_rows=sum(r["semantic_muscle_key"] is not None for r in pm),
        bindable_motor_rows=len({b["bodyId"] for b in bindings}), output_path_matches=len(bindings),
        covered_physical_actuators=len(bound_names),
        physical_actuators_without_confirmed_input=[r["actuator_name"] for r in records if r["actuator_name"] not in bound_names],
        gap_reason_counts=dict(Counter(reason for gap in gaps for reason in gap["reasons"])),
        bindings=bindings, gaps=gaps, runtime_connections_created=0)


def check_hydraulics(model, fly_name):
    data = mj.MjData(model)
    key = model.key("neutral").id
    mj.mj_resetDataKeyframe(model, data, key)
    fluid = ProboscisHydraulics(model, fly_name=fly_name)
    fluid.reset(data)
    report = fluid.advance(data, 1e-5)
    assert not any(report["boundary_flow_mm3_s"].values()) and not fluid.pressure_pa.any()
    initial = float(fluid.liquid_volume_mm3.sum())
    j = fluid.wall_joints[0]
    data.qpos[j.qposadr[0]] += 0.001  # Sealed isovolumetric material probe.
    report = fluid.advance(data, 1e-5, inlet_pressure_pa=None, crop_pressure_pa=None,
                           proventriculus_pressure_pa=None, salivary_pressure_pa=None)
    assert abs(fluid.liquid_volume_mm3.sum() - initial) < 1e-14
    assert fluid.pressure_pa[0] < 0 and fluid.generalized_forces(data)[j.dofadr[0]] < 0
    # Pressure loads must be work-conjugate to actual wall/crop geometry.
    forces = fluid.generalized_forces(data)
    for joint in fluid.wall_joints + fluid.crop_joints:
        address = joint.qposadr[0]
        reference = data.qpos[address]
        volumes = []
        for delta in (1e-7, -1e-7):
            data.qpos[address] = reference + delta
            volumes.append(fluid._geometry(data)[0])
        data.qpos[address] = reference
        derivative = (volumes[0] - volumes[1]) / 2e-7
        np.testing.assert_allclose(forces[joint.dofadr[0]], fluid.pressure_pa @ derivative, atol=1e-8)

    outflows = []
    max_residual = 0.0
    for radial_displacement in (0, -0.012):
        mj.mj_resetDataKeyframe(model, data, key)
        for joint in fluid.crop_joints:
            data.qpos[joint.qposadr[0]] = radial_displacement
        fluid.reset(data)
        for _ in range(1000):
            # An imposed pressure difference is a passive flow assay, not feeding.
            report = fluid.advance(data, 1e-5, inlet_pressure_pa=100)
            max_residual = max(max_residual, abs(report["conservation_residual_mm3"]))
            assert report["hydraulic_dissipation_nW"] >= 0
        assert report["boundary_flow_mm3_s"]["inlet"] > 0
        outflows.append(-report["boundary_flow_mm3_s"]["crop"])
    assert 0 < outflows[1] < outflows[0]
    # Couple pressure reaction to native force-driven mechanics at 10 us.
    mj.mj_resetDataKeyframe(model, data, key)
    fluid.reset(data)
    model.opt.timestep = 1e-5
    actuator = model.actuator(f"{fly_name}/proboscis_muscle_left_m10").id
    for tick in range(2000):
        data.ctrl[actuator] = 0.5 if tick < 1000 else 0
        report = fluid.advance(data, 1e-5, inlet_pressure_pa=0)
        data.qfrc_applied[:] = fluid.generalized_forces(data)
        mj.mj_step(model, data)
        max_residual = max(max_residual, abs(report["conservation_residual_mm3"]))
        assert np.isfinite(data.qpos).all() and (fluid.liquid_volume_mm3 > 0).all()
    assert not any(w.number for w in data.warning)
    assert max_residual < 1e-12
    return dict(max_conservation_residual_mm3=max_residual,
                crop_outflow_open_constricted_mm3_s=outflows,
                scope="primed passive pressure-flow mechanics; no feeding trajectory")


def check():
    fly = NeuroMechFly(name="proboscis_check")
    fly.add_joints(Skeleton(axis_order=AxisOrder.YAW_PITCH_ROLL, joint_preset=JointPreset.LEGS_ONLY),
                   KinematicPosePreset.NEUTRAL, stiffness=0, damping=0.02, armature=1e-6)
    before_joints = [(j.name, np.r_[j.axis, j.stiffness, j.damping, j.armature].copy()) for j in fly.mjcf_root.joints]
    before_shapes = [(g.name, g.mass, g.meshname) for g in fly.mjcf_root.geoms]
    before_bodies = [(b.name, b.pos.copy(), b.quat.copy()) for b in fly.mjcf_root.bodies]
    before_spec = fly.mjcf_root.copy()
    before_spec.compiler.fusestatic = False
    before_model = before_spec.compile()
    before_mass = float(before_model.body_mass.sum())
    before_data = mj.MjData(before_model)
    mj.mj_forward(before_model, before_data)
    original_surface = mesh_points_in_body(before_model, before_data, "c_haustellum", "c_haustellum")
    # Rejected arguments must leave the rig untouched.
    for options in ({"group_force_uN": 0}, {"activation_time_s": (0.01, float("nan"))},
                    {"activation_time_s": (1e-5, 4e-5)}):
        try:
            add_proboscis_muscles(fly, **options)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid muscle parameter was accepted")
        assert len(list(fly.mjcf_root.joints)) == len(before_joints)
        assert not list(fly.mjcf_root.actuators) and not list(fly.mjcf_root.tendons)

    records = add_proboscis_muscles(fly)
    assert Counter(r["side"] for r in records) == {"left": 17, "right": 17, "unpaired": 1}
    assert Counter(r["muscle_target"] for r in records if r["limb"] == "proboscis") == {target: 2 for target in MUSCLE_TARGETS}
    assert len({r["actuator_name"] for r in records}) == 35
    assert len(list(fly.mjcf_root.joints)) == len(before_joints) + 18
    for name, mass, mesh in before_shapes:
        geom = fly.mjcf_root.geom(name)
        if name not in ("c_haustellum", "c_rostrum", "c_abdomen12"):
            assert (geom.mass, geom.meshname) == (mass, mesh)
    for name, properties in before_joints:
        joint = fly.mjcf_root.joint(name)
        np.testing.assert_array_equal(properties, np.r_[joint.axis, joint.stiffness, joint.damping, joint.armature])
    for name, pos, quat in before_bodies:
        body = fly.mjcf_root.body(name)
        np.testing.assert_array_equal(pos, body.pos)
        np.testing.assert_array_equal(quat, body.quat)
    try:
        add_proboscis_muscles(fly)
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("Duplicate mechanics were accepted")

    lookup = {(r["side"], r["muscle_target"]): r for r in records}
    p = json.loads(M9_CONFIG.read_text())
    for target in MUSCLE_TARGETS:
        left, right = lookup["left", target], lookup["right", target]
        for ls, rs in zip(left["sites"], right["sites"]):
            np.testing.assert_allclose(ls["pos_mm"], np.asarray(rs["pos_mm"]) * [1, -1, 1], atol=1e-12)
    np.testing.assert_array_equal(lookup["right", "m9"]["sites"][0]["pos_mm"], p["origin_head_mm"])
    np.testing.assert_array_equal(lookup["right", "m9"]["sites"][1]["pos_mm"], p["insertion_rostrum_mm"])
    for r in records:
        assert r["mapping_status"] == "unmapped" and not r["motor_neuron_ids"]
        if r["limb"] == "proboscis":
            assert r["semantic_muscle_key"] == "proboscis." + r["muscle_target"]
        else:
            assert r["side"] == "unpaired" and r["peripheral_target_topology"] == "unpaired_organ_group"
            assert r["semantic_muscle_key"] == "gut.crop_entry_muscles" and not r["peripheral_target_sides"]
        assert r["muscle_target"] not in UNIMPLEMENTED_TARGETS
        assert r["optimal_fiber_length_mm"] > 0 and r["tendon_length_mm"] > 0
        np.testing.assert_allclose(r["activation_time_s"], (0.01, 0.04))
    for side in ("left", "right"):
        assert sum(lookup[side, t]["force_uN"] for t in ("m3L", "m3M")) == 28
    motor_bindings = check_motor_bindings(records)

    # Test world-qualified names after real FlyGym attachment, entirely in memory.
    world = TetheredWorld(name="isolated_proboscis_mechanics")
    world.add_fly(fly, [0, 0, 0], Rotation3D("quat", [1, 0, 0, 0]))
    spec = world.mjcf_root.copy()
    spec.compiler.fusestatic = False
    spec.option.integrator = mj.mjtIntegrator.mjINT_IMPLICITFAST
    spec.option.gravity = (0, 0, 0)  # Isolate muscle forces from whole-body weight.
    model = spec.compile()
    data = mj.MjData(model)
    key = model.key("neutral").id
    mj.mj_resetDataKeyframe(model, data, key)
    mj.mj_forward(model, data)
    assert model.nu == model.na == model.ntendon == 35 and model.neq == 0
    np.testing.assert_allclose(model.body_mass.sum(), before_mass, atol=1e-15)
    for name in LABELLUM_GEOMS:
        assert model.geom(f"{fly.name}/{name}").bodyid == model.body(f"{fly.name}/{name}").id
    new_surface = np.concatenate([mesh_points_in_body(model, data, f"{fly.name}/{name}", f"{fly.name}/c_haustellum")
                                  for name in ("c_haustellum", *LABELLUM_GEOMS)])
    # This assay uses the bundled <=2000-face mesh; compare the entire old/new surface.
    distances = np.linalg.norm(original_surface[:, None, :] - new_surface[None, :, :], axis=2)
    surface_error = float(max(distances.min(axis=0).max(), distances.min(axis=1).max()))
    assert surface_error < 2e-7, surface_error
    assert (model.actuator_trntype == mj.mjtTrn.mjTRN_TENDON).all()
    assert (model.actuator_dyntype == mj.mjtDyn.mjDYN_MUSCLE).all()
    assert (model.actuator_gaintype == mj.mjtGain.mjGAIN_MUSCLE).all()
    assert (model.actuator_biastype == mj.mjtBias.mjBIAS_MUSCLE).all()
    assert (model.actuator_ctrlrange == (0, 1)).all() and (model.actuator_actrange == (0, 1)).all()
    assert model.actuator_ctrllimited.all() and model.actuator_actlimited.all()
    assert np.unique(model.actuator_actadr).size == 35
    assert not data.ctrl.any() and not data.act.any()
    np.testing.assert_allclose(data.actuator_force, 0, atol=1e-20)
    q0 = data.qpos.copy()
    ids = [model.actuator(r["actuator_name"]).id for r in records]
    joints = [model.joint(f"{fly.name}/{name}") for name in JOINT_NAMES.values()]
    dofs, addresses = [int(j.dofadr[0]) for j in joints], [int(j.qposadr[0]) for j in joints]
    assert not model.jnt_stiffness[[j.id for j in joints]].any()
    np.testing.assert_array_equal(q0[addresses], 0)

    # Inferred native fiber and tendon calibration must match the declared values.
    inferred_l0 = np.diff(model.actuator_lengthrange, axis=1)[:, 0] / np.diff(model.actuator_gainprm[:, :2], axis=1)[:, 0]
    inferred_lt = model.actuator_lengthrange[:, 0] - model.actuator_gainprm[:, 0] * inferred_l0
    np.testing.assert_allclose(inferred_l0[ids], [r["optimal_fiber_length_mm"] for r in records], atol=1e-14)
    np.testing.assert_allclose(inferred_lt[ids], [r["tendon_length_mm"] for r in records], atol=1e-14)
    assert (inferred_l0 > 0).all() and (inferred_lt > 0).all()

    # Unit-tension torque = -d(length)/dq; signs are anatomical, not a motion goal.
    expected_signs = {"m1": (1, 0), "m2D": (1, 0), "m2V": (1, -1),
                      "m3L": (0, -1), "m3M": (0, -1), "m4": (0, 1), "m9": (-1, 0)}
    arms = -moments(model, data)[:, dofs]
    for r, i in zip(records, ids):
        for value, sign in zip(arms[i], expected_signs.get(r["muscle_target"], (0, 0))):
            assert abs(value) < 1e-12 if sign == 0 else value * sign > 1e-4
    neutral_arms = {r["muscle_target"]: arms[i].tolist() for r, i in zip(records, ids) if r["side"] == "right"}

    # Sweep the declared mechanical stops. Compare the geometric Jacobian to a
    # central difference and require strictly positive *actual* fiber lengths.
    epsilon, max_error, min_fiber = 1e-6, 0.0, float("inf")
    for qr in np.linspace(*joints[0].range, 15):
        for qh in np.linspace(*joints[1].range, 15):
            data.qpos[:] = q0
            data.qpos[addresses] = (qr, qh)
            mj.mj_forward(model, data)
            jacobian = moments(model, data)
            min_fiber = min(min_fiber, float(np.min(data.actuator_length - inferred_lt)))
            assert np.isfinite(data.actuator_length).all()
            leg_dofs = [model.joint(f"{fly.name}/{name}").dofadr[0] for name, _ in before_joints]
            assert np.max(abs(jacobian[:, leg_dofs])) < 1e-12
            for dof, address in zip(dofs, addresses):
                reference = data.qpos[address]
                lengths = []
                for delta in (epsilon, -epsilon):
                    data.qpos[address] = reference + delta
                    mj.mj_forward(model, data)
                    lengths.append(data.actuator_length.copy())
                data.qpos[address] = reference
                derivative = (lengths[0] - lengths[1]) / (2 * epsilon)
                max_error = max(max_error, float(np.max(abs(derivative - jacobian[:, dof]))))
    assert min_fiber > 0 and max_error < 1e-7

    # New structures: correct muscle directions, passive recoil, and positive
    # lengths throughout sampled combinations of all 18 anatomical coordinates.
    data.qpos[:] = q0
    mj.mj_forward(model, data)
    jacobian = moments(model, data)
    new_joints = [model.joint(i) for i in range(model.njnt)
                  if model.joint(i).name.startswith((f"{fly.name}/proboscis_", f"{fly.name}/gut_"))]
    for r, i in zip(records, ids):
        t = r["muscle_target"]
        if t in ("m6", "m7"):
            key_name = "extension" if t == "m6" else "abduction"
            assert -jacobian[i, model.joint(r["joint_names"][key_name]).dofadr[0]] > 1e-5
        elif t in PUMP_TARGETS + ("m13",):
            assert -jacobian[i, model.joint(r["joint_names"]["dilation"]).dofadr[0]] > 0.1
        elif r["limb"] == "gut":
            assert all(-jacobian[i, model.joint(j).dofadr[0]] < -0.1 for j in r["joint_names"].values())
    rng = np.random.default_rng(42)
    for _ in range(100):
        data.qpos[:] = q0
        for joint in new_joints:
            data.qpos[joint.qposadr[0]] = rng.uniform(*joint.range)
        mj.mj_forward(model, data)
        min_fiber = min(min_fiber, float(np.min(data.actuator_length - inferred_lt)))
    assert min_fiber > 0
    for joint in new_joints:
        if model.jnt_stiffness[joint.id] > 0:
            data.qpos[:], data.qvel[:] = q0, 0
            data.qpos[joint.qposadr[0]] = 0.002
            mj.mj_forward(model, data)
            assert data.qfrc_passive[joint.dofadr[0]] < 0

    # One activated unit at a time: native force and generalized force must agree
    # with the constitutive law and physical site geometry, including M2V coupling.
    data.qpos[:], data.qvel[:] = q0, 0
    for r, i in zip(records, ids):
        data.act[:] = 0
        data.act[model.actuator_actadr[i]] = 0.4
        mj.mj_forward(model, data)
        force = 0.4 * mj.mju_muscleGain(data.actuator_length[i], 0,
            model.actuator_lengthrange[i], model.actuator_acc0[i], model.actuator_gainprm[i, :9])
        assert force < 0
        np.testing.assert_allclose(data.actuator_force[i], force, atol=1e-12)
        np.testing.assert_allclose(data.qfrc_actuator, moments(model, data)[i] * force, atol=1e-12)
        assert np.count_nonzero(data.act) == 1
    data.act[:] = 0.3
    data.qvel[dofs] = (0.07, -0.11)
    mj.mj_forward(model, data)
    np.testing.assert_allclose(data.actuator_velocity, moments(model, data) @ data.qvel, atol=1e-12)
    np.testing.assert_allclose(data.qfrc_actuator @ data.qvel, data.actuator_force @ data.actuator_velocity, atol=1e-12)

    def pulse(index, dt, excitation):
        model.opt.timestep = dt
        d = mj.MjData(model)
        mj.mj_resetDataKeyframe(model, d, key)
        adr, peak = model.actuator_actadr[index], 0.0
        for tick in range(round(0.08 / dt)):
            # Deliberate out-of-range values verify the native excitation clamp.
            d.ctrl[index] = excitation if tick < round(0.04 / dt) else -1
            mj.mj_step(model, d)
            assert np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all()
            assert ((d.act >= 0) & (d.act <= 1)).all()
            assert not np.delete(d.act, adr).any()  # No contralateral/cross-muscle drive.
            peak = max(peak, float(d.act[adr]))
        assert not any(w.number for w in d.warning)
        return d, peak

    peaks = []
    for i in ids:
        result, peak = pulse(i, 1e-5, 2)
        assert 0 < result.act[model.actuator_actadr[i]] < peak <= 1
        peaks.append(peak)
    i = model.actuator(lookup["right", "m9"]["actuator_name"]).id
    coarse, _ = pulse(i, 1e-5, 2)
    clipped, _ = pulse(i, 1e-5, 1)
    fine, _ = pulse(i, 5e-6, 2)
    quiet, quiet_peak = pulse(i, 1e-5, 0)
    np.testing.assert_array_equal(coarse.act, clipped.act)
    np.testing.assert_array_equal(coarse.qpos, clipped.qpos)
    assert quiet_peak == 0 and not quiet.act.any()
    q_error = float(np.max(abs(coarse.qpos[addresses] - fine.qpos[addresses])))
    a_error = float(np.max(abs(coarse.act - fine.act)))
    assert q_error < 0.005 and a_error < 0.005
    assert np.max(abs(coarse.qpos[addresses] - quiet.qpos[addresses])) > 1e-6
    hydraulics = check_hydraulics(model, fly.name)
    return dict(status="PASS", scope="isolated constitutive mechanics; no feeding behavior validation",
        units="mm-g-s; force uN; hinge torque nN m", added_dofs=18, muscles=len(records),
        total_mass_error_g=float(model.body_mass.sum() - before_mass),
        max_reference_surface_vertex_error_mm=surface_error,
        labellar_contact_geoms=[f"{fly.name}/{n}" for n in LABELLUM_GEOMS],
        targets_per_side=list(MUSCLE_TARGETS), native_activation_states=model.na,
        min_sampled_fiber_length_mm=min_fiber, max_jacobian_error_mm_per_rad=max_error,
        right_unit_tension_moment_arms_mm=neutral_arms, pulse_peak_activation=min(peaks),
        half_dt_max_qpos_error_rad=q_error, half_dt_max_activation_error=a_error,
        unimplemented_targets=UNIMPLEMENTED_TARGETS, motor_neuron_links_created=0,
        motor_binding_audit=motor_bindings, hydraulics=hydraulics)


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
