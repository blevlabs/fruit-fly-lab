"""Body forces for supported MaleCNS muscle targets; no action or gait controller."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import mujoco as mj
import numpy as np
from flygym import Simulation
from flygym.anatomy import AxisOrder, BodySegment, ContactBodiesPreset, JointPreset, Skeleton
from flygym.compose import FlatGroundWorld, KinematicPosePreset, NeuroMechFly, TetheredWorld
from flygym.compose.fly.base_fly import ActuatorType
from flygym.utils.math import Rotation3D

from arena import add_sources
from leg_muscles import add_leg_muscles
from proboscis_muscles import add_proboscis_muscles
from head_muscles import add_head_muscles
from flight_integration import AIR_DENSITY, AIR_VISCOSITY, add_flight_mechanics, bind_flight_motor_units
from neuromuscular import NeuromuscularJunction

ROOT = Path(__file__).resolve().parent


def config():
    return json.loads((ROOT / 'cns-model.json').read_text())


def body_signature():
    files = ('cns_body.py', 'cns-model.json', 'leg_muscles.py', 'proboscis_muscles.py',
             'head_muscles.py', 'flight_mechanics.py', 'flight_integration.py',
             'neuromuscular.py', 'arena.py', 'muscle9.json', 'neural-motor/malecns-motor-map.json')
    return hashlib.sha256(b''.join((ROOT / f).read_bytes() for f in files)).hexdigest()


def _connect_motor_units(fly, records, motors):
    """Resolve only named target/side matches; split group capacity, not signals."""
    linked = set()
    units = []
    for record in records:
        matches = []
        for motor in motors:
            if record.get('peripheral_target_topology') == 'unpaired_organ_group':
                side_matches = (record['side'] == 'unpaired'
                                and motor.get('peripheral_target_topology') == 'unpaired_organ_group')
            else:
                side_matches = record['side'][0].upper() in motor.get('peripheral_target_sides', [])
            if not side_matches:
                continue
            if record.get('semantic_muscle_key') is not None:
                match = motor['semantic_muscle_key'] == record['semantic_muscle_key']
            else:
                match = (motor.get('peripheral_limb') == record['limb']
                         and record['target_muscle'] is not None
                         and motor['target'] == record['target_muscle'])
            if match:
                matches.append(motor)
        record['motor_neuron_ids'] = [m['bodyId'] for m in matches]
        record['mapping_status'] = 'named_target_with_estimated_capacity' if matches else 'unmapped'
        if not matches:
            continue
        # The source MTU models a whole muscle group. Each identified motor unit
        # gets a separate activation state and an explicit equal capacity share.
        # Multiple geometric a/b paths retain their existing capacity partition.
        name = record['local_actuator_name']
        original = next(a for a in fly.mjcf_root.actuators if a.name == name)
        gain = np.array(original.gainprm, copy=True)
        bias = np.array(original.biasprm, copy=True)
        gain[2] /= len(matches); bias[2] /= len(matches)
        for motor in matches:
            unit_name = f'{name}_mn{motor["bodyId"]}'
            actuator = fly.mjcf_root.add_actuator(name=unit_name,
                trntype=mj.mjtTrn.mjTRN_TENDON, target=record['local_tendon_name'],
                gear=(1, 0, 0, 0, 0, 0), lengthrange=np.array(original.lengthrange, copy=True),
                ctrllimited=True, ctrlrange=(0, 1), actlimited=True, actrange=(0, 1),
                dyntype=mj.mjtDyn.mjDYN_MUSCLE, dynprm=np.array(original.dynprm, copy=True),
                gaintype=mj.mjtGain.mjGAIN_MUSCLE, gainprm=gain,
                biastype=mj.mjtBias.mjBIAS_MUSCLE, biasprm=bias)
            fly.jointdof_to_mjcfactuator_by_type[ActuatorType.MUSCLE][unit_name] = actuator
            fly.jointdof_to_neutralaction_by_type[ActuatorType.MUSCLE][unit_name] = 0.0
            units.append(dict(bodyId=motor['bodyId'], actuator_name=f'{fly.name}/{unit_name}',
                muscle=record['target_muscle'], limb=record['limb'], side=record['side'],
                source_muscle_path=record['actuator_name'], capacity_fraction=1 / len(matches),
                maximum_isometric_force_uN=float(gain[2]),
                target_evidence=motor['assignment_method'], side_evidence=motor['peripheral_side_method'],
                output_topology=motor['peripheral_target_topology'],
                approximation='Equal motor-unit capacity; no measured fiber-subdivision assignment'))
            linked.add(motor['bodyId'])
        fly.mjcf_root.delete(original)
        del fly.jointdof_to_mjcfactuator_by_type[ActuatorType.MUSCLE][name]
        del fly.jointdof_to_neutralaction_by_type[ActuatorType.MUSCLE][name]
    fly._rebuild_neutral_keyframe()
    # Bilateral or unpaired innervation must be documented in the source row;
    # even then the neuron cannot acquire a different named muscle target.
    targets = defaultdict(set)
    for unit in units:
        targets[unit['bodyId']].add((unit['limb'], unit['muscle']))
    if any(len(values) != 1 for values in targets.values()):
        raise ValueError('A motor neuron was assigned to conflicting peripheral targets')
    return units, linked


def make_body(*, tethered=False):
    p = config()
    motor_map = json.loads((ROOT / 'neural-motor/malecns-motor-map.json').read_text())
    if motor_map['dataset'] != p['dataset'] or len({m['bodyId'] for m in motor_map['motors']}) != len(motor_map['motors']):
        raise ValueError('Motor mapping dataset or identifiers are invalid')
    fly = NeuroMechFly(name='fly')
    # Use the same physical mass budget during component compilation and final
    # world compilation; hidden minimum-mass floors can otherwise add tissue.
    fly.mjcf_root.compiler.boundmass = 0
    fly.mjcf_root.compiler.boundinertia = 0
    skeleton = Skeleton(axis_order=AxisOrder.YAW_PITCH_ROLL, joint_preset=JointPreset.LEGS_ONLY)
    joints = fly.add_joints(skeleton, KinematicPosePreset.NEUTRAL,
        stiffness=p['leg_joint_stiffness'], damping=p['leg_joint_damping_nNm_s'],
        armature=p['leg_joint_armature_g_mm2'])
    for dof, joint in joints.items():
        initial_angle = fly.jointdof_to_neutralangle[dof]
        joint.limited = True
        joint.range = (initial_angle - p['joint_range_half_width_rad'],
                       initial_angle + p['joint_range_half_width_rad'])
    fly.colorize()
    records = add_leg_muscles(fly, group_force_uN=p['leg_group_force_uN'],
                              activation_time_s=p['leg_activation_time_s'])
    records += add_proboscis_muscles(fly)
    records += add_head_muscles(fly)
    units, linked = _connect_motor_units(fly, records, motor_map['motors'])
    flight_paths = add_flight_mechanics(fly)
    flight_units, flight_linked = bind_flight_motor_units(fly, flight_paths, motor_map['motors'])
    if linked & flight_linked:
        raise ValueError('A motor neuron acquired targets in two independent muscle banks')
    linked |= flight_linked
    # Native collision layers: fly surfaces=1, source objects=2, ground=4.
    # Only actual exterior meshes enter this set; internal sclerite/organ proxy
    # geoms and aerodynamic ellipsoids remain non-colliding.
    surfaces = {g.name for geoms in fly.bodyseg_to_mjcfgeom.values() for g in geoms}
    surfaces |= {name.removeprefix(f'{fly.name}/') for r in records for name in r.get('contact_geom_names', [])}
    for geometry in fly.flight_contact_geometry.values():
        surfaces -= {name.removeprefix(f'{fly.name}/') for name in geometry['visual_geom_names']}
        surfaces |= {name.removeprefix(f'{fly.name}/') for name in geometry['contact_geom_names']}
    for name in surfaces:
        geom = fly.mjcf_root.geom(name)
        geom.contype, geom.conaffinity = 1, 7
    owners = {geom.name: body for body in fly.mjcf_root.bodies for geom in body.geoms}
    surface_bodies = {owners[name].name for name in surfaces}
    parent_exclusions = {(owners[name].parent.name, owners[name].name) for name in surfaces
                         if owners[name].parent is not None and owners[name].parent.name in surface_bodies}
    fly.add_tracking_camera(name='body_cam', pos_offset=(-0.5, -7.5, 0),
        rotation=Rotation3D('euler', (1.57, 0, 0)), fovy=35)
    fly.add_tracking_camera(name='feeding_cam', mode='fixed', pos_offset=(0.45, -2.8, -0.3),
        rotation=Rotation3D('euler', (1.57, 0, 0)), fovy=40)
    world = TetheredWorld(name='cns_supported_body') if tethered else FlatGroundWorld(name='cns_supported_body')
    add_sources(world, register_as_ground=False)
    for i in range(2):
        food = world.mjcf_root.geom(f'food_{i}')
        food.contype, food.conaffinity = 2, 1
    if tethered:
        world.add_fly(fly, [0, 0, 0], Rotation3D('quat', [1, 0, 0, 0]))
    else:
        world.add_fly(fly, [0, 0, 0], Rotation3D('quat', [1, 0, 0, 0]),
            bodysegs_with_ground_contact=ContactBodiesPreset.LEGS_THORAX_ABDOMEN_HEAD,
            add_ground_contact_sensors=False)
        ground = world.mjcf_root.geom('ground_plane')
        ground.contype, ground.conaffinity = 4, 1
    # These connected joint/socket proxy volumes overlap in the supplied rig.
    # They are not separate colliding cuticle surfaces. Distal limb/body and
    # cross-limb contacts remain enabled; true socket surface detail is unresolved.
    # Explicit parent pairs also cover the tethered preparation, where MuJoCo's
    # world-weld parent exception would otherwise turn sockets into obstacles.
    exclusions = list(parent_exclusions)
    for limb in ('lf', 'rf', 'lm', 'rm', 'lh', 'rh'):
        exclusions += [(f'{limb}_coxa', f'{limb}_trochanterfemur'),
                       ('c_thorax', f'leg_muscle_{limb}_trochanter'),
                       ('c_thorax', f'{limb}_trochanterfemur')]
    exclusions += [('c_head', f'{side}_funiculus') for side in ('l', 'r')]
    exclusions += [('c_rostrum', f'proboscis_labellum_{side}') for side in ('left', 'right')]
    exclusions += [('lh_coxa', 'rh_coxa')]
    exclusions += [('c_abdomen12', f'{side}_haltere') for side in ('l', 'r')]
    exclusions = sorted(set(exclusions))
    for index, (a, b) in enumerate(exclusions):
        world.mjcf_root.add_exclude(name=f'connected_socket_{index}', bodyname1=f'fly/{a}', bodyname2=f'fly/{b}')
    world.mjcf_root.compiler.fusestatic = False
    world.mjcf_root.compiler.boundmass = 0
    world.mjcf_root.compiler.boundinertia = 0
    world.mjcf_root.option.timestep = p['timestep_s']
    world.mjcf_root.memory = p['physics_arena_bytes']
    world.mjcf_root.option.integrator = mj.mjtIntegrator.mjINT_IMPLICITFAST
    world.mjcf_root.option.iterations = 100
    world.mjcf_root.option.tolerance = 1e-12
    # The inherited NoSlip PGS pass forms a constraint-space matrix that grows
    # quadratically with dense wing contacts. Use the ordinary Newton friction
    # solution, with no extra hard-friction correction or removed contacts.
    world.mjcf_root.option.noslip_iterations = 0
    world.mjcf_root.option.density = AIR_DENSITY
    world.mjcf_root.option.viscosity = AIR_VISCOSITY
    sim = Simulation(world)
    sim.source_contact_masks = (2, 1)
    mj.mj_forward(sim.mj_model, sim.mj_data)
    initial_lift = 0.0
    if not tethered:
        ground = sim.mj_model.geom('ground_plane').id
        deepest = min((contact.dist for contact in sim.mj_data.contact
                       if ground in (contact.geom1, contact.geom2)), default=0)
        if deepest < 0:
            # Nonpenetrating initial placement only; no support force or pose
            # controller is applied after the simulation clock starts.
            initial_lift = float(-deepest + .001)
            free = np.flatnonzero(sim.mj_model.jnt_type == mj.mjtJoint.mjJNT_FREE)
            if len(free) != 1:
                raise ValueError('Expected one free whole-body root for initial ground placement')
            root_z = sim.mj_model.jnt_qposadr[free[0]] + 2
            sim.mj_model.key_qpos[sim._neutral_keyframe_id, root_z] += initial_lift
            sim.reset()
            mj.mj_forward(sim.mj_model, sim.mj_data)
    coverage = dict(dataset=p['dataset'], model=p['model'], tethered=tethered,
        total_motor_neurons=len(motor_map['motors']), connected_motor_neurons=len(linked),
        unconnected_motor_neurons=len(motor_map['motors']) - len(linked),
        muscle_tendon_paths=len(records) + len(flight_paths),
        connected_muscle_paths=sum(bool(r['motor_neuron_ids']) for r in records + flight_paths),
        native_motor_unit_actuators=len(units) + sum(u['bodyId'] is not None for u in flight_units),
        connected_flight_motor_neurons=len(flight_linked),
        physical_contacts='Native exterior self-contact, source and ground collisions; adjacent-body native filtering retained',
        collision_exclusions=exclusions, initial_ground_clearance_lift_mm=initial_lift,
        flight_reference_pose=fly.flight_reference_pose,
        flight_contact_geometry=fly.flight_contact_geometry,
        wing_collision_patches=sum(g['patch_count'] for g in fly.flight_contact_geometry.values()),
        fly_mass_g=float(sum(sim.mj_model.body_mass[i] for i in range(sim.mj_model.nbody)
                             if sim.mj_model.body(i).name.startswith(f'{fly.name}/'))),
        asynchronous_motor_units=sum(u['kind'] == 'asynchronous' and u['bodyId'] is not None for u in flight_units),
        connected_motor_by_subclass=dict(Counter(m['subclass'] for m in motor_map['motors'] if m['bodyId'] in linked)),
        unresolved_motor_ids=[m['bodyId'] for m in motor_map['motors'] if m['bodyId'] not in linked],
        unimplemented_body=['unresolved muscle identities and individual fiber assignments',
            'abdomen/genitalia musculature', 'antennal/retinal neuronal muscle correspondences',
            'complete alimentary fluid transport and body metabolism',
            'validated full-stroke flight/hinge physiology and natural behavior'],
        assumptions=p, muscle_paths=records, motor_units=units,
        flight_paths=flight_paths, flight_motor_units=flight_units)
    return sim, fly, coverage


class MotorUnits:
    def __init__(self, model, coverage):
        params = config()['nmj']
        self.ids = sorted({u['bodyId'] for u in coverage['motor_units']})
        self.index = {body_id: i for i, body_id in enumerate(self.ids)}
        self.nmjs = [NeuromuscularJunction(model.opt.timestep, params) for _ in self.ids]
        self.actuators = np.array([model.actuator(u['actuator_name']).id for u in coverage['motor_units']])
        self.unit_indices = np.array([self.index[u['bodyId']] for u in coverage['motor_units']])

    def reset(self):
        for nmj in self.nmjs:
            nmj.reset()

    def advance(self, data, spikes, *, release_block=False):
        spikes = np.asarray(spikes)
        if spikes.shape != (len(self.ids),) or not np.isin(spikes, [0, 1]).all():
            raise ValueError('One binary event per connected motor neuron is required')
        control = np.array([nmj.advance(bool(event), release_block=release_block)
                            for nmj, event in zip(self.nmjs, spikes)])
        data.ctrl[:] = 0
        data.ctrl[self.actuators] = control[self.unit_indices]
