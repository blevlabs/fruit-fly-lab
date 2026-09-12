"""CPU-only neck, antenna and retinal mechanics checks. No sensory/behavior policy.

Run: MUJOCO_GL=disable .venv/bin/python -B check_head_muscles.py
"""
from collections import Counter
import json

import mujoco as mj
import numpy as np
from flygym.anatomy import AxisOrder, BodySegment, JointPreset, Skeleton
from flygym.compose import KinematicPosePreset, NeuroMechFly, TetheredWorld
from flygym.utils.math import Rotation3D

from check_proboscis_muscles import check_motor_bindings, moments
from head_muscles import HEAD_JOINTS, SUPPORT_JOINTS, add_head_muscles
from proboscis_muscles import add_proboscis_muscles


def check():
    fly = NeuroMechFly(name="head_check")
    fly.add_joints(Skeleton(axis_order=AxisOrder.YAW_PITCH_ROLL, joint_preset=JointPreset.LEGS_ONLY),
        KinematicPosePreset.NEUTRAL, stiffness=0.04, damping=0.02, armature=1e-6)
    old_bodies = dict(fly.bodyseg_to_mjcfbody)
    old_joints = {j.name: np.r_[j.axis, j.stiffness, j.damping, j.armature] for j in fly.mjcf_root.joints}
    source = fly.mjcf_root.copy()
    source.compiler.fusestatic = False
    mass = float(source.compile().body_mass.sum())
    for options in ({"group_force_uN": -1}, {"activation_time_s": (0.01, 0)},
                    {"activation_time_s": (1e-5, 4e-5)}, {"sensory_force_uN": float("nan")}):
        try:
            add_head_muscles(fly, **options)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid force or activation parameters accepted")
        assert len(fly.mjcf_root.joints) == len(old_joints)
    records = add_head_muscles(fly)
    assert Counter(r["limb"] for r in records) == dict(neck=12, antenna=8, retina=4)
    assert len(fly.mjcf_root.joints) == len(old_joints) + 15
    for segment, body in old_bodies.items():
        assert fly.bodyseg_to_mjcfbody[segment] is body
    for name, prior in old_joints.items():
        joint = fly.mjcf_root.joint(name)
        np.testing.assert_array_equal(prior, np.r_[joint.axis, joint.stiffness, joint.damping, joint.armature])
    for side in ("l", "r"):
        assert not list(fly.bodyseg_to_mjcfbody[BodySegment(f"{side}_eye")].joints)
    try:
        add_head_muscles(fly)
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("Duplicate mechanics accepted")
    # Exercise standard composition APIs after adding the internal anatomy.
    fly.colorize()
    fly.add_tracking_camera(name="check_cam")
    world = TetheredWorld(name="head_component_assay")
    world.add_fly(fly, [0, 0, 0], Rotation3D("quat", [1, 0, 0, 0]))
    spec = world.mjcf_root.copy()
    spec.compiler.fusestatic = False
    spec.option.gravity = (0, 0, 0)
    spec.option.integrator = mj.mjtIntegrator.mjINT_IMPLICITFAST
    spec.option.timestep = 1e-5
    spec.option.jacobian = mj.mjtJacobian.mjJAC_DENSE
    model = spec.compile()
    data = mj.MjData(model)
    key = model.key("neutral").id
    mj.mj_resetDataKeyframe(model, data, key)
    mj.mj_forward(model, data)
    assert model.nu == model.na == model.ntendon == 24 and model.neq == 2
    np.testing.assert_allclose(model.body_mass.sum(), mass, atol=1e-15)
    np.testing.assert_allclose(data.efc_pos[:6], 0, atol=1e-12)
    assert np.linalg.matrix_rank(data.efc_J.reshape(-1, model.nv)[:6], tol=1e-10) == 2
    q0 = data.qpos.copy()
    assert not data.act.any() and not data.ctrl.any()
    np.testing.assert_allclose(data.actuator_force, 0, atol=1e-20)
    assert (model.actuator_trntype == mj.mjtTrn.mjTRN_TENDON).all()
    assert (model.actuator_dyntype == mj.mjtDyn.mjDYN_MUSCLE).all()
    np.testing.assert_array_equal(model.actuator_dynprm[:, :2], np.tile((0.01, 0.04), (24, 1)))
    for r in records:
        assert not r["motor_neuron_ids"] and r["mapping_status"] == "unmapped"
        i = model.actuator(r["actuator_name"]).id
        assert abs(data.actuator_length[i] - r["reference_length_mm"]) < 1e-10
        assert r["optimal_fiber_length_mm"] > 0 and r["tendon_length_mm"] > 0
    ids = [model.actuator(r["actuator_name"]).id for r in records]
    lt = np.zeros(model.nu)
    lt[ids] = [r["tendon_length_mm"] for r in records]
    jac = moments(model, data)
    assert (np.linalg.norm(jac, axis=1) > 1e-5).all()
    max_error = 0.0
    for j in range(model.njnt):
        joint = model.joint(j)
        address, dof = int(joint.qposadr[0]), int(joint.dofadr[0])
        lengths = []
        for delta in (1e-6, -1e-6):
            data.qpos[:] = q0
            data.qpos[address] += delta
            mj.mj_forward(model, data)
            lengths.append(data.actuator_length.copy())
        max_error = max(max_error, float(np.max(abs((lengths[0] - lengths[1]) / 2e-6 - jac[:, dof]))))
    assert max_error < 1e-7
    data.qpos[:], data.qvel[:] = q0, 0
    data.act[:] = 0.3
    mj.mj_forward(model, data)
    np.testing.assert_allclose(data.qfrc_actuator, moments(model, data).T @ data.actuator_force, atol=1e-12)
    assert (data.actuator_force < 0).all()
    rng = np.random.default_rng(4)
    new = [model.joint(i) for i in range(model.njnt)
           if model.joint(i).name.startswith((f"{fly.name}/neck_", f"{fly.name}/antenna_", f"{fly.name}/retina_"))]
    min_fiber = float("inf")
    for _ in range(100):
        data.qpos[:] = q0
        for joint in new:
            data.qpos[joint.qposadr[0]] = rng.uniform(*joint.range)
        # Sample anatomically compatible condylar poses, not broken joint closures.
        for head_name, support_name in zip(HEAD_JOINTS, SUPPORT_JOINTS):
            data.qpos[model.joint(f"{fly.name}/{support_name}").qposadr[0]] = data.qpos[model.joint(f"{fly.name}/{head_name}").qposadr[0]]
        mj.mj_forward(model, data)
        min_fiber = min(min_fiber, float(np.min(data.actuator_length - lt)))
    assert min_fiber > 0

    max_closure_error = 0.0
    ad_head_motion = []
    for r, i in zip(records, ids):
        mj.mj_resetDataKeyframe(model, data, key)
        for tick in range(2000):
            data.ctrl[i] = 2 if tick < 1000 else -1
            mj.mj_step(model, data)
            assert np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()
            assert ((data.act >= 0) & (data.act <= 1)).all()
            assert not np.delete(data.act, model.actuator_actadr[i]).any()
            max_closure_error = max(max_closure_error, float(np.max(abs(data.efc_pos[:6]))))
        assert data.act[model.actuator_actadr[i]] > 0 and not any(w.number for w in data.warning)
        if r["muscle_target"] in ("AD", "LEV"):
            ad_head_motion.append(abs(float(data.qpos[model.joint(f"{fly.name}/neck_head_roll").qposadr[0]])))
    assert min(ad_head_motion) > 1e-6 and max_closure_error < 0.005, (ad_head_motion, max_closure_error)

    # Both add orders compose; none replaces the fly object or the existing handles.
    for order in ((add_head_muscles, add_proboscis_muscles), (add_proboscis_muscles, add_head_muscles)):
        combined = NeuroMechFly(name="combined")
        metadata = order[0](combined) + order[1](combined)
        snapshot = combined.mjcf_root.copy()
        snapshot.compiler.fusestatic = False
        compiled = snapshot.compile()
        assert compiled.nu == compiled.na == compiled.ntendon == len(metadata) == 59
        assert compiled.neq == 2
    audit = check_motor_bindings(records, subclasses=("nm", "am", "rm"))
    bound = {r["bodyId"]: r["physical_side"] for r in audit["bindings"]}
    assert bound[10156] == "L" and bound[10754] == "R"  # CvN6/7 contralateral.
    return dict(status="PASS", neck_units=12, antennal_units=8, retinal_units=4,
        added_coordinates=15, independent_condylar_constraints=2,
        mass_error_g=float(model.body_mass.sum() - mass), min_sampled_fiber_length_mm=min_fiber,
        max_jacobian_error=max_error, max_condylar_position_error_mm=max_closure_error,
        smallest_AD_LEV_induced_head_roll_rad=min(ad_head_motion),
        motor_binding_audit=audit, scope="estimated constituent mechanics; no behavior or sensory-encoding validation")


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
