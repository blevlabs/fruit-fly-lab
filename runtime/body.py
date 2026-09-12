"""Shared NeuroMechFly scene for local rendering and workstation physics."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import mujoco
from flygym import Simulation
from flygym.anatomy import AxisOrder, BodySegment, ContactBodiesPreset, JointPreset, Skeleton
from flygym.compose import FlatGroundWorld, KinematicPosePreset, NeuroMechFly, TetheredWorld
from flygym.utils.math import Rotation3D
from arena import add_sources
from flygym_demo.complex_terrain import (
    HybridTurningController, LocomotionAction, PreprogrammedSteps,
    apply_locomotion_action, make_locomotion_fly,
)

PROBOSCIS_JOINT = 'fly/proboscis_pitch'
PROBOSCIS_ACTUATOR = 'fly/m9_right'
MUSCLE_CONFIG = Path(__file__).with_name('muscle9.json')


def muscle_parameters():
    p = json.loads(MUSCLE_CONFIG.read_text())
    for key in ('origin_head_mm', 'insertion_rostrum_mm'):
        if np.asarray(p[key]).shape != (3,) or not np.isfinite(p[key]).all():
            raise ValueError(f'Invalid {key}')
    positive = ('optimal_fiber_length_mm', 'force_uN', 'vmax', 'fpmax', 'fvmax')
    if any(not math.isfinite(p[k]) or p[k] <= 0 for k in positive):
        raise ValueError('Muscle lengths, forces and curve scales must be positive')
    nonnegative = ('tendon_length_mm', 'passive_stiffness_nNm_per_rad', 'passive_damping_nNm_s_per_rad')
    if any(not math.isfinite(p[k]) or p[k] < 0 for k in nonnegative):
        raise ValueError('Invalid tendon or passive joint parameter')
    if not (np.isfinite(p['joint_range_rad']).all() and p['joint_range_rad'][0] < 0 < p['joint_range_rad'][1]):
        raise ValueError('Invalid mechanical range')
    if not 0 < p['lmin'] < 1 < p['lmax'] or any(not math.isfinite(t) or t <= 0 for t in p['activation_time_s']):
        raise ValueError('Invalid muscle curves or activation times')
    return p


def _fixed_neutral_pose(fly):
    """Bake the supplied rig pose into rigid appendages of the tethered assay."""
    skeleton = Skeleton(axis_order=AxisOrder.YAW_PITCH_ROLL, joint_preset=JointPreset.LEGS_ONLY)
    pose = KinematicPosePreset.NEUTRAL.get_pose_by_axis_order(skeleton.axis_order)
    for dof in skeleton.iter_jointdofs(fly.root_segment):
        axis = np.array(dof.axis.to_vector())
        if dof.child.pos[0] == 'r' and not fly._is_pitch(dof):
            axis = -axis
        rotation, combined = np.empty(4), np.empty(4)
        mujoco.mju_axisAngle2Quat(rotation, axis, pose.joint_angles_lookup_rad.get(dof.name, 0))
        body = fly.bodyseg_to_mjcfbody[dof.child]
        mujoco.mju_mulQuat(combined, body.quat, rotation)
        body.quat = combined


def make_body(*, locomotion=False, parameters=None, clamp_angle=None):
    p = muscle_parameters() if parameters is None else parameters
    # Preset gait is available only to the separately labelled `fly walk` demo.
    fly = make_locomotion_fly(name='fly', add_adhesion=True, colorize=True) if locomotion else NeuroMechFly(name='fly')
    if not locomotion:
        _fixed_neutral_pose(fly)
        fly.colorize()
    rostrum = fly.bodyseg_to_mjcfbody[BodySegment('c_rostrum')]
    head = fly.bodyseg_to_mjcfbody[BodySegment('c_head')]
    rostrum.add_joint(
        name='proboscis_pitch', type=mujoco.mjtJoint.mjJNT_HINGE, axis=(0, 1, 0),
        limited=True, range=p['joint_range_rad'],
        stiffness=p['passive_stiffness_nNm_per_rad'],
        damping=p['passive_damping_nNm_s_per_rad'])
    head.add_site(name='m9_origin', pos=p['origin_head_mm'], size=(0.015, 0, 0), rgba=(0.9, 0.25, 0.15, 1))
    rostrum.add_site(name='m9_insertion', pos=p['insertion_rostrum_mm'], size=(0.015, 0, 0), rgba=(0.9, 0.25, 0.15, 1))
    tendon = fly.mjcf_root.add_tendon(name='m9_tendon', width=0.014, rgba=(0.9, 0.25, 0.15, 1))
    tendon.wrap_site('m9_origin')
    tendon.wrap_site('m9_insertion')
    # Declared fiber/tendon lengths define native length normalization, never an angle target.
    lengthrange = [p['tendon_length_mm'] + p['optimal_fiber_length_mm'] * r for r in (0.25, 1.25)]
    prm = [0.25, 1.25, p['force_uN'], 200, p['lmin'], p['lmax'], p['vmax'], p['fpmax'], p['fvmax'], 0]
    fly.mjcf_root.add_actuator(name='m9_right', trntype=mujoco.mjtTrn.mjTRN_TENDON,
        target='m9_tendon', gear=(1, 0, 0, 0, 0, 0), lengthrange=lengthrange,
        ctrllimited=True, ctrlrange=(0, 1), actlimited=True, actrange=(0, 1),
        dyntype=mujoco.mjtDyn.mjDYN_MUSCLE, dynprm=[*p['activation_time_s'], 0, 0, 0, 0, 0, 0, 0, 0],
        gaintype=mujoco.mjtGain.mjGAIN_MUSCLE, gainprm=prm,
        biastype=mujoco.mjtBias.mjBIAS_MUSCLE, biasprm=prm)
    fly._rebuild_neutral_keyframe()
    fly.add_tracking_camera(name='body_cam', pos_offset=(-0.5, -7.5, 0),
        rotation=Rotation3D('euler', (1.57, 0, 0)), fovy=35)
    fly.add_tracking_camera(name='feeding_cam', mode='fixed', pos_offset=(0.45, -2.8, -0.3),
        rotation=Rotation3D('euler', (1.57, 0, 0)), fovy=40)
    world = FlatGroundWorld() if locomotion else TetheredWorld(name='mn9_muscle_assay')
    if not locomotion:
        world.mjcf_root.worldbody.add_geom(name='ground_plane', type=mujoco.mjtGeom.mjGEOM_PLANE,
            size=(100, 100, 1), rgba=(0.4, 0.42, 0.43, 1), contype=0, conaffinity=0)
    add_sources(world)
    if locomotion:
        world.add_fly(fly, [0, 0, 0.8], Rotation3D('quat', [1, 0, 0, 0]),
            bodysegs_with_ground_contact=ContactBodiesPreset.TIBIA_TARSUS_ONLY,
            add_ground_contact_sensors=False)
    else:
        world.add_fly(fly, [0, 0, -0.15], Rotation3D('quat', [1, 0, 0, 0]))
        # Preserve named sensing/attachment frames and include real mouth loads.
        world.mjcf_root.compiler.fusestatic = False
        for target in ('food_0', 'food_1', 'ground_plane'):
            world.mjcf_root.add_pair(geomname1='fly/c_haustellum', geomname2=target,
                name=f'mouth-{target}', friction=(0.3, 0.3, 0.005, 0.0001, 0.0001))
    world.mjcf_root.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    if clamp_angle is not None:
        if not math.isfinite(clamp_angle) or not p['joint_range_rad'][0] <= clamp_angle <= p['joint_range_rad'][1]:
            raise ValueError('Isometric clamp is outside the joint range')
        world.mjcf_root.add_equality(name='isometric_m9', type=mujoco.mjtEq.mjEQ_JOINT,
            name1=PROBOSCIS_JOINT, data=[clamp_angle, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            solref=(0.002, 1), solimp=(0.9999, 0.9999, 0.001, 0.5, 2))
    sim = Simulation(world)
    controller = HybridTurningController(timestep=sim.timestep,
        preprogrammed_steps=PreprogrammedSteps(),
        output_dof_order=fly.get_actuated_jointdofs_order('position')) if locomotion else None
    return sim, fly, controller


def reset_body(sim, fly, controller):
    sim.reset()
    if controller is not None:
        controller.reset(seed=0)
        apply_locomotion_action(sim, fly.name, LocomotionAction(
            joint_angles=controller.preprogrammed_steps.default_pose_by_dof_order(
                controller.output_dof_order), adhesion_onoff=np.ones(6, dtype=bool)))
    sim.warmup(duration_s=0.05 if controller is not None else 0.2)
    sim.mj_data.time = 0  # The settled pose is the initial condition.
    mujoco.mj_forward(sim.mj_model, sim.mj_data)


def body_signature():
    root = Path(__file__).parent
    return hashlib.sha256(b''.join((root / name).read_bytes() for name in
        ('body.py', 'arena.py', 'neuromuscular.py', 'muscle9.json'))).hexdigest()


def muscle_state(sim):
    model, data = sim.mj_model, sim.mj_data
    i = model.actuator(PROBOSCIS_ACTUATOR).id
    length, velocity = data.actuator_length[i], data.actuator_velocity[i]
    activation = data.act[model.actuator_actadr[i]]
    active = activation * mujoco.mju_muscleGain(length, velocity,
        model.actuator_lengthrange[i], model.actuator_acc0[i], model.actuator_gainprm[i, :9])
    passive = mujoco.mju_muscleBias(length, model.actuator_lengthrange[i],
        model.actuator_acc0[i], model.actuator_biasprm[i, :9])
    dof = model.joint(PROBOSCIS_JOINT).dofadr[0]
    return dict(excitation=float(data.ctrl[i]), activation=float(activation),
        active_tension_uN=float(-active), passive_tension_uN=float(-passive),
        total_tension_uN=float(-data.actuator_force[i]), torque_nNm=float(data.qfrc_actuator[dof]),
        length_mm=float(length), velocity_mm_s=float(velocity))
