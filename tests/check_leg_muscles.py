"""CPU-only constitutive-mechanics check; no brain, behavior policy or live app.

Run: MUJOCO_GL=disable .venv/bin/python -B check_leg_muscles.py
Diagnostic excitation below is confined to this assay, never supplied by importer.
"""
from collections import Counter, defaultdict
import json

import mujoco as mj
import numpy as np
from flygym import Simulation
from flygym.anatomy import AxisOrder, JointPreset, Skeleton
from flygym.compose import KinematicPosePreset, NeuroMechFly, TetheredWorld
from flygym.utils.math import Rotation3D

from leg_muscles import ACCESSORY_FIBERS, MUSCLES, XNH_TO_DONOR, _mesh_in_body, _segment_frame, _source_geometry, add_leg_muscles


def moments(model, data):
    matrix = np.zeros((model.nu, model.nv))
    for i in range(model.nu):
        start, count = data.moment_rowadr[i], data.moment_rownnz[i]
        matrix[i, data.moment_colind[start:start + count]] = data.actuator_moment[start:start + count]
    return matrix


def check():
    fly = NeuroMechFly(name="leg_check")
    fly.add_joints(Skeleton(axis_order=AxisOrder.YAW_PITCH_ROLL, joint_preset=JointPreset.LEGS_ONLY),
        KinematicPosePreset.NEUTRAL, stiffness=0, damping=0.02, armature=1e-6)
    # This assay uses viscous damping, no angle-restoring spring or angle actuator.
    before_joints = [(j.name, *[np.asarray(v).copy() for v in (j.axis, j.stiffness, j.damping, j.armature)])
        for j in fly.mjcf_root.joints]
    baseline_spec = fly.mjcf_root.copy(); baseline_spec.compiler.fusestatic = False
    baseline_model = baseline_spec.compile(); baseline_data = mj.MjData(baseline_model)
    mj.mj_kinematics(baseline_model, baseline_data)
    baseline_vertices = {}
    for limb in ("lf", "lm", "lh", "rf", "rm", "rh"):
        for suffix in ("trochanterfemur", "tarsus5"):
            name = f"{limb}_{suffix}"
            vertices, _ = _mesh_in_body(baseline_model, baseline_data, name)
            b = baseline_data.body(name)
            baseline_vertices[name] = vertices @ b.xmat.reshape(3, 3).T + b.xpos
    records = add_leg_muscles(fly)
    assert Counter(r["limb"] for r in records) == dict(lf=24, rf=24, lm=22, rm=22, lh=21, rh=21)
    assert len({r["actuator_name"] for r in records}) == 134
    assert all(r["target_muscle"] is not None for r in records)
    assert not any("sterno_tergo_trochanter_extensor" in r["muscle_name"] for r in records)
    for old in before_joints:
        joint = fly.mjcf_root.joint(old[0])
        assert old[0] == joint.name and np.array_equal(old[1], joint.axis)
        for prior, current in zip(old[2:], (joint.stiffness, joint.damping, joint.armature)):
            np.testing.assert_array_equal(prior, current)
    try:
        add_leg_muscles(fly)
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("Duplicate import was accepted")
    assert len(list(fly.mjcf_root.actuators)) == 134

    capacities = defaultdict(float)
    for r in records:
        capacities[r["limb"], r["muscle_group"]] += r["force_uN"]
        assert r["mapping_status"] == "unmapped" and not r["motor_neuron_ids"]
        assert r["tendon_length_mm"] >= 0 and r["optimal_fiber_length_mm"] > 0
        assert r["peripheral_limb"] == r["limb"]
        assert r["physics_max_timestep_s"] == 1e-5
        if r["limb"][1] != "f":
            assert r["geometry_status"].startswith("estimated_")
            assert r["target_muscle"] and (r["homology_source"] or r["target_muscle"] == "TTM")
    np.testing.assert_allclose(list(capacities.values()), 28)

    # Mirror check at the ACTUAL body-local site coordinates, not name-based signs.
    lookup = {(r["limb"], r["muscle_name"]): r for r in records}
    for r in records:
        if r["side"] == "right":
            left = lookup["l" + r["limb"][1], r["muscle_name"]]
            for ls, rs in zip(left["sites"], r["sites"]):
                # Thoracic sites have different coxa anchoring; the full model's
                # bilateral rigging is symmetric across the thoracic sagittal plane.
                np.testing.assert_allclose(rs["pos_mm"], np.asarray(ls["pos_mm"]) * [1, -1, 1], atol=2e-7)

    # Independent source-frame check: retain the nonzero trochanter-to-femur
    # translation. Directly copying source femur-local site coordinates would fail.
    sm, sd, paths = _source_geometry()
    point = sd.site_xpos[sm.site(paths["LFTibia_flex_93434"][0]).id]
    relative = sd.body("LFTrochanter").xmat.reshape(3, 3).T @ (point - sd.body("LFTrochanter").xpos)
    np.testing.assert_allclose(relative, sm.body("LFFemur").pos + sm.site(paths["LFTibia_flex_93434"][0]).pos, atol=1e-12)
    assert np.linalg.norm(relative - sm.site(paths["LFTibia_flex_93434"][0]).pos) > 0.09
    source_distal = sd.body("LFTrochanter").xmat.reshape(3, 3).T @ (sd.body("LFTibia").xpos - sd.body("LFTrochanter").xpos)
    structure = lookup["lf", "sternotrochanter"]["structures"]
    offset = np.asarray(structure["femur_offset_mm"])
    target_distal = fly.bodyseg_to_mjcfbody[next(b for b in fly.bodyseg_to_mjcfbody if b.name == "lf_tibia")].pos + offset
    target_point = np.asarray(lookup["lf", "tibia_flexor"]["sites"][0]["pos_mm"]) + offset
    ratio = np.linalg.norm(target_distal) / np.linalg.norm(source_distal)
    # A similarity registration must preserve distances to BOTH joint landmarks.
    np.testing.assert_allclose(np.linalg.norm(target_point), ratio * np.linalg.norm(relative), atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(target_point - target_distal),
        ratio * np.linalg.norm(relative - source_distal), atol=1e-12)
    basis, length = _segment_frame(np.zeros(3), np.array([1., 2., -3.]), np.array([0., 1., 0.]))
    np.testing.assert_allclose(basis.T @ basis, np.eye(3), atol=1e-12)
    assert abs(np.linalg.det(basis) - 1) < 1e-12 and length > 0

    # The new ATF paths have independent tendon attachments; primary 3D skeleton
    # IDs are provenance, never motor IDs. Pin the nm -> mm and donor-frame transfer.
    for region, sid, digest, node_ids, raw in ACCESSORY_FIBERS:
        rec = lookup["lf", f"accessory_tibia_flexor_{region}"]
        assert rec["target_muscle"] == "Acc. ti flexor" and rec["source_skeleton_id"] == sid
        assert rec["source_sha256"] == digest and rec["subdivision_mapping_required"]
        assert rec["force_uN"] == 14 and len(rec["sites"]) == 2
        for i, site in enumerate(rec["sites"]):
            rot, offset = XNH_TO_DONOR[i]
            np.testing.assert_allclose(rot @ rot.T, np.eye(3), atol=3e-12)
            np.testing.assert_allclose(site["source_pos_mm"], rot @ (np.asarray(raw[i]) / 1e6) + offset, atol=1e-12)
            assert site["source_node_id"] == node_ids[i]
        assert rec["sites"][1]["attachment_status"] == "estimated_rigid_tibia_apodeme_endpoint"
    assert len({lookup['lf', 'accessory_tibia_flexor_' + region]['local_tendon_name'] for region in ('anterior', 'posterior')}) == 2
    for muscle in ("tarsus_levator", "tarsus_depressor"):
        rec = lookup["lf", muscle]
        assert [s["body"] for s in rec["sites"]] == ["lf_tibia", "lf_tarsus1"]
        assert all(s["source_pos_mm"] is None for s in rec["sites"])
        assert rec["geometry_status"] == "estimated_bone_surface_geometry"

    world = TetheredWorld(name="isolated_leg_mechanics")
    world.add_fly(fly, [0, 0, 0], Rotation3D("quat", [1, 0, 0, 0]))
    world.mjcf_root.compiler.fusestatic = False
    world.mjcf_root.option.integrator = mj.mjtIntegrator.mjINT_IMPLICITFAST
    sim = Simulation(world)
    model, data = sim.mj_model, sim.mj_data
    key = model.key("neutral").id
    mj.mj_forward(model, data)
    assert model.nu == model.na == model.ntendon == 134 and model.nq == 90
    assert (model.actuator_trntype == mj.mjtTrn.mjTRN_TENDON).all()
    assert (model.actuator_dyntype == mj.mjtDyn.mjDYN_MUSCLE).all()
    assert (model.actuator_gainprm[:, :2] == [0, 1]).all()
    assert (model.actuator_lengthrange[:, 0] >= 0).all()
    assert np.unique(model.actuator_actadr).size == 134  # parent later splits by actual MN
    for rec in records:
        i = model.actuator(rec["actuator_name"]).id
        np.testing.assert_allclose(model.actuator_lengthrange[i],
            [rec["tendon_length_mm"], rec["tendon_length_mm"] + rec["optimal_fiber_length_mm"]], atol=1e-12)
        if rec["target_muscle"] in ("ltm1-tibia", "ltm2-femur"):
            assert rec["tendon_length_mm"] > 0 and rec["shared_apodeme"]
    structural_joints = {j for r in records for j in r.get("structural_joint_names", [])}
    contacts = {g for r in records for g in r.get("contact_geom_names", [])}
    assert len(structural_joints) == 24 and len(contacts) == 12
    for name in structural_joints:
        assert model.joint(name).id >= 0
    for name in contacts:
        assert model.geom(name).id >= 0
    jump = [r for r in records if r["target_muscle"] == "TTM"]
    assert {r["limb"] for r in jump} == {"lm", "rm"}
    assert all(r["semantic_muscle_key"] == "wing.tergotrochanteral_jump" for r in jump)
    assert all(r["sites"][0]["body"] == "c_thorax" for r in jump)
    assert not data.ctrl.any() and not data.act.any()
    np.testing.assert_allclose(data.actuator_force, 0, atol=1e-20)
    neutral = data.qpos.copy()
    jacobian = moments(model, data)
    assert (np.linalg.norm(jacobian, axis=1) > 1e-5).all()

    # Partitioning must preserve the original cuticle surface at reference q=0.
    reference = mj.MjData(model); mj.mj_kinematics(model, reference)
    surface_error = 0.0
    for name, old in baseline_vertices.items():
        limb, segment = name.split("_", 1)
        extra = f"leg_muscle_{limb}_" + ("trochanter_geom" if segment == "trochanterfemur" else "pretarsal_geom")
        points = []
        for geom_name in ("leg_check/" + name, "leg_check/" + extra):
            g = reference.geom(geom_name); mid = model.geom(geom_name).dataid[0]
            v0, count = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
            points.extend(model.mesh_vert[v0:v0 + count] @ g.xmat.reshape(3, 3).T + g.xpos)
        distance = np.linalg.norm(np.asarray(points)[:, None, :] - old[None, :, :], axis=2)
        surface_error = max(surface_error, float(distance.min(0).max()), float(distance.min(1).max()))
    assert surface_error < 2e-6

    epsilon, max_jacobian_error = 1e-6, 0.0
    for dof in range(model.nv):
        address = model.jnt_qposadr[model.dof_jntid[dof]]
        lengths = []
        for delta in (epsilon, -epsilon):
            data.qpos[:] = neutral
            data.qpos[address] += delta
            mj.mj_forward(model, data)
            lengths.append(data.actuator_length.copy())
        derivative = (lengths[0] - lengths[1]) / (2 * epsilon)
        max_jacobian_error = max(max_jacobian_error, float(np.max(abs(derivative - jacobian[:, dof]))))
    assert max_jacobian_error < 1e-7

    # Geometric signs are measured here, never enforced by an action controller.
    mj.mj_resetDataKeyframe(model, data, key)
    mj.mj_forward(model, data)
    jacobian = moments(model, data)
    tibia_arms = {}
    distal_arms = {}
    for limb in ("lf", "lm", "lh", "rf", "rm", "rh"):
        dof = model.joint(f"leg_check/{limb}_trochanterfemur-{limb}_tibia-pitch").dofadr[0]
        a, b = [model.actuator(lookup[limb, muscle]["actuator_name"]).id for muscle in ("tibia_flexor", "tibia_extensor")]
        assert jacobian[a, dof] * jacobian[b, dof] < 0
        tibia_arms[limb] = [-float(jacobian[a, dof]), -float(jacobian[b, dof])]
        accessory = [model.actuator(lookup[limb, "accessory_tibia_flexor_" + region]["actuator_name"]).id
                     for region in ("anterior", "posterior")]
        assert all(jacobian[i, dof] * jacobian[a, dof] > 0 for i in accessory)
        tarsus_dof = model.joint(f"leg_check/{limb}_tibia-{limb}_tarsus1-pitch").dofadr[0]
        lev, dep = [model.actuator(lookup[limb, name]["actuator_name"]).id for name in ("tarsus_levator", "tarsus_depressor")]
        # Published action and geometry agree at neutral: levator flexes the
        # already negatively flexed tarsus; depressor extends towards straight.
        assert -jacobian[lev, tarsus_dof] < 0 < -jacobian[dep, tarsus_dof]
        distal_arms[limb] = dict(accessory_flexor=[-float(jacobian[i, dof]) for i in accessory],
            tarsus_levator=-float(jacobian[lev, tarsus_dof]), tarsus_depressor=-float(jacobian[dep, tarsus_dof]))
        claw = model.joint(f"leg_check/leg_muscle_{limb}_pretarsal_flexion").dofadr[0]
        ltm1, ltm2 = [model.actuator(lookup[limb, name]["actuator_name"]).id for name in ("ltm1_tibia", "ltm2_femur_proximal")]
        assert -jacobian[ltm1, claw] > 0 and -jacobian[ltm2, claw] > 0
        assert abs(jacobian[ltm1, dof]) < 1e-12 and abs(jacobian[ltm2, dof]) > 1e-5
        distal_arms[limb]["long_tendon_claw"] = -float(jacobian[ltm1, claw])
        for region in ("1", "2"):
            i = model.actuator(lookup[limb, "femur_reductor_" + region]["actuator_name"]).id
            own = [model.joint(f"leg_check/leg_muscle_{limb}_femur_compliance_{a}").dofadr[0] for a in "xyz"]
            assert np.linalg.norm(jacobian[i, own]) > 1e-5
            assert np.linalg.norm(np.delete(jacobian[i], own)) < 1e-10
        stern, terg = [lookup[limb, n] for n in ("sternotrochanter", "tergotrochanter")]
        assert stern["sites"][0]["pos_mm"][2] < terg["sites"][0]["pos_mm"][2]
        assert [s["body"] for s in stern["sites"]] == ["c_thorax", f"{limb}_coxa", f"leg_muscle_{limb}_trochanter"]

    data.qvel[:] = np.linspace(-0.02, 0.03, model.nv)
    data.act[:] = 0.3  # isometric/velocity constitutive-law probe, not a runtime input
    mj.mj_forward(model, data)
    expected_force = []
    for i in range(model.nu):
        gain = mj.mju_muscleGain(data.actuator_length[i], data.actuator_velocity[i],
            model.actuator_lengthrange[i], model.actuator_acc0[i], model.actuator_gainprm[i, :9])
        bias = mj.mju_muscleBias(data.actuator_length[i], model.actuator_lengthrange[i],
            model.actuator_acc0[i], model.actuator_biasprm[i, :9])
        expected_force.append(data.act[model.actuator_actadr[i]] * gain + bias)
    np.testing.assert_allclose(data.actuator_force, expected_force, atol=1e-12)
    matrix = moments(model, data)
    np.testing.assert_allclose(data.qfrc_actuator, matrix.T @ data.actuator_force, atol=1e-12)
    np.testing.assert_allclose(data.actuator_velocity, matrix @ data.qvel, atol=1e-12)
    assert abs(data.qfrc_actuator @ data.qvel - data.actuator_force @ data.actuator_velocity) < 1e-12

    # Exercise the reported contact API in a separate copy. No pairs are added
    # by the muscle module: main owns world contacts, as this fixture does here.
    claw_name = "leg_check/leg_muscle_lf_pretarsal_geom"
    geom = data.geom(claw_name); mid = model.geom(claw_name).dataid[0]
    v0, count = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
    vertices = model.mesh_vert[v0:v0 + count] @ geom.xmat.reshape(3, 3).T + geom.xpos
    plane_height = float(vertices[:, 2].min() + 0.002)
    contact_spec = world.mjcf_root.copy()
    contact_spec.worldbody.add_geom(name="contact_probe_plane", type=mj.mjtGeom.mjGEOM_PLANE,
        pos=(0, 0, plane_height), size=(100, 100, 1), contype=0, conaffinity=0)
    contact_spec.add_pair(name="new_claw_contact", geomname1=claw_name, geomname2="contact_probe_plane")
    contact_model = contact_spec.compile(); contact_data = mj.MjData(contact_model)
    mj.mj_resetDataKeyframe(contact_model, contact_data, contact_model.key("neutral").id)
    mj.mj_forward(contact_model, contact_data)
    contact_force = 0.0
    for i, contact in enumerate(contact_data.contact):
        if contact_model.geom(claw_name).id in contact.geom:
            force = np.zeros(6); mj.mj_contactForce(contact_model, contact_data, i, force)
            contact_force += force[0]
    assert contact_force > 0

    def integrate(dt, excitation):
        model.opt.timestep = dt
        d = mj.MjData(model)
        mj.mj_resetDataKeyframe(model, d, key)
        peak = 0.0
        for tick in range(round(0.12 / dt)):
            # Uniform assay pulse stresses all mechanics without choosing an action.
            d.ctrl[:] = excitation if round(0.01 / dt) <= tick < round(0.06 / dt) else 0
            mj.mj_step(model, d)
            assert np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all()
            assert ((0 <= d.act) & (d.act <= 1)).all()
            peak = max(peak, float(d.act.max()))
        assert not any(w.number for w in d.warning)
        return d, peak

    quiet, quiet_peak = integrate(1e-4, 0)
    assert quiet_peak == 0 and not quiet.act.any()
    coarse100, peak = integrate(1e-4, 1)
    fine50, _ = integrate(5e-5, 1)
    coarse_error = float(np.max(abs(coarse100.qpos - fine50.qpos)))
    # Keep the original angular tolerance at the explicitly required physics
    # resolution. 100 us remains a separate finite-state stress check, not a pass
    # for integration accuracy. Do not weaken force curves to satisfy this test.
    coarse, _ = integrate(1e-5, 1)
    fine, _ = integrate(5e-6, 1)
    q_error = float(np.max(abs(coarse.qpos - fine.qpos)))
    a_error = float(np.max(abs(coarse.act - fine.act)))
    assert peak > 0 and q_error < 0.003 and a_error < 0.005
    assert np.linalg.norm(coarse.qpos - quiet.qpos) > 1e-6
    return dict(status="PASS", scope="constitutive leg mechanics only; no normal-fly behavior claim",
        units="mm-g-s; force uN; hinge torque nN m", coverage=dict(Counter(r["limb"] for r in records)),
        total_units=len(records), native_activation_states=model.na, geometric_tendons=model.ntendon,
        sites=sum(len(r["sites"]) for r in records), unbound_prototype_records=len(records),
        skipped_paths_per_middle_or_hind_leg=[x[1] for x in MUSCLES if not x[3] and x[2] is not None],
        added_structural_joints=len(structural_joints), contact_geoms=len(contacts),
        isolated_claw_contact_normal_force_uN=float(contact_force),
        cuticle_reference_max_error_mm=surface_error,
        compiled_mass_change_g=float(model.body_mass.sum() - baseline_model.body_mass.sum()),
        required_physics_timestep_s=1e-5,
        coarse_100us_half_dt_error_rad=coarse_error,
        coarse_100us_angular_precision="not_qualified_to_0.003_rad",
        max_jacobian_error_mm_per_rad=max_jacobian_error, tibia_tension_moment_arms_mm=tibia_arms,
        added_distal_tension_moment_arms_mm=distal_arms,
        pulse_peak_activation=peak, half_dt_max_qpos_error_rad=q_error,
        half_dt_max_activation_error=a_error, numerical_warnings=0)


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
