"""Estimated flight anatomy attached to the actual NeuroMechFly body, mm-g-s.

Build before world attachment. No graph imports, policy, desired motion or stepping
of the physics engine. Main owns neuron IDs, the neural clock and mj_step.
See docs/research/whole-body-flight-mechanics.md for geometry and coverage limits.
"""
from dataclasses import asdict, replace
import math
import warnings

import mujoco as mj
import numpy as np
from flygym.anatomy import BodySegment

from flight_mechanics import IFMParameters, StretchActivatedMuscle
from neuromuscular import NeuromuscularJunction


AIR_DENSITY = 1.28e-6  # g/mm^3
AIR_VISCOSITY = 1.85e-5  # g/(mm s)
PHYSICS_DT_MAX = 1e-5
WING_CONTACT_SHELL_MM = .0005  # estimated numerical skin around each source triangle
SEGMENTATION_SOURCE = 'https://zenodo.org/records/5000357'
SEGMENTATION_MD5 = '49b440960e59d903422eab5e00ca5e5f'
TOPOLOGY_SOURCE = 'https://www.nature.com/articles/s41586-024-07293-4/figures/1'
HALTERE_SOURCE = 'https://pubmed.ncbi.nlm.nih.gov/31607538/'
# Proximal-minus-distal geometric end caps in calibrated image x,y,z (mm).
# These are estimated belly axes, not verified muscle/tendon insertion landmarks.
MUSCLE_AXES = {
    'i1': (-.21534, .18078, .03024), 'i2': (.01620, .25104, .02335),
    'b1': (-.14452, -.10297, -.04126), 'b2': (-.16381, .14375, .08007),
    'b3': (.17369, -.10177, -.01672), 'iii1': (-.14640, .17538, -.00093),
    'iii3': (-.03883, .08505, .04213), 'iii2_4': (-.08098, .08648, -.01360),
    'hg1': (-.04010, .16858, .07786), 'hg2': (.00570, .08632, .02622),
    'hg3': (.00080, .18939, .08736), 'hg4': (.01316, .09357, .03003),
}
STEERING_NMJ = dict(delay_s=.001, tau_exc_s=.002, tau_recovery_s=.1,
                    spike_gain=.2, depression=.2)


def _unit(vector):
    vector = np.asarray(vector, dtype=float)
    length = np.linalg.norm(vector)
    if not np.isfinite(vector).all() or length < 1e-10:
        raise ValueError('Degenerate anatomical axis')
    return vector / length


def _appendage_frame(model, data, name, root):
    """Mesh principal axes, expressed in thorax coordinates; no pose change."""
    body, geom = data.body(name), data.geom(name)
    mid = model.geom(name).dataid[0]
    if model.geom(name).type[0] != mj.mjtGeom.mjGEOM_MESH or mid < 0:
        raise ValueError(f'{name} needs its existing anatomical mesh')
    start, count = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
    vertices = model.mesh_vert[start:start+count] @ geom.xmat.reshape(3, 3).T + geom.xpos
    rr = root.xmat.reshape(3, 3)
    vertices = (vertices-root.xpos) @ rr
    pivot = (body.xpos-root.xpos) @ rr
    center = vertices.mean(axis=0)
    values, axes = np.linalg.eigh(np.cov(vertices.T))
    span = axes[:, -1] * (1 if np.dot(axes[:, -1], center-pivot) > 0 else -1)
    chord = axes[:, -2]
    if chord[0] < 0:
        chord = -chord
    normal = _unit(np.cross(chord, span))
    # A geometric surface normal is a polar direction, mirrored like a point.
    # Keep it dorsally oriented on both sides; use a proper rotation for the geom.
    if normal[2] < 0:
        normal = -normal
    basis = np.column_stack((chord, span, normal))
    if np.linalg.det(basis) < 0:
        basis[:, 0] *= -1
    projected = vertices @ basis
    radii = np.maximum(np.ptp(projected, axis=0)/2, .003)
    center = ((projected.max(axis=0)+projected.min(axis=0))/2) @ basis.T
    rotation = rr.T @ body.xmat.reshape(3, 3)
    return dict(pivot=pivot, rotation=rotation, span=span, chord=chord,
                normal=normal, basis=basis, radii=radii, center=center)


