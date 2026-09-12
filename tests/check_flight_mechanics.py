"""Local CPU component checks only. No brain, viewer, network or flight policy.

Run: .venv/bin/python -B check_flight_mechanics.py
Length steps and irregular spike events below are laboratory test inputs,
not generated motor behavior or runtime wing trajectories.
"""
from dataclasses import replace
import json
import math
from pathlib import Path
import warnings

import mujoco
import numpy as np

from flight_mechanics import IFMParameters, StretchActivatedMuscle, free_wing_xml, ReducedThorax


def must_reject(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('Invalid input accepted')


def mesh_triangles(model,data,geom_name):
    gid=model.geom(geom_name).id
    mid=model.geom_dataid[gid]
    start,count=model.mesh_vertadr[mid],model.mesh_vertnum[mid]
    vertices=model.mesh_vert[start:start+count]@data.geom_xmat[gid].reshape(3,3).T+data.geom_xpos[gid]
    start,count=model.mesh_faceadr[mid],model.mesh_facenum[mid]
    return vertices[model.mesh_face[start:start+count]]


def point_surface_distance(point,triangles):
    """Independent nearest distance to raw triangles, not their convex hulls."""
    a,b,c=triangles.transpose(1,0,2)
    e1,e2,q=b-a,c-a,point-a
    aa,bb,cc=(e1*e1).sum(1),(e1*e2).sum(1),(e2*e2).sum(1)
    qa,qb=(q*e1).sum(1),(q*e2).sum(1)
    denominator=aa*cc-bb*bb
    u=np.divide(cc*qa-bb*qb,denominator,out=np.zeros_like(aa),where=denominator>1e-24)
    v=np.divide(aa*qb-bb*qa,denominator,out=np.zeros_like(aa),where=denominator>1e-24)
    interior=(denominator>1e-24)&(u>=0)&(v>=0)&(u+v<=1)
    distance=np.where(interior,np.linalg.norm(q-u[:,None]*e1-v[:,None]*e2,axis=1),np.inf)
    for p,r in ((a,b),(b,c),(c,a)):
        edge=r-p
        t=np.clip(((point-p)*edge).sum(1)/(edge*edge).sum(1),0,1)
        distance=np.minimum(distance,np.linalg.norm(point-p-t[:,None]*edge,axis=1))
    return float(distance.min())


def check_wing_contacts():
    from flygym import Simulation
    from flygym.compose import NeuroMechFly,FlatGroundWorld
    from flygym.utils.math import Rotation3D
    from flight_integration import add_flight_mechanics,bind_flight_motor_units,FlightMotorUnits
    fly=NeuroMechFly(name='fly')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore');old,od=fly.compile()
    mujoco.mj_kinematics(old,od)
    old_depth=float(mujoco.mj_geomDistance(old,od,old.geom('l_wing').id,old.geom('r_wing').id,1.,np.zeros(6)))
    assert old_depth<-.3
    records=add_flight_mechanics(fly)
    units,_=bind_flight_motor_units(fly,records,[])  # passive body, no invented motor inputs
    world=FlatGroundWorld()
    world.add_fly(fly,[0,0,5],Rotation3D('quat',[1,0,0,0]),bodysegs_with_ground_contact=[])
    for label,radius in [('small',.03),('food_sized',.7)]:
        probe=world.mjcf_root.worldbody.add_body(name='probe_'+label,pos=(0,0,100))
        probe.add_freejoint(name='probe_'+label)
        probe.add_geom(name='probe_'+label,type=mujoco.mjtGeom.mjGEOM_SPHERE,
                       size=(radius,0,0),mass=.0001,contype=2,conaffinity=1)
    world.mjcf_root.option.timestep=1e-5
    world.mjcf_root.option.gravity=(0,0,0)
    world.mjcf_root.option.density=world.mjcf_root.option.viscosity=0
    world.mjcf_root.option.integrator=mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    world.mjcf_root.option.iterations=100
    world.mjcf_root.option.tolerance=1e-12
    world.mjcf_root.compiler.fusestatic=False
    sim=Simulation(world)
    model,data=sim.mj_model,sim.mj_data
    mujoco.mj_forward(model,data)
    initial=data.qpos.copy()
    bank=FlightMotorUnits(model,units)
    patch_ids={side:[model.geom(n).id for n in meta['contact_geom_names']]
               for side,meta in fly.flight_contact_geometry.items()}
    assert data.ncon==0  # contacts are enabled; the explicit initial pose is clear
    source_open={s:mesh_triangles(model,data,f'fly/{s.lower()}_wing') for s in ('L','R')}
    separation=float(source_open['L'][...,1].min()-source_open['R'][...,1].max())
    assert separation>0
    for side,letter in [('L','l'),('R','r')]:
        old_mid=old.geom(letter+'_wing').dataid[0]
        new_mid=model.geom('fly/'+letter+'_wing').dataid[0]
        old_start,new_start=old.mesh_vertadr[old_mid],model.mesh_vertadr[new_mid]
        count=old.mesh_vertnum[old_mid]
        assert np.array_equal(old.mesh_vert[old_start:old_start+count],model.mesh_vert[new_start:new_start+count])
        assert old.body(letter+'_wing').mass[0]==model.body('fly/'+letter+'_wing').mass[0]
        assert np.all(model.geom_contype[patch_ids[side]]==1) and np.all(model.geom_conaffinity[patch_ids[side]]==7)
        assert np.all(model.geom_group[patch_ids[side]]==5)
        assert model.geom('fly/'+letter+'_wing').contype[0]==0

    trials=[]
    for label,radius in [('small',.03),('food_sized',.7)]:
        gid=model.geom('probe_'+label).id
        adr=model.joint('probe_'+label).qposadr[0]
        triangles=source_open['L']
        xy=triangles.mean(axis=(0,1))[:2]
        ids=np.array(patch_ids['L'])
        ids=ids[np.linalg.norm(data.geom_xpos[ids,:2]-xy,axis=1)<=radius+model.geom_rbound[ids]+.01]
        def position_and_gap(height):
            data.qpos[adr:adr+3]=(*xy,height)
            mujoco.mj_kinematics(model,data)
            return min(float(mujoco.mj_geomDistance(model,data,gid,int(i),2.,np.zeros(6))) for i in ids)
        for expected in (.002,-.001):
            mujoco.mj_resetData(model,data);data.qpos[:]=initial;bank.reset()
            low=float(triangles[...,2].mean());high=float(triangles[...,2].max()+radius+.1)
            assert position_and_gap(low)<expected and position_and_gap(high)>expected
            for _ in range(35):
                middle=(low+high)/2
                if position_and_gap(middle)>expected:high=middle
                else:low=middle
            measured=position_and_gap((low+high)/2)
            raw_gap=point_surface_distance(data.qpos[adr:adr+3],triangles)-radius
            assert abs(measured-expected)<2e-6
            assert abs(raw_gap-measured)<.0003  # .25-um outward skin + CCD/rounding error
            mujoco.mj_forward(model,data)
            contacts=[(i,c) for i,c in enumerate(data.contact) if gid in c.geom]
            force=np.zeros(3)
            relaxed=None
            for i,c in contacts:
                local=np.zeros(6);mujoco.mj_contactForce(model,data,i,local)
                force+=(1 if c.geom[1]==gid else -1)*c.frame.reshape(3,3).T@local[:3]
            if expected>0:
                assert not contacts and np.linalg.norm(force)==0
            else:
                assert contacts and abs(min(c.dist for _,c in contacts)-expected)<5e-6
                assert force[2]>0 and data.qacc[model.joint('probe_'+label).dofadr[0]+2]>0
                for _ in range(1000):
                    mujoco.mj_forward(model,data);bank.advance(data,np.zeros(0,dtype=int));mujoco.mj_step(model,data)
                mujoco.mj_forward(model,data)
                relaxed=min(float(mujoco.mj_geomDistance(model,data,gid,int(i),2.,np.zeros(6))) for i in ids)
                assert relaxed-measured>1e-5  # >10 nm of separation, beyond CCD rounding
                assert np.isfinite(data.qpos).all() and sum(w.number for w in data.warning)==0
            trials.append(dict(probe_radius_mm=radius,expected_gap_mm=expected,
                native_gap_mm=measured,raw_triangle_gap_mm=raw_gap,contact_count=len(contacts),
                upward_force_uN=float(force[2]),relaxed_gap_mm=relaxed))
    return dict(old_folded_convex_penetration_mm=old_depth,open_source_y_clearance_mm=separation,
        open_initial_contacts=0,patches_per_wing={s:len(x) for s,x in patch_ids.items()},
        visual_mesh_data_unchanged=True,wing_masses_unchanged=True,
        condition='explicit static open-wing reference, not a wing controller',foreign_body_trials=trials)


def check_thorax():
    def run(channel=None, *, dt=1e-5, blocked=False, load=0, **options):
        f = ReducedThorax(dt_s=dt, **options)
        wing_dof = f.model.joint('PWP_ax2_flexure').dofadr[0]
        f.data.qfrc_applied[wing_dof] = load  # external mechanical assay load
        events = {round(t/dt)-1 for t in (.002, .007, .013)}
        for tick in range(round(.02/dt)):
            f.step({channel: tick in events} if channel else {}, release_block=blocked)
        mujoco.mj_forward(f.model, f.data)
        assert np.isfinite(f.data.qpos).all() and np.isfinite(f.data.qvel).all()
        assert sum(w.number for w in f.data.warning) == 0
        assert max(abs(f.data.efc_pos)) < 1e-5
        scale = options.get('geometry_scale', 1.0)
        # Closure of the physical rhombus, including solver compliance tolerance.
        dlm, dvm = f.data.tendon('DLM').length[0], f.data.tendon('DVM').length[0]
        assert abs(dlm*dlm+dvm*dvm - scale*scale*(.9**2+.65**2)) < 1e-5
        state = np.array([f.data.joint('notum_heave').qpos[0],
                          f.data.joint('PWP_ax2_flexure').qpos[0]])
        return f, state

    quiet, q = run()
    assert np.max(abs(quiet.data.qpos)) < 1e-12
    assert all(n.received == 0 for n in quiet.steering_nmjs.values())
    outcomes, convergence = {}, {}
    for name in ('DLM', 'DVM', 'i1', 'i2'):
        f, state = run(name)
        blocked, b = run(name, blocked=True)
        assert np.max(abs(b-q)) < 1e-12
        assert abs(state[1]) > 1e-8  # transmission exists; no desired amplitude
        assert state[0] * state[1] < 0
        assert state[1] < 0 if name == 'DLM' else state[1] > 0
        assert (f.data.ten_length[0]-.9) * (f.data.ten_length[1]-.65) < 0
        outcomes[name] = state.tolist()
        _, fine = run(name, dt=5e-6)
        convergence[name] = float(np.max(abs(state-fine) / abs(fine)))
        assert convergence[name] < .02
    # At reference geometry DLM and steering forces are not applied to wing DOF.
    native = ReducedThorax()
    native.data.actuator('DLM').ctrl[0] = 1
    mujoco.mj_forward(native.model, native.data)
    wing_dof = native.model.joint('PWP_ax2_flexure').dofadr[0]
    assert native.data.qfrc_actuator[wing_dof] == 0
    assert np.linalg.norm(native.data.qfrc_actuator) > 0
    _, clamp = run('DLM', clamp_notum=True)
    assert abs(clamp[1]) < abs(outcomes['DLM'][1]) * .01
    _, loaded = run('DLM', load=.002)
    assert loaded[1] > outcomes['DLM'][1]
    sensitivity = {}
    for label, options in (
        ('scale_0.8', dict(geometry_scale=.8)),
        ('scale_1.2', dict(geometry_scale=1.2)),
        ('half_stiffness', dict(hinge_stiffness=.05)),
        ('double_stiffness', dict(hinge_stiffness=.2)),
    ):
        _, state = run('DLM', **options)
        assert state[0] > 0 and state[1] < 0
        sensitivity[label] = state.tolist()
    must_reject(lambda: quiet.step({'wing_angle': .1}))
    must_reject(lambda: quiet.step({'DLM': 2}))
    must_reject(lambda: ReducedThorax(dt_s=.0001))
    return dict(heave_mm_and_wing_rad=outcomes, half_dt_relative_errors=convergence,
                opposing_load_wing_rad=float(loaded[1]), clamped_wing_rad=float(clamp[1]),
                sensitivity=sensitivity, topology='estimated unilateral scutum-ax1-ax2 linkage',
                reconstructed_joint_geometry=False, self_sustained_flight_tested=False)


def check_body_integration():
    from flygym import Simulation
    from flygym.compose import NeuroMechFly, FlatGroundWorld
    from flygym.utils.math import Rotation3D
    from flight_integration import (add_flight_mechanics, bind_flight_motor_units,
        FlightMotorUnits, AIR_DENSITY, AIR_VISCOSITY)

    rows = json.loads(((Path(__file__).resolve().parents[1] / 'runtime')/'neural-motor/malecns-motor-map.json').read_text())['motors']

    def properties(model, data):
        mass = float(sum(model.body_mass))
        first = sum((model.body_mass[i]*data.xipos[i] for i in range(1, model.nbody)), np.zeros(3))
        inertia = np.zeros((3,3))
        for i in range(1,model.nbody):
            center, rotation = data.xipos[i], data.ximat[i].reshape(3,3)
            inertia += rotation@np.diag(model.body_inertia[i])@rotation.T
            inertia += model.body_mass[i]*(np.dot(center,center)*np.eye(3)-np.outer(center,center))
        return mass, first/mass, inertia

    def build(dt=1e-5, air=True, gravity=False):
        fly = NeuroMechFly(name='fly')
        fly.mjcf_root.compiler.boundmass = fly.mjcf_root.compiler.boundinertia = 0
        reference_spec=fly.mjcf_root.copy()
        reference_spec.compiler.fusestatic=False
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            before, bd = fly.compile()
        mujoco.mj_forward(before,bd)
        original = properties(before,bd)
        records = add_flight_mechanics(fly)
        # Reposing is an explicit initial condition. Compare the internal mass
        # partition against the same open-wing reference, not the old folded pose.
        for side,letter in [('L','l'),('R','r')]:
            reference_spec.body(letter+'_wing').quat=fly.flight_reference_pose[side]['initial_body_quat']
        reference_model=reference_spec.compile()
        reference_data=mujoco.MjData(reference_model)
        mujoco.mj_kinematics(reference_model,reference_data)
        mujoco.mj_comPos(reference_model,reference_data)
        opened=properties(reference_model,reference_data)
        units, linked = bind_flight_motor_units(fly,records,rows)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            after, ad = fly.compile()
        mujoco.mj_forward(after,ad)
        new = properties(after,ad)
        assert abs(original[0]-new[0]) < 1e-15
        assert np.max(abs(opened[1]-new[1])) < 1e-12
        assert np.max(abs(opened[2]-new[2])) < 1e-12
        for name in ('l_wing','r_wing','l_haltere','r_haltere'):
            assert before.body(name).mass[0] == after.body(name).mass[0]
            assert np.max(abs(bd.body(name).xpos-ad.body(name).xpos)) < 1e-12
        world = FlatGroundWorld()
        world.add_fly(fly,[0,0,5],Rotation3D('quat',[1,0,0,0]),bodysegs_with_ground_contact=[])
        world.mjcf_root.option.timestep = dt
        world.mjcf_root.option.gravity = (0,0,-9810 if gravity else 0)
        world.mjcf_root.option.density = AIR_DENSITY if air else 0
        world.mjcf_root.option.viscosity = AIR_VISCOSITY if air else 0
        world.mjcf_root.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
        world.mjcf_root.option.iterations = 100
        world.mjcf_root.option.tolerance = 1e-12
        world.mjcf_root.compiler.fusestatic = False
        sim = Simulation(world)
        model, data = sim.mj_model, sim.mj_data
        mujoco.mj_forward(model,data)
        assert abs(sum(model.body_mass)-original[0]) < 1e-15
        bank = FlightMotorUnits(model,units)
        return model,data,bank,records,units,linked,fly.flight_mass_budget

    model,data,bank,records,units,linked,budget = build()
    initial = data.qpos.copy()
    rotational = [model.joint(f'fly/flight_{side}_wing_{mode}').dofadr[0]
                  for side in ('L','R') for mode in ('stroke','elevation','pitch')]
    jacobian = data.efc_J.reshape(data.nefc,model.nv)
    _, singular, vt = np.linalg.svd(jacobian, full_matrices=True)
    nullspace = vt[int(sum(singular>1e-8)):].T
    assert np.linalg.matrix_rank(nullspace[rotational]) == 6
    assert len(bank.ids) == len(linked) == 66
    assert len({(r['semantic_muscle_key'],r['peripheral_target_side']) for r in records}) == len(records)
    assert len([u for u in units if u['bodyId'] is None]) == 10
    for r in records:
        group = [u for u in units if u['semantic_muscle_key']==r['semantic_muscle_key']
                 and u['peripheral_target_side']==r['peripheral_target_side']]
        assert np.isclose(sum(u['force_uN'] for u in group),r['force_uN'],rtol=1e-12)
        assert np.isclose(sum(u['area_mm2'] for u in group),r['area_mm2'],rtol=1e-12)
    for side,pool in {(u['peripheral_target_side'],u['capacity_pool']) for u in units}:
        members=[u for u in units if u['peripheral_target_side']==side and u['capacity_pool']==pool]
        assert np.isclose(sum(u['capacity_fraction'] for u in members),1.,rtol=1e-12)
        assert np.isclose(sum(u['force_uN'] for u in members),members[0]['pool_isometric_force_uN'],rtol=1e-12)
    assert next(u for u in units if u['bodyId']==801295)['peripheral_target_side']=='L'
    assert next(u for u in units if u['bodyId']==801970)['peripheral_target_side']=='R'

    def reset(m=model,d=data,b=bank):
        mujoco.mj_resetData(m,d)
        d.qpos[:] = initial
        mujoco.mj_forward(m,d)
        b.reset()

    def run(key=None, side='L', duration=.006, *, m=model,d=data,b=bank,blocked=False):
        reset(m,d,b)
        indices = sorted({b.index[u['bodyId']] for u in b.units if u['bodyId'] is not None
            and u['semantic_muscle_key']==key and (side=='both' or u['peripheral_target_side']==side)})
        emission_steps = {round(t/m.opt.timestep)-1 for t in (.001,.003,.005)}
        maximum = 0.
        for tick in range(round(duration/m.opt.timestep)):
            events = np.zeros(len(b.ids),dtype=int)
            if tick in emission_steps:
                events[indices] = 1
            mujoco.mj_forward(m,d)
            b.advance(d,events,release_block=blocked)
            mujoco.mj_step(m,d)
            maximum = max(maximum,float(np.max(abs(d.efc_pos))))
        mujoco.mj_forward(m,d)
        assert np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all()
        assert sum(w.number for w in d.warning)==0
        assert maximum < 1e-4  # 0.1 um, below source voxel spacing; not a motion target
        angles = np.array([d.joint(f'fly/flight_{s}_wing_{mode}').qpos[0]
            for s in ('L','R') for mode in ('stroke','elevation','pitch')])
        halteres = np.array([d.joint(f'fly/flight_{s}_haltere_{mode}').qpos[0]
            for s in ('L','R') for mode in ('sweep','bend','torsion')])
        return np.r_[angles,halteres],maximum

    quiet,_ = run()
    assert max(abs(quiet)) < 1e-9
    tested,maximum = 0,0.
    for r in records:
        if not r['motor_neuron_ids']:
            continue
        response,error = run(r['semantic_muscle_key'],r['peripheral_target_side'])
        assert np.linalg.norm(response-quiet)>1e-10  # physical transmission exists
        maximum=max(maximum,error);tested+=1
    blocked,_ = run('wing.dlm_c_f',blocked=True)
    assert np.max(abs(blocked-quiet)) < 1e-9

    # Every family member has its own NMJ and activation history.
    reset()
    siblings=[(u,s) for u,s in zip(bank.units,bank.states) if u['semantic_muscle_key']=='wing.dlm_c_f'
              and u['peripheral_target_side']=='L']
    one=siblings[0][0]['bodyId']
    event=np.zeros(len(bank.ids),int);event[bank.index[one]]=1
    bank.advance(data,event)
    for u,state in siblings:
        assert state.nmj.received == int(u['bodyId']==one)
    bank.reset()
    assert all((state.nmj if hasattr(state,'nmj') else state).received==0 for state in bank.states)

    # A stationary world-free body cannot gain momentum from internal actuation.
    vm,vd,vb,*_ = build(air=False)
    root=vm.body('fly/c_thorax').id
    start=vd.subtree_com[root].copy()
    response,_ = run('wing.i1',duration=.02,m=vm,d=vd,b=vb)
    mujoco.mj_subtreeVel(vm,vd)
    com_drift=float(np.linalg.norm(vd.subtree_com[root]-start))
    momentum=float(np.linalg.norm(vd.subtree_linvel[root])*vm.body_subtreemass[root])
    angular=float(np.linalg.norm(vd.subtree_angmom[root]))
    assert np.linalg.norm(response)>1e-8
    assert com_drift < 1e-5 and momentum < 1e-7 and angular < 1e-7
    assert np.linalg.norm(vd.qpos[3:7]-initial[3:7])>1e-10  # real root reaction
    assert np.all(vd.xfrc_applied==0) and np.all(vd.qfrc_applied==0)

    fine_model,fine_data,fine_bank,*_ = build(dt=5e-6)
    convergence={}
    for key in ('wing.dlm_c_f','wing.i1','wing.b2','wing.hg3','haltere.hDVM','haltere.hi2'):
        coarse,_=run(key,duration=.012)
        fine,_=run(key,duration=.012,m=fine_model,d=fine_data,b=fine_bank)
        convergence[key]=float(np.linalg.norm(coarse-fine)/np.linalg.norm(fine))
        assert convergence[key]<.05

    run('wing.i1',duration=.012)
    with_air=data.qfrc_passive.copy()
    model.opt.density=model.opt.viscosity=0
    mujoco.mj_forward(model,data)
    aerodynamic_force=float(np.linalg.norm(with_air-data.qfrc_passive))
    assert aerodynamic_force>1e-10
    model.opt.density,model.opt.viscosity=AIR_DENSITY,AIR_VISCOSITY
    gm,gd,gb,*_ = build(gravity=True)
    run(duration=.01,m=gm,d=gd,b=gb)  # passive free fall, not a takeoff policy
    assert gd.qpos[2] < initial[2]
    return dict(muscle_paths=len(records),motor_units=len(units),mapped_motor_ids=len(linked),
        passive_only_units=10,independent_wing_rotation_modes=6,tested_semantic_side_paths=tested,
        mass_budget=budget,maximum_pin_error_mm=maximum,half_dt_relative_errors=convergence,
        vacuum_com_drift_mm=com_drift,vacuum_linear_momentum_g_mm_s=momentum,
        vacuum_angular_momentum_g_mm2_s=angular,aerodynamic_generalized_force_norm=aerodynamic_force,
        free_body_coupling_verified=True,biological_flight_verified=False)


def check_composed_body(dt=1e-5):
    """Compatibility with the current neighboring modules, in a new local model."""
    from flygym import Simulation
    from flygym.compose import NeuroMechFly, FlatGroundWorld, KinematicPosePreset
    from flygym.anatomy import Skeleton, AxisOrder, JointPreset
    from flygym.utils.math import Rotation3D
    from leg_muscles import add_leg_muscles
    from proboscis_muscles import add_proboscis_muscles
    from flight_integration import (add_flight_mechanics, bind_flight_motor_units,
        FlightMotorUnits, AIR_DENSITY, AIR_VISCOSITY, WING_CONTACT_SHELL_MM)
    fly=NeuroMechFly(name='fly')
    fly.add_joints(Skeleton(axis_order=AxisOrder.YAW_PITCH_ROLL,joint_preset=JointPreset.LEGS_ONLY),
                   KinematicPosePreset.NEUTRAL,stiffness=.01,damping=.01)
    legs=add_leg_muscles(fly)
    proboscis=add_proboscis_muscles(fly)
    records=add_flight_mechanics(fly)
    rows=json.loads(((Path(__file__).resolve().parents[1] / 'runtime')/'neural-motor/malecns-motor-map.json').read_text())['motors']
    units,_=bind_flight_motor_units(fly,records,rows)
    world=FlatGroundWorld()
    world.add_fly(fly,[0,0,5],Rotation3D('quat',[1,0,0,0]),bodysegs_with_ground_contact=[])
    world.mjcf_root.option.timestep=dt
    world.mjcf_root.option.gravity=(0,0,0)
    world.mjcf_root.option.density=AIR_DENSITY
    world.mjcf_root.option.viscosity=AIR_VISCOSITY
    world.mjcf_root.option.integrator=mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    world.mjcf_root.option.iterations=100
    world.mjcf_root.option.tolerance=1e-12
    world.mjcf_root.compiler.fusestatic=False
    sim=Simulation(world)
    model,data=sim.mj_model,sim.mj_data
    bank=FlightMotorUnits(model,units)
    other=model.actuator(legs[0]['actuator_name']).id
    data.ctrl[other]=.001
    mujoco.mj_forward(model,data)
    bank.advance(data,np.zeros(len(bank.ids),int))
    assert data.ctrl[other]==.001  # bank must not clear another subsystem's controls
    data.ctrl[other]=0
    bank.reset()
    rng=np.random.default_rng(3)
    largest=0.
    initial_q=data.qpos.copy()
    schedule=rng.random((10000,len(bank.ids)))<50*1e-5
    factor=round(1e-5/dt)
    for step in range(10000*factor):
        # Independent random spikes are a stress-test input only, never a runtime drive.
        # Half-dt comparison preserves these exact event timestamps.
        events=schedule[step//factor] if step%factor==factor-1 else np.zeros(len(bank.ids),bool)
        mujoco.mj_forward(model,data)
        bank.advance(data,events)
        mujoco.mj_step(model,data)
        largest=max(largest,float(np.max(abs(data.efc_pos))))
    assert np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()
    assert sum(w.number for w in data.warning)==0 and largest<WING_CONTACT_SHELL_MM/2
    displacement=np.zeros(model.nv)
    mujoco.mj_differentiatePos(model,displacement,1.,initial_q,data.qpos)
    return dict(leg_paths=len(legs),proboscis_paths=len(proboscis),flight_paths=len(records),
        nq=model.nq,nu=model.nu,duration_s=.1,maximum_pin_error_mm=largest,
        maximum_ifm_strain=max(abs(x['strain']) for x in bank.last_forces.values()),
        pin_error_budget_mm=WING_CONTACT_SHELL_MM/2,_displacement=displacement,
        other_controls_preserved=True,input_kind='synthetic stress test, not neural behavior')


def main():
    dt = 0.0001
    normal, blocked = StretchActivatedMuscle(dt), StretchActivatedMuscle(dt)
    first_active = None
    for tick in range(1000):
        event = tick in (0, 117, 309, 578, 803)  # synthetic irregular events
        a = normal.advance(1, event)
        b = blocked.advance(1, event, release_block=True)
        assert b['active_force_uN'] == 0
        assert b['passive_force_uN'] == a['passive_force_uN'] == 28
        if a['active_force_uN'] > 0 and first_active is None:
            first_active = tick
    assert first_active == 11
    assert normal.nmj.delivered == 5 and blocked.nmj.delivered == 0

    # Matched priming lets strain, rather than a clock or neural spike, alter force.
    muscles = [StretchActivatedMuscle(dt) for _ in range(3)]
    for m in muscles:
        for tick in range(1000):
            m.advance(1, tick in (0, 117, 309, 578, 803))
    normalized_sa = []
    for _ in range(500):
        base, stretch, shorten = [m.advance(length) for m, length in zip(muscles, (1, 1.01, .99))]
        assert stretch['active_force_uN'] >= base['active_force_uN']
        assert shorten['active_force_uN'] <= base['active_force_uN']
        normalized_sa.append(stretch['stretch_stress_pa'] / stretch['activation'])
    p = muscles[0].p
    peak_time = math.log(p.stretch_decay_s / p.stretch_rise_s) / (
        1 / p.stretch_rise_s - 1 / p.stretch_decay_s)
    observed_peak = (int(np.argmax(normalized_sa)) + .5) * dt
    assert abs(observed_peak - peak_time) < dt
    assert normalized_sa[-1] < .02 * max(normalized_sa)

    # A still fiber has zero stretch contribution despite continued excitation.
    assert base['stretch_stress_pa'] == 0
    normal.reset()
    assert normal.advance(1)['active_force_uN'] == 0 and not normal.nmj.pending
    must_reject(lambda: normal.advance(1.1))
    must_reject(lambda: normal.advance(float('nan')))
    must_reject(lambda: StretchActivatedMuscle(dt, replace(p, area_mm2=-1)))
    must_reject(lambda: free_wing_xml(fluid_coefficients=(1, 2)))

    def material_trace(step):
        m = StretchActivatedMuscle(step)
        trace = []
        events = {round(t / step) - 1 for t in (.002, .017, .041)}
        for tick in range(round(.08 / step)):
            # External isometric length step, not a commanded animal trajectory.
            f = m.advance(1.01 if tick * step >= .03 else 1, tick in events)
            trace.append(f['active_force_uN'])
        return np.array(trace)

    coarse, fine = material_trace(dt), material_trace(dt / 2)
    relative_error = float(np.max(abs(coarse - fine.reshape(-1, 2).mean(axis=1))) / max(fine))
    assert relative_error < .02

    # Native tendon: pulling force has the correct sign and virtual-work units.
    fixture = '''<mujoco><option timestep="0.00001" gravity="0 0 0"/>
      <worldbody><site name="origin" pos="0 0 0"/>
        <body pos="1 0 0"><joint type="slide" axis="1 0 0"/>
          <geom type="sphere" size="0.05" mass="0.001"/>
          <site name="insertion"/></body></worldbody>
      <tendon><spatial name="fiber"><site site="origin"/>
        <site site="insertion"/></spatial></tendon>
      <actuator><motor tendon="fiber" gear="-1"/></actuator></mujoco>'''
    model = mujoco.MjModel.from_xml_string(fixture)
    data = mujoco.MjData(model)
    m = muscles[0]
    mujoco.mj_forward(model, data)
    tension = m.advance(float(data.ten_length[0]))['tension_uN']
    data.ctrl[0], data.qvel[0] = tension, -.1
    mujoco.mj_forward(model, data)
    assert np.isclose(data.qfrc_actuator[0], -tension)
    assert np.isclose(data.qfrc_actuator @ data.qvel, -tension * data.ten_velocity[0])
    before = data.qpos[0]
    mujoco.mj_step(model, data)
    assert data.qpos[0] < before and np.isfinite(data.qpos).all()

    # Actual free dynamics; only initial velocity is set, with no actuator at all.
    fluid_power = {}
    for side in ('left', 'right'):
        model = mujoco.MjModel.from_xml_string(free_wing_xml(side=side))
        data = mujoco.MjData(model)
        assert model.nu == 0 and model.nv == 6
        assert np.isclose(model.body_mass[1], 8e-6)
        mujoco.mj_forward(model, data)
        assert np.all(data.qfrc_passive == 0)
        data.qvel[:3] = (1000, 300, -200)  # mm/s: external initial condition
        mujoco.mj_forward(model, data)
        power = float(data.qfrc_passive @ data.qvel)
        assert power < 0
        fluid_power[side] = power
        for _ in range(100):
            mujoco.mj_step(model, data)
        assert np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()
        assert sum(w.number for w in data.warning) == 0
        vacuum = mujoco.MjModel.from_xml_string(free_wing_xml(
            side=side, density_g_per_mm3=0, viscosity_g_per_mm_s=0))
        v = mujoco.MjData(vacuum)
        v.qvel[:3] = (1000, 300, -200)
        mujoco.mj_forward(vacuum, v)
        assert np.all(v.qfrc_passive == 0)

    thorax = check_thorax()
    contacts = check_wing_contacts()
    integration = check_body_integration()
    composition = check_composed_body()
    fine_composition=check_composed_body(5e-6)
    composition['half_dt_relative_error']=float(np.linalg.norm(
        composition.pop('_displacement')-fine_composition['_displacement'])/
        np.linalg.norm(fine_composition['_displacement']))
    composition['half_dt_maximum_pin_error_mm']=fine_composition['maximum_pin_error_mm']
    assert composition['half_dt_relative_error']<.01 and fine_composition['maximum_pin_error_mm']<1e-4
    print(json.dumps(dict(status='PASS', scope='local NeuroMechFly flight attachment and component mechanics',
        mujoco_version=mujoco.__version__, nmj_first_active_tick=first_active,
        stretch_peak_s=observed_peak, stretch_analytic_peak_s=peak_time,
        normalized_peak_stretch_stress_pa=max(normalized_sa),
        half_dt_relative_error=relative_error, initial_fluid_power_nW=fluid_power,
        reduced_thorax=thorax, wing_contacts=contacts, body_integration=integration, composed_body=composition,
        local_body_motor_rows_bound=integration['mapped_motor_ids'], central_neural_run_verified=False,
        biological_flight_verified=False), indent=2))


if __name__ == '__main__':
    main()