def _wing_contact_patches(fly, model, data, wing_name, prefix):
    """Exact source-triangle prisms preserve camber, not the global convex hull.

    Every nondegenerate source triangle receives a 0.5-um solid skin. Nothing
    fills between adjacent patches; duplicate faces are removed. This does not
    repair intersections in the source pose or infer a biological wing thickness.
    """
    gid = model.geom(wing_name).id
    mid = model.geom_dataid[gid]
    start, count = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
    vertices = model.mesh_vert[start:start+count] @ data.geom_xmat[gid].reshape(3,3).T + data.geom_xpos[gid]
    owner = data.body(wing_name)
    vertices = (vertices-owner.xpos) @ owner.xmat.reshape(3,3)
    start, count = model.mesh_faceadr[mid], model.mesh_facenum[mid]
    faces = model.mesh_face[start:start+count]
    _, indices = np.unique(np.sort(faces,axis=1),axis=0,return_index=True)
    triangles = vertices[faces[np.sort(indices)]]
    normals = np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    magnitudes = np.linalg.norm(normals,axis=1)
    omitted_area = float(magnitudes[magnitudes<=2e-12].sum()/2)
    triangles,normals = triangles[magnitudes>2e-12],normals[magnitudes>2e-12]
    normals /= np.linalg.norm(normals,axis=1)[:,None]
    body = fly.bodyseg_to_mjcfbody[BodySegment(wing_name)]
    names = []
    for i,(triangle,normal) in enumerate(zip(triangles,normals)):
        padding=normal*WING_CONTACT_SHELL_MM/2
        prism=np.r_[triangle-padding,triangle+padding]
        name = prefix+'wing_contact_'+str(i)
        fly.mjcf_root.add_mesh(name=name, scale=(1,1,1),
                              uservert=prism.ravel())
        body.add_geom(name=name,type=mj.mjtGeom.mjGEOM_MESH,meshname=name,
            mass=0,contype=1,conaffinity=7,group=5,rgba=(0,0,0,0),
            friction=model.geom_friction[gid],solref=model.geom_solref[gid],
            solimp=model.geom_solimp[gid],condim=int(model.geom_condim[gid]),
            margin=float(model.geom_margin[gid]),gap=float(model.geom_gap[gid]))
        names.append(f'{fly.name}/{name}')
    return dict(contact_geom_names=names,visual_geom_names=[f'{fly.name}/{wing_name}'],
        source_mesh_name=wing_name,source_triangle_count=int(count),
        unique_surface_triangles=len(triangles),omitted_degenerate_area_mm2=omitted_area,
        patch_count=len(triangles),maximum_local_envelope_mm=0.,
        shell_thickness_mm=WING_CONTACT_SHELL_MM,source_pose_changed=False,
        mass_added_g=0.,geometry_status='source_triangle_prisms_with_estimated_normal_padding',
        source_rest_intersections='Original mirrored folded surfaces intersect; explicit open-wing reference replaces that initial pose')


def add_flight_mechanics(fly):
    """Add bilateral body-coupled mechanics; return semantic list[dict] records.

    Wing hinges/meshes/masses are retained; a static open-wing initial condition
    replaces the intersecting mirrored folded source. Internal sclerites, rhombic
    scutal compliance and ligament dimensions are hypotheses. No CNS IDs are
    selected here. bind_flight_motor_units can allocate explicit caller rows.
    """
    spec = fly.mjcf_root
    if any(j.name.startswith('flight_') for j in spec.joints):
        raise ValueError('Flight mechanics already added')
    names = ['c_thorax', 'l_wing', 'r_wing', 'l_haltere', 'r_haltere']
    bodies = {n: fly.bodyseg_to_mjcfbody[BodySegment(n)] for n in names}
    if any(list(bodies[n].joints) for n in names[1:]):
        raise ValueError('Add flight mechanics before declaring wing/haltere joints')
    # Match the world compiler: hidden mass/inertia floors would invalidate the
    # internal mass partition (FlyGym's standalone fly defaults clamp tiny parts).
    spec.compiler.boundmass = 0
    spec.compiler.boundinertia = 0
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        model, data = fly.compile()
    data.qpos[:] = fly._get_neutral_qpos(model)
    mj.mj_kinematics(model, data)
    mj.mj_comPos(model, data)
    root = data.body('c_thorax')
    frames = {n: _appendage_frame(model, data, n, root) for n in names[1:]}
    fly.flight_reference_pose = {}
    for side,letter,sign in [('L','l',1),('R','r',-1)]:
        name=letter+'_wing'
        frame=frames[name]
        source_quat=np.array(bodies[name].quat,copy=True)
        # Static initial condition: lateral span and dorsal surface normal.
        # This rigid rotation preserves source camber and the anatomical hinge.
        target_basis=np.diag((sign,sign,1.))
        rotation=target_basis @ frame['basis'].T @ frame['rotation']
        quaternion=np.zeros(4)
        mj.mju_mat2Quat(quaternion,rotation.reshape(9))
        bodies[name].quat=quaternion
        fly.flight_reference_pose[side]=dict(
            condition='explicit_open_wing_initial_condition_not_biological_rest',
            source_body_quat=source_quat.tolist(),initial_body_quat=quaternion.tolist(),
            hinge_position_mm=np.asarray(bodies[name].pos).tolist(),
            target_span_thorax=[0,sign,0],target_normal_thorax=[0,0,1],
            source_problem='Mirrored folded source surfaces intersect',dynamic_pose_commands=False)
    # Derive all attachment/reference transforms AFTER the static repose.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        model,data=fly.compile()
    data.qpos[:]=fly._get_neutral_qpos(model)
    mj.mj_kinematics(model,data)
    mj.mj_comPos(model,data)
    root=data.body('c_thorax')
    frames={n:_appendage_frame(model,data,n,root) for n in names[1:]}
    poses = {'c_thorax': (np.zeros(3), np.eye(3))}
    poses.update({n: (f['pivot'], f['rotation']) for n, f in frames.items()})
    records, side_notum, side_haltere, added_bodies = [], {}, {}, []
    fly.flight_contact_geometry = {}

    def site(owner, name, point):
        origin, rotation = poses[owner]
        local = rotation.T @ (np.asarray(point)-origin)
        bodies[owner].add_site(name=name, pos=local, size=(.004, 0, 0))
        return dict(local_name=name, body=owner, pos_mm=local.tolist(),
                    reference_thorax_mm=np.asarray(point).tolist())

    def body(parent, name, point, mass=5e-8):
        origin, rotation = poses[parent]
        quat = np.zeros(4)
        mj.mju_mat2Quat(quat, rotation.T.reshape(9))
        bodies[name] = bodies[parent].add_body(name=name,
            pos=rotation.T @ (np.asarray(point)-origin), quat=quat)
        poses[name] = (np.asarray(point), np.eye(3))
        added_bodies.append(name)
        bodies[name].add_geom(type=mj.mjtGeom.mjGEOM_SPHERE, size=(.008, 0, 0),
                             mass=mass, contype=0, conaffinity=0, rgba=(.3, .6, .8, .4))
        return name

    def joint(owner, name, axis, *, slide=False, stiffness=.03, damping=.0001):
        return bodies[owner].add_joint(name=name,
            type=mj.mjtJoint.mjJNT_SLIDE if slide else mj.mjtJoint.mjJNT_HINGE,
            axis=poses[owner][1].T @ _unit(axis), stiffness=stiffness, damping=damping,
            armature=0, limited=False)

    def link_inertia(owner, endpoint):
        """Put a link's existing mass along its actual length, not at its pivot."""
        origin, rotation = poses[owner]
        g = bodies[owner].geoms[0]
        g.type = mj.mjtGeom.mjGEOM_CAPSULE
        g.fromto = np.r_[np.zeros(3), rotation.T @ (np.asarray(endpoint)-origin)]
        g.size = (.008, 0, 0)

    def pin(a, b, name):
        spec.add_equality(name=name, type=mj.mjtEq.mjEQ_CONNECT,
            name1=a['local_name'], name2=b['local_name'], objtype=mj.mjtObj.mjOBJ_SITE,
            solref=(.00002, 1), solimp=(.9999, .9999, .0001, .5, 2))

    def ligament(a, b, name, stiffness=20.):
        length = math.dist(a['reference_thorax_mm'], b['reference_thorax_mm'])
        if length < 1e-8:
            raise ValueError('Ligament needs distinct reference endpoints')
        tendon = spec.add_tendon(name=name, stiffness=stiffness, damping=0,
                                 springlength=(0, length), width=.002)
        tendon.wrap_site(a['local_name']); tendon.wrap_site(b['local_name'])

    def muscle(side, key, target, a, b, *, kind='synchronous', area=.0001,
               force=2.8, pool=None, fraction=1., geometry='estimated_registered_segment_axis'):
        name = 'flight_'+side+'_'+key.replace('.', '_')
        length = math.dist(a['reference_thorax_mm'], b['reference_thorax_mm'])
        if length < .001:
            raise ValueError(f'Degenerate muscle path {name}')
        tendon = spec.add_tendon(name=name+'_tendon', width=.003)
        tendon.wrap_site(a['local_name']); tendon.wrap_site(b['local_name'])
        p = replace(IFMParameters(), reference_length_mm=length, area_mm2=area,
                    passive_prestress_pa=0.)
        if kind == 'asynchronous':
            spec.add_actuator(name=name, trntype=mj.mjtTrn.mjTRN_TENDON,
                target=name+'_tendon', gear=(-1, 0, 0, 0, 0, 0),
                gaintype=mj.mjtGain.mjGAIN_FIXED, gainprm=[1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            force = area*p.isometric_stress_pa
        else:
            prm = [0, 1, force, 200, .5, 1.6, 10, 1.3, 1.2, 0]
            spec.add_actuator(name=name, trntype=mj.mjtTrn.mjTRN_TENDON,
                target=name+'_tendon', gear=(1, 0, 0, 0, 0, 0), lengthrange=(0, length),
                ctrllimited=True, ctrlrange=(0, 1), actlimited=True, actrange=(0, 1),
                dyntype=mj.mjtDyn.mjDYN_MUSCLE, dynprm=[.001, .004, 0, 0, 0, 0, 0, 0, 0, 0],
                gaintype=mj.mjtGain.mjGAIN_MUSCLE, gainprm=prm,
                biastype=mj.mjtBias.mjBIAS_MUSCLE, biasprm=prm)
        records.append(dict(semantic_muscle_key=key, peripheral_target_side=side,
            side='left' if side == 'L' else 'right', limb=key.split('.')[0],
            target_muscle=target, kind=kind, group_capacity_fraction=fraction,
            capacity_pool=pool or key, force_uN=force, area_mm2=area,
            pool_isometric_force_uN=force/fraction, pool_area_mm2=area/fraction,
            reference_length_mm=length, local_actuator_name=name,
            actuator_name=f'{fly.name}/{name}', local_tendon_name=name+'_tendon',
            tendon_name=f'{fly.name}/{name}_tendon', sites=[a, b],
            ifm_parameters=asdict(p) if kind == 'asynchronous' else None,
            nmj_parameters=dict(STEERING_NMJ) if kind == 'synchronous' else None,
            motor_neuron_ids=[], mapping_status='unmapped', geometry_status=geometry,
            parameter_status='estimated_not_behavior_fitted',
            topology_source=(HALTERE_SOURCE if key.startswith('haltere.') else
                'https://doi.org/10.1098/rstb.1985.0154' if key.startswith(('wing.ps','wing.tp')) else TOPOLOGY_SOURCE),
            geometry_source=SEGMENTATION_SOURCE if geometry=='estimated_registered_segment_axis' else None,
            segmentation_md5=SEGMENTATION_MD5 if geometry=='estimated_registered_segment_axis' else None,
            kinematic_joint_names=[f'{fly.name}/flight_{side}_'+
                ('haltere_'+mode if key.startswith('haltere.') else 'wing_'+mode)
                for mode in (('sweep','bend','torsion') if key.startswith('haltere.') else
                             ('stroke','elevation','pitch'))]))

    for side, letter, sign in [('L', 'l', 1), ('R', 'r', -1)]:
        prefix = 'flight_'+side+'_'
        wing_name, haltere_name = letter+'_wing', letter+'_haltere'
        f = frames[wing_name]
        pivot, span, chord, normal = (f[k] for k in ('pivot', 'span', 'chord', 'normal'))
        notum_point = pivot + np.array((.12, -sign*.18, .15))
        sternum = notum_point - (0, 0, .65)
        notum = body('c_thorax', prefix+'notum', notum_point, 1e-5)
        joint(notum, prefix+'notum_heave', (0, 0, 1), slide=True, stiffness=0, damping=0)
        top_site = site(notum, prefix+'notum_top', notum_point)
        side_notum[side] = site(notum, prefix+'scutellar_crosslink', notum_point + (-.1, 0, 0))
        dlm_sites = []
        for end, direction in [('anterior', 1), ('posterior', -1)]:
            corner = sternum + (direction*.45, 0, .325)
            lower = body('c_thorax', prefix+end, sternum, 2e-6)
            joint(lower, prefix+end+'_flexure', (0, 1, 0), stiffness=.1)
            # Distribute inertia along the actual link, not an artificial joint armature.
            g = bodies[lower].geoms[0]
            g.type = mj.mjtGeom.mjGEOM_CAPSULE
            g.fromto = np.r_[np.zeros(3), corner-sternum]; g.size = (.012, 0, 0)
            upper = body(lower, prefix+end+'_scutum', corner, 2e-6)
            joint(upper, prefix+end+'_scutal_flexure', (0, 1, 0), stiffness=.1)
            g = bodies[upper].geoms[0]
            g.type = mj.mjtGeom.mjGEOM_CAPSULE
            g.fromto = np.r_[np.zeros(3), notum_point-corner]; g.size = (.012, 0, 0)
            pin(site(upper, prefix+end+'_top', notum_point), top_site, prefix+end+'_closure')
            dlm_sites.append((lower, corner))
        for suffix, offset, area in [('a_b', .04, .02), ('c_f', -.02, .04)]:
            a = site(dlm_sites[0][0], prefix+'dlm_'+suffix+'_a', dlm_sites[0][1]+(0, sign*offset, 0))
            b = site(dlm_sites[1][0], prefix+'dlm_'+suffix+'_b', dlm_sites[1][1]+(0, sign*offset, 0))
            muscle(side, 'wing.dlm_'+suffix, 'DLM '+('a, b' if suffix=='a_b' else 'c-f'),
                   a, b, kind='asynchronous', area=area, geometry='estimated_thoracic_fiber_family')
        for suffix, x, area in [('1_a_c', .2, .03), ('2_a_b', 0., .02), ('3_a_b', -.2, .02)]:
            a = site('c_thorax', prefix+'dvm_'+suffix+'_a', sternum+(x, 0, 0))
            b = site(notum, prefix+'dvm_'+suffix+'_b', notum_point+(x, 0, 0))
            muscle(side, 'wing.dvm'+suffix, 'DVM '+suffix.replace('_a_c', 'a-c').replace('_a_b', 'a, b'),
                   a, b, kind='asynchronous', area=area, geometry='estimated_thoracic_fiber_family')

        pleural_base = pivot + (.05, -sign*.03, -.4)
        pleura = body('c_thorax', prefix+'pleural_plate', pleural_base, 2e-6)
        link_inertia(pleura, pivot)
        joint(pleura, prefix+'pleural_ap_flexure', (1, 0, 0), stiffness=.3)
        joint(pleura, prefix+'pleural_dv_flexure', (0, 1, 0), stiffness=.3)
        pwp = site(pleura, prefix+'PWP', pivot)
        for axis_name, axis in [('x', (1,0,0)), ('y',(0,1,0)), ('z',(0,0,1))]:
            joint(wing_name, prefix+'wing_translation_'+axis_name, axis, slide=True, stiffness=0, damping=0)
        for mode, axis in [('stroke', normal), ('elevation', chord), ('pitch', span)]:
            joint(wing_name, prefix+'wing_'+mode, axis, stiffness=.01)
        pin(site(wing_name, prefix+'wing_PWP', pivot), pwp, prefix+'PWP_joint')
        for geom in fly.bodyseg_to_mjcfgeom[BodySegment(wing_name)]:
            geom.contype = geom.conaffinity = 0
        fly.flight_contact_geometry[side] = _wing_contact_patches(fly,model,data,wing_name,prefix)
        fly.flight_contact_geometry[side]['reference_pose']=fly.flight_reference_pose[side]
        fly.flight_contact_geometry[side]['source_pose_changed']=True
        quat = np.zeros(4)
        mj.mju_mat2Quat(quat, (f['rotation'].T @ f['basis']).reshape(9))
        bodies[wing_name].add_geom(name=prefix+'wing_air', type=mj.mjtGeom.mjGEOM_ELLIPSOID,
            pos=f['rotation'].T @ (f['center']-pivot), quat=quat, size=f['radii'],
            mass=0, contype=0, conaffinity=0, fluid_ellipsoid=1,
            fluid_coefs=(.5,.25,1.5,1,1), rgba=(.5,.7,1,.15))
        site(wing_name, prefix+'wing_tip', pivot+span*2*f['radii'][1])

        ax1_prox = pivot-.12*span+.04*normal
        ax1_dist = pivot-.04*span+.015*chord
        ax1 = body(notum, prefix+'ax1', ax1_prox)
        link_inertia(ax1, ax1_dist)
        rod = _unit(ax1_dist-ax1_prox)
        axis1 = _unit(np.cross(rod, chord))
        joint(ax1, prefix+'ax1_flexure_1', axis1)
        joint(ax1, prefix+'ax1_flexure_2', np.cross(rod, axis1))
        pin(site(ax1, prefix+'ax1_distal', ax1_dist),
            site(wing_name, prefix+'ax2_medial', ax1_dist), prefix+'ax1_ax2_joint')

        basalare = body(pleura, prefix+'basalare', pivot+.07*chord-.03*span)
        joint(basalare, prefix+'basalare_flexure_1', normal)
        joint(basalare, prefix+'basalare_flexure_2', span)
        basalare_tip = pivot+.07*chord-.09*span-.02*normal
        link_inertia(basalare, basalare_tip)
        ligament(site(basalare, prefix+'basalare_ligament', basalare_tip),
            site(wing_name, prefix+'radial_ligament', pivot+.12*span+.04*chord), prefix+'basalare_radial')
        ax3_point = pivot+.025*span-.05*chord
        ax3 = body(wing_name, prefix+'ax3', ax3_point)
        link_inertia(ax3, ax3_point+.025*span-.015*normal)
        joint(ax3, prefix+'ax3_flexure', span)
        ax4_point = pivot-.08*chord-.03*span
        ax4 = body(notum, prefix+'ax4', ax4_point)
        link_inertia(ax4, ax4_point+.035*span)
        joint(ax4, prefix+'ax4_flexure_1', span)
        joint(ax4, prefix+'ax4_flexure_2', normal)
        # The ax4-canoe-ax3 path is an elastic link, not a prescribed pitch relation.
        ligament(site(ax4, prefix+'canoe_prox', ax4_point+.02*span),
            site(ax3, prefix+'canoe_dist', ax3_point-.01*chord), prefix+'canoe', stiffness=40)
        ligament(site(ax3, prefix+'anal_prox', ax3_point+.015*normal),
            site(wing_name, prefix+'anal_spar', pivot+.12*span-.07*chord), prefix+'ax3_anal', stiffness=40)

        for slug, image_axis in MUSCLE_AXES.items():
            owner, insertion = ((basalare, basalare_tip) if slug.startswith('b') else
                (ax1, ax1_dist-.015*rod) if slug in ('i1','i2') else
                (ax3, ax3_point-.02*normal) if slug.startswith('iii') else
                (ax4, ax4_point+(.01 if slug in ('hg1','hg2') else -.01)*chord))
            image_axis = np.asarray(image_axis)
            direction = np.array((-image_axis[0], -sign*image_axis[2], -image_axis[1]))
            origin = insertion + direction*(1+.03/np.linalg.norm(direction))
            a = site(pleura, prefix+slug+'_origin', origin)
            b = site(owner, prefix+slug+'_insertion', insertion)
            muscle(side, 'wing.'+slug, slug, a, b)
        for slug, height in [('ps1', .05), ('ps2', .12)]:
            a = site('c_thorax', prefix+slug+'_origin', sternum+(.05,0,height))
            b = site(pleura, prefix+slug+'_insertion', pleural_base+(-.03,-sign*.04,.1))
            muscle(side, 'wing.'+slug, slug, a, b, geometry='estimated_pleurosternal_topology')
        for slug, x in [('tp1', .03), ('tp2', -.03), ('tp', 0.)]:
            a = site(pleura, prefix+slug+'_origin', pleural_base+(x,0,.23))
            b = site(notum, prefix+slug+'_insertion', ax1_prox+.04*chord)
            muscle(side, 'wing.'+slug, slug, a, b, force=2.8,
                   pool='wing.tergopleural_complex', fraction=1/3,
                   geometry='estimated_tergopleural_common_tendon_topology')

        hf = frames[haltere_name]
        hp, hs, hc, hn = (hf[k] for k in ('pivot','span','chord','normal'))
        for mode, axis in [('sweep', hn), ('bend', hc), ('torsion', hs)]:
            joint(haltere_name, prefix+'haltere_'+mode, axis, stiffness=.01, damping=.00002)
        # Tiny apodeme arms keep asynchronous fiber strain small at large stalk excursions.
        hpower = hp-.005*hs+.003*hc
        muscle(side, 'haltere.hDVM', 'hDVM',
            site('c_thorax', prefix+'hDVM_origin', hp+(.12,-sign*.12,.12)),
            site(haltere_name, prefix+'hDVM_insertion', hpower),
            kind='asynchronous', area=.0005, geometry='estimated_haltere_power_apodeme')
        for slug, offset in [('hi1', -.004), ('hi2', -.007), ('hiii2', .005),
                             ('hb1', -.003), ('hb2', -.006), ('hiii1', .008), ('hiii3', .003)]:
            # Known muscles may lack a resolved CNS target; no identity is invented.
            distal = hp+offset*hs+(.004 if 'iii' in slug else -.004)*hc
            proximal = hp+(.04 if slug in ('hb1','hb2') else -.04, -sign*.035, -.07)
            muscle(side, 'haltere.'+slug, slug,
                site('c_thorax', prefix+slug+'_origin', proximal),
                site(haltere_name, prefix+slug+'_insertion', distal),
                force=.28, area=.00001, geometry='estimated_haltere_axillary_or_basalar_apodeme')
        side_haltere[side] = site(haltere_name, prefix+'haltere_link', hp-.004*hs)
        ligament(site(pleura, prefix+'subepimeral_link', hp+(.04,-sign*.02,.02)),
                  side_haltere[side], prefix+'subepimeral', stiffness=2.)
    # Finite passive scutellar coupling; no equality of wing phases or angles.
    ligament(side_notum['L'], side_notum['R'], 'flight_scutellar_crosslink', stiffness=20.)
    # Reduced bending energy of the scutellar bridge: k*(hL-hR)^2/2.
    # Unlike a transverse string, this has linear stiffness to differential heave.
    bending = spec.add_tendon(name='flight_scutellar_bending', stiffness=20.,
                              damping=.001, springlength=(0,0))
    bending.wrap_joint('flight_L_notum_heave', 1.)
    bending.wrap_joint('flight_R_notum_heave', -1.)
    fly._rebuild_neutral_keyframe()
    fly.flight_mass_budget = _reallocate_thorax_inertia(fly, model, added_bodies)
    fly._rebuild_neutral_keyframe()
    for record in records:
        record['mass_budget'] = fly.flight_mass_budget
        if record['limb'] == 'wing':
            record['contact_geometry_key'] = record['peripheral_target_side']
    return records


def _reallocate_thorax_inertia(fly, source_model, internal_names):
    """Subtract new internal rigid bodies from native thorax spatial inertia.

    Total mass, COM and inertia are preserved across the internal partition at
    the current open-wing reference pose (initialized before this calculation).
    Deformation then redistributes this mass physically. Refuse nonphysical
    residual inertia rather than silently adding mass or an artificial armature.
    """
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        model, data = fly.compile()
    mj.mj_kinematics(model, data)
    mj.mj_comPos(model, data)
    source = source_model.body('c_thorax')
    total = float(source.mass[0])
    rotation = np.zeros(9)
    mj.mju_quat2Mat(rotation, source.iquat)
    rotation = rotation.reshape(3,3)
    center = np.array(source.ipos)
    def shift(mass, position):
        return mass*(np.dot(position,position)*np.eye(3)-np.outer(position,position))
    inertia = rotation @ np.diag(source.inertia) @ rotation.T + shift(total,center)
    moment = total*center
    parent = data.body('c_thorax')
    parent_rotation = parent.xmat.reshape(3,3)
    allocated = 0.
    for name in internal_names:
        b, d = model.body(name), data.body(name)
        mass = float(b.mass[0])
        position = parent_rotation.T @ (d.xipos-parent.xpos)
        basis = parent_rotation.T @ d.ximat.reshape(3,3)
        inertia -= basis @ np.diag(b.inertia) @ basis.T + shift(mass, position)
        moment -= mass*position
        allocated += mass
    remaining = total-allocated
    if remaining <= 0:
        raise ValueError('Flight internal mass exceeds the original thorax mass')
    center = moment/remaining
    principal, axes = np.linalg.eigh(inertia-shift(remaining,center))
    if min(principal) <= 0 or max(principal) >= sum(principal)-max(principal):
        raise ValueError('Flight geometry leaves a nonphysical residual thorax inertia')
    if np.linalg.det(axes) < 0:
        axes[:,0] *= -1
    quaternion = np.zeros(4)
    mj.mju_mat2Quat(quaternion, axes.reshape(9))
    thorax = fly.bodyseg_to_mjcfbody[BodySegment('c_thorax')]
    thorax.mass, thorax.ipos = remaining, center
    thorax.inertia, thorax.iquat = principal, quaternion
    thorax.explicitinertial = True
    return dict(native_thorax_mass_g=total, allocated_internal_mass_g=allocated,
                residual_thorax_mass_g=remaining, net_added_mass_g=0.,
                reference_spatial_inertia_preserved=True,
                allocation_status='estimated_internal_partition_not_measured')


def bind_flight_motor_units(fly, records, motor_rows):
    """Bind caller-provided exact semantic/side rows, sharing each path's capacity.

    Returns (unit_records, linked_IDs). Unmatched paths retain a passive-only unit
    with bodyId=None so IFM passive tension is computed even without innervation.
    """
    motor_rows = list(motor_rows)
    if (any(type(r['bodyId']) is not int or r['bodyId'] <= 0 for r in motor_rows)
            or len({r['bodyId'] for r in motor_rows}) != len(motor_rows)):
        raise ValueError('CNS motor IDs must be unique positive integers')
    if any(r.get('binding_finalized') for r in records):
        raise ValueError('Flight records already bound')
    units, linked = [], set()
    for r in records:
        matches = [m for m in motor_rows if m.get('semantic_muscle_key') == r['semantic_muscle_key']
                   and m.get('peripheral_target_side') == r['peripheral_target_side']
                   and m.get('evidence_status') == 'supported_at_stated_resolution']
        r['motor_neuron_ids'] = [m['bodyId'] for m in matches]
        r['binding_finalized'] = True
        r['mapping_status'] = 'named_target_side_with_estimated_capacity' if matches else 'unmapped'
        original = next(a for a in fly.mjcf_root.actuators if a.name == r['local_actuator_name'])
        for motor in matches or [None]:
            fraction = 1/max(1,len(matches))
            name = r['local_actuator_name'] if motor is None else r['local_actuator_name']+'_mn'+str(motor['bodyId'])
            if motor is not None:
                gain, bias = np.array(original.gainprm), np.array(original.biasprm)
                if r['kind'] == 'synchronous':
                    gain[2] *= fraction; bias[2] *= fraction
                fly.mjcf_root.add_actuator(name=name, trntype=original.trntype,
                    target=r['local_tendon_name'], gear=np.array(original.gear),
                    lengthrange=np.array(original.lengthrange),
                    ctrllimited=original.ctrllimited, ctrlrange=np.array(original.ctrlrange),
                    actlimited=original.actlimited, actrange=np.array(original.actrange),
                    dyntype=original.dyntype, dynprm=np.array(original.dynprm),
                    gaintype=original.gaintype, gainprm=gain,
                    biastype=original.biastype, biasprm=bias)
                linked.add(motor['bodyId'])
            unit = dict(r, bodyId=None if motor is None else motor['bodyId'],
                        actuator_name=f'{fly.name}/{name}',
                        capacity_fraction=fraction*r['group_capacity_fraction'],
                        within_path_capacity_fraction=fraction,
                        force_uN=r['force_uN']*fraction, area_mm2=r['area_mm2']*fraction,
                        side_evidence=None if motor is None else motor['peripheral_side_method'],
                        target_evidence=None if motor is None else motor['assignment_method'],
                        passive_only=motor is None,
                        capacity_assumption='Equal motor-unit shares within the named muscle/family')
            if r['kind'] == 'asynchronous':
                unit['ifm_parameters'] = dict(r['ifm_parameters'], area_mm2=unit['area_mm2'])
            units.append(unit)
        if matches:
            fly.mjcf_root.delete(original)
    fly._rebuild_neutral_keyframe()
    return units, linked


class FlightMotorUnits:
    """Independent per-MN NMJ/muscle states; update owned controls, never mj_step."""

    def __init__(self, model, units):
        if not 0 < model.opt.timestep <= PHYSICS_DT_MAX:
            raise ValueError('Flight mechanics requires a physics timestep <= 10 us')
        self.ids = sorted({u['bodyId'] for u in units if u['bodyId'] is not None})
        self.index = {body_id:i for i,body_id in enumerate(self.ids)}
        self.units, self.states, self.actuators, self.tendons = units, [], [], []
        for u in units:
            state = (StretchActivatedMuscle(model.opt.timestep, IFMParameters(**u['ifm_parameters']))
                     if u['kind'] == 'asynchronous' else
                     NeuromuscularJunction(model.opt.timestep, u['nmj_parameters']))
            self.states.append(state)
            self.actuators.append(model.actuator(u['actuator_name']).id)
            self.tendons.append(model.tendon(u['tendon_name']).id)
        self.last_forces = {}

    def reset(self):
        for state in self.states:
            state.reset()
        self.last_forces.clear()

    def advance(self, data, spikes, *, release_block=False):
        events = np.asarray(spikes)
        if events.shape != (len(self.ids),) or not np.isin(events, [0,1]).all() or type(release_block) is not bool:
            raise ValueError('One binary end-of-step event per bank.ids motor is required')
        for u, state, aid, tid in zip(self.units, self.states, self.actuators, self.tendons):
            event = False if u['bodyId'] is None else bool(events[self.index[u['bodyId']]])
            if u['kind'] == 'asynchronous':
                result = state.advance(float(data.ten_length[tid]), event, release_block=release_block)
                data.ctrl[aid] = result['tension_uN']
                self.last_forces[u['actuator_name']] = result
            else:
                data.ctrl[aid] = state.advance(event, release_block=release_block)
