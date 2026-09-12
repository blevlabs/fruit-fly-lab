"""Leg mechanics from FlyMimic paths, XNH fibers and declared estimates; no policy.

Call once, after add_joints(..., AxisOrder.YAW_PITCH_ROLL, neutral_pose=...),
before attaching the NeuroMechFly to a world. Returned names are world-qualified;
local names are also supplied. Excitation is ctrl in [0, 1]; MuJoCo owns activation.
See docs/research/whole-body-muscle-mechanics.md for registration and missing anatomy.
"""
from collections import Counter
import hashlib
import xml.etree.ElementTree as ET

import mujoco as mj
import numpy as np
from flygym import assets_dir
from flygym.anatomy import AxisOrder, BodySegment
from flygym.compose.fly.base_fly import ActuatorType


SOURCE_XML = assets_dir / "model/musculoskeletal/best_combined_arm_damping_stiff_cvt3.xml"
SOURCE_SHA256 = "04f6070d6733940357be005ca72c02ba0d9455538ff018da70c74de7458e9531"
HOMOLOGY_SOURCE = "https://cdn.elifesciences.org/articles/96084/elife-96084-supp6-v2.csv"
XNH_SOURCE = "https://radagast.hms.harvard.edu/catmaidvnc/61"
ANATOMY_APPENDIX = "https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf"
# Kuan/Phelps public XNH project 61. These are geometry skeletons, NOT CNS IDs.
# One median-length traced fiber per anatomical region, selected before simulation.
ACCESSORY_FIBERS = (
    ("anterior", 606022, "0e610f93abc423a8aaae77237b9898b89a0d70096a936f2305470db6ab8b93d7",
     (12587011, 12587018), ((181162, 326925, 296850), (154571, 225922, 234675))),
    ("posterior", 602225, "551630e5284a628cb1fb5e23abc0578529381d64428f89f03337ec7e3b78f837",
     (12571841, 12571844), ((97348, 244425, 312112), (120336, 198675, 252562))),
)
# XNH mm -> donor FlyMimic mesh-local mm. Femur: rigid cuticle registration
# (3.53 um RMS); tibia: shared joint pivot/hinge plus measured bone principal axis.
# The fiber's distal end is treated as rigid to the tibial apodeme: an estimate,
# not a recovered cuticular insertion or an identified motor-unit attachment.
XNH_TO_DONOR = (
    (np.array([[-0.769289352279, 0.484940543406, -0.415964616081],
               [-0.638750455877, -0.597882468906, 0.484287526674],
               [-0.013847295290, 0.638254825862, 0.769700610417]]),
     np.array([0.073683280873, 0.200511879721, -0.788355761918])),
    (np.array([[0.438318077989, -0.793204622128, -0.422733592163],
               [-0.431717018504, -0.598308911706, 0.675016193959],
               [-0.788351240528, -0.113370514717, -0.604689546751]]),
     np.array([0.134085358237, 0.041981415560, 0.220094492278])),
)
XNH_TO_TROCHANTER = (
    np.array([[-0.878213416208, 0.390256543453, -0.276479702482],
              [-0.477451379991, -0.681590160361, 0.554504312918],
              [0.027953091738, 0.618978742439, 0.784910148406]]),
    np.array([0.050960839988, 0.257244532938, -0.852983778220]))
LTM2_FIBERS = (
    ("proximal", 609813, "9bdccc8dc4c1629ed45077803fa0200a5faa98a099543e8affeaf19ca955c854",
     (133004, 542250, 540384), 0.1481108659302442),
    ("distal", 609856, "3602b5773faf40eee738392dda417a703515bd42cda4aba9a0a570e631ac5c48",
     (134162, 496099, 531375), 0.20235775414460794),
)
# Trochanter fibers were traced from femur insertion toward trochanter origin;
# their root/leaf ordering is the reverse of the femoral fibers above.
FEMUR_REDUCTOR_FIBERS = (
    ("1", 603409, "a6c2181e76e52daebef663ba3120a3608507ed43809f219bf2101396670795db",
     (218512, 612525, 549900), (178162, 575025, 562875)),
    ("2", 603329, "08bbc8a402b99499cf1231c7971e0547fd49b9d54601184384b2539f77cbc770",
     (174188, 638325, 572232), (166012, 587700, 563925)),
)
# Skeleton 601725 is the common long apodeme, not a neuron. The last point is
# at the truncated tibial end of the XNH volume, not at the claw.
LONG_TENDON_POINTS = (
    ("LFFemur", 12569708, (136050, 342450, 357188)),
    ("LFFemur", 12569732, (133350, 183450, 193012)),
    ("LFTibia", 12569748, (156524, 150600, 170925)),
    ("LFTibia", 12569764, (264974, 150150, 251625)),
    ("LFTibia", 12569773, (438073, 181476, 375825)),
)
# source actuator, semantic slug, candidate muscle group, serial transfer supported
# Candidate labels are NOT a neuron-to-muscle crosswalk. a/b remain source bundles.
MUSCLES = (
    ("LFC_tergopleural_promotor_a", "tergopleural_promotor_a", "Tergopleural promotor", False),
    ("LFC_tergopleural_promotor_b", "tergopleural_promotor_b", "Tergopleural promotor", False),
    ("LFC_pleural_remotor_and_abductor", "pleural_remotor_abductor", "Pleural remotor/abductor", True),
    ("LFC_pleural_promotor", "pleural_promotor", "Pleural promotor", False),
    ("LFC_sternal_anterior_rotator", "sternal_anterior_rotator", "Sternal anterior rotator", True),
    ("LFC_sternal_posterior_rotator", "sternal_posterior_rotator", "Sternal posterior rotator", True),
    ("LFC_sternal_adductor", "sternal_adductor", "Sternal adductor", True),
    ("LFF_trochanter_flexor_b", "trochanter_flexor_b", "Tr flexor", True),
    # The source combines sterno/tergo terminology: do not choose one MN target.
    ("LFF_sterno-tergo-trochanter_extensor_a", "sterno_tergo_trochanter_extensor_a", None, False),
    ("LFF_sterno-tergo-trochanter_extensor_b", "sterno_tergo_trochanter_extensor_b", None, False),
    ("LFF_accesory_trochanter_flexor", "accessory_trochanter_flexor", "Acc. tr flexor", True),
    ("LFF_trochanter_extensor", "trochanter_extensor", "Tr extensor", True),
    ("LFF_trochanter_flexor_a", "trochanter_flexor_a", "Tr flexor", True),
    ("LFTibia_flex_93434", "tibia_flexor", "Ti flexor", True),
    ("LFTibia_extensor_93932", "tibia_extensor", "Ti extensor", True),
)


def _source_geometry():
    """Compile source kinematics in memory; no asset downloads or source dynamics."""
    raw = SOURCE_XML.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("FlyMimic asset changed; review registration before importing")
    root = ET.fromstring(raw)
    paths = {t.get("name"): [s.get("site") for s in t] for t in root.find("tendon")}
    paths = {a.get("name"): paths[a.get("tendon")] for a in root.find("actuator")}
    # Retain the authored body/site frames and inertials, not meshes, policy or fits.
    for parent in root.iter():
        for child in list(parent):
            if child.tag in {"asset", "geom", "actuator", "tendon", "equality", "keyframe"}:
                parent.remove(child)
    model = mj.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))
    data = mj.MjData(model)
    mj.mj_kinematics(model, data)
    return model, data, paths


def _segment_frame(proximal, distal, hinge_axis):
    """Right-handed frame from a bone axis and projected, declared pitch axis."""
    length = np.linalg.norm(distal - proximal)
    if not np.isfinite(length) or length <= 1e-8:
        raise ValueError("Degenerate segment landmarks")
    longitudinal = (distal - proximal) / length
    transverse = hinge_axis - np.dot(hinge_axis, longitudinal) * longitudinal
    if np.linalg.norm(transverse) <= 1e-8:
        raise ValueError("Hinge axis parallel to segment; registration is undefined")
    transverse /= np.linalg.norm(transverse)
    return np.column_stack((np.cross(transverse, longitudinal), transverse, longitudinal)), length


def _bone_surface_point(model, data, bone, distal, fraction, radial_world):
    """Estimated inner-cuticle point from an actual mesh cross-section, in mm."""
    body, geom = data.body(bone), data.geom(bone)
    rotation = body.xmat.reshape(3, 3)
    shaft = rotation.T @ (data.body(distal).xpos - body.xpos)
    length = np.linalg.norm(shaft)
    if length <= 1e-8:
        raise ValueError(f"Missing shaft geometry for {bone}")
    axis = shaft / length
    radial = rotation.T @ radial_world
    radial -= np.dot(radial, axis) * axis
    if np.linalg.norm(radial) <= 1e-8:
        raise ValueError(f"Undefined anatomical side for {bone}")
    radial /= np.linalg.norm(radial)
    mesh_id = model.geom(bone).dataid[0]
    if model.geom(bone).type[0] != mj.mjtGeom.mjGEOM_MESH or mesh_id < 0:
        raise ValueError(f"A cuticle mesh is required for {bone}")
    start, count = model.mesh_vertadr[mesh_id], model.mesh_vertnum[mesh_id]
    vertices = model.mesh_vert[start:start + count]
    vertices = (vertices @ geom.xmat.reshape(3, 3).T + geom.xpos - body.xpos) @ rotation
    section = vertices[np.abs(vertices @ axis - fraction * length) < 0.05 * length]
    if len(section) < 3:
        raise ValueError(f"Insufficient mesh cross-section for {bone}")
    radius = float(np.max((section - fraction * shaft) @ radial))
    if not np.isfinite(radius) or radius <= 1e-8:
        raise ValueError(f"No cuticle on the specified anatomical side of {bone}")
    # ponytail: 80% of outer-cuticle radius approximates an inner attachment;
    # replace these estimates with segmented attachment/apodeme surfaces.
    return fraction * shaft + 0.8 * radius * radial


def _extra_record(fly, neutral, limb, slug, target, sites, capacity, force, times, **provenance):
    name = f"leg_muscle_{limb}_{slug}"
    points = []
    for i, site in enumerate(sites):
        site["local_name"] = f"{name}_site{i}"
        body = neutral.body(site["body"])
        points.append(body.xpos + body.xmat.reshape(3, 3) @ site["pos_mm"])
    length = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())
    if not np.isfinite(length) or length <= 1e-8:
        raise ValueError(f"Invalid estimated path for {name}")
    return dict(limb=limb, side="left" if limb[0] == "l" else "right",
        neuromere={"f": "T1", "m": "T2", "h": "T3"}[limb[1]],
        muscle_name=slug, target_muscle=target, muscle_group=target,
        group_capacity_fraction=capacity, subdivision_mapping_required=True,
        motor_neuron_ids=[], mapping_status="unmapped", source_actuator=None,
        local_actuator_name=name, actuator_name=f"{fly.name}/{name}",
        local_tendon_name=f"{name}_tendon", tendon_name=f"{fly.name}/{name}_tendon",
        sites=sites, reference_length_mm=length, optimal_fiber_length_mm=length,
        tendon_length_mm=0.0, force_uN=force * capacity, activation_time_s=times.tolist(),
        parameter_status="estimated_not_motion_fitted", **provenance)


def _mesh_in_body(model, data, name):
    body, geom = data.body(name), data.geom(name)
    mid = model.geom(name).dataid[0]
    v0, nv = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
    f0, nf = model.mesh_faceadr[mid], model.mesh_facenum[mid]
    vertices = model.mesh_vert[v0:v0 + nv]
    vertices = (vertices @ geom.xmat.reshape(3, 3).T + geom.xpos - body.xpos) @ body.xmat.reshape(3, 3)
    return vertices, model.mesh_face[f0:f0 + nf].copy()


def _add_articulations(fly, model, data, dorsal_by_limb):
    """Partition existing cuticle; add estimated passive interfaces, never a servo.

    Reparse MJCF because native same-spec reparenting cannot move an existing
    subtree safely. Refresh every FlyGym element reference by its unchanged name.
    """
    # Serialization compiles the spec and can invalidate its element references.
    serialized = fly.mjcf_root.copy()
    serialized.compiler.fusestatic = False  # Keep head/root and other named frames.
    root = ET.fromstring(serialized.to_xml())
    asset = root.find("asset")
    parents = {child: parent for parent in root.iter() for child in parent}
    bodies = {b.get("name"): b for b in root.iter("body")}
    structures, extra_geoms, replacement_meshes = {}, {}, {}
    vector = lambda a: " ".join(format(float(x), ".12g") for x in np.asarray(a).ravel())

    def split_mesh(name, axis, cutoff):
        vertices, faces = _mesh_in_body(model, data, name)
        proximal = vertices[faces].mean(axis=1) @ axis < cutoff
        names = []
        for suffix, selection in (("proximal", proximal), ("distal", ~proximal)):
            kept = faces[selection]
            indices, mapped = np.unique(kept.ravel(), return_inverse=True)
            if len(indices) < 4 or len(kept) < 4:
                raise ValueError(f"Insufficient cuticle for {name} {suffix} partition")
            mesh_name = f"leg_muscle_{name}_{suffix}_mesh"
            ET.SubElement(asset, "mesh", name=mesh_name, vertex=vector(vertices[indices]),
                face=" ".join(str(int(x)) for x in mapped), inertia="convex")
            names.append(mesh_name)
        return names

    for limb, dorsal_world in dorsal_by_limb.items():
        prefix = f"leg_muscle_{limb}"
        femur_name, tarsus_name = f"{limb}_trochanterfemur", f"{limb}_tarsus5"
        femur = bodies[femur_name]
        shaft = data.body(femur_name).xmat.reshape(3, 3).T @ (data.body(f"{limb}_tibia").xpos - data.body(femur_name).xpos)
        # The donor trochanter occupies about 15% of the combined proximal leg
        # segment length. The cut plane and mass partition remain estimates.
        offset = 0.15 * shaft
        prox_mesh, distal_mesh = split_mesh(femur_name, shaft / np.linalg.norm(shaft), np.linalg.norm(offset))
        trochanter = ET.Element("body", name=f"{prefix}_trochanter", pos=femur.get("pos", "0 0 0"), quat=femur.get("quat", "1 0 0 0"))
        parent = parents[femur]
        position = list(parent).index(femur)
        parent.remove(femur); parent.insert(position, trochanter); trochanter.append(femur)
        femur.set("pos", vector(offset)); femur.set("quat", "1 0 0 0")
        for joint in list(femur.findall("joint")):
            femur.remove(joint); trochanter.append(joint)
        # Existing child frames and markers keep exactly their reference positions.
        for element in femur:
            if element.tag in {"body", "site", "camera", "light"}:
                element.set("pos", vector(np.fromstring(element.get("pos", "0 0 0"), sep=" ") - offset))
        geom = femur.find("geom")
        mass = float(model.body(femur_name).mass[0])
        prox_mass = max(0.15 * mass, float(fly.mjcf_root.compiler.boundmass))
        prox_geom = ET.SubElement(trochanter, "geom", **dict(geom.attrib))
        prox_geom.set("name", f"{prefix}_trochanter_geom"); prox_geom.set("mesh", prox_mesh)
        prox_geom.set("pos", "0 0 0"); prox_geom.set("quat", "1 0 0 0"); prox_geom.set("mass", str(prox_mass))
        geom.set("mesh", distal_mesh); geom.set("pos", vector(-offset)); geom.set("quat", "1 0 0 0"); geom.set("mass", str(mass - prox_mass))
        joint_names = []
        # Match the supplied rig's existing numerical/rotor inertia convention;
        # zero armature on these tiny new segments makes the 100 us solve stiff.
        femur_armature = model.dof_armature[model.joint(f"{limb}_coxa-{femur_name}-pitch").dofadr[0]]
        for suffix, axis in zip("xyz", np.eye(3)):
            name = f"{prefix}_femur_compliance_{suffix}"
            ET.SubElement(femur, "joint", name=name, type="hinge", axis=vector(axis),
                limited="true", range="-0.02 0.02", stiffness="0.02", damping="0.002",
                armature=str(float(femur_armature)), springref="0", solreflimit="0.002 1", solimplimit="0.9999 0.9999 0.001 0.5 2")
            joint_names.append(name)
        extra_geoms[femur_name] = [prox_geom.get("name")]
        replacement_meshes[femur_name] = distal_mesh

        tarsus = bodies[tarsus_name]
        rotation = data.body(tarsus_name).xmat.reshape(3, 3)
        axis = rotation.T @ (data.body(tarsus_name).xpos - data.body(f"{limb}_tarsus4").xpos)
        axis /= np.linalg.norm(axis)
        dorsal = rotation.T @ dorsal_world
        dorsal -= np.dot(dorsal, axis) * axis; dorsal /= np.linalg.norm(dorsal)
        vertices, _ = _mesh_in_body(model, data, tarsus_name)
        length = float(np.max(vertices @ axis))
        pivot = 0.75 * length * axis
        prox_mesh, distal_mesh = split_mesh(tarsus_name, axis, 0.75 * length)
        geom = tarsus.find("geom")
        mass = float(model.body(tarsus_name).mass[0])
        pretarsus = ET.SubElement(tarsus, "body", name=f"{prefix}_pretarsus", pos=vector(pivot))
        claw_name = f"{prefix}_pretarsal_flexion"
        claw_armature = model.dof_armature[model.joint(f"{limb}_tarsus4-{tarsus_name}-pitch").dofadr[0]]
        ET.SubElement(pretarsus, "joint", name=claw_name, type="hinge", axis=vector(np.cross(dorsal, axis)),
            limited="true", range="-0.05 1.4", stiffness="0.002", damping="0.0002",
            armature=str(float(claw_armature)), springref="0", solreflimit="0.002 1", solimplimit="0.9999 0.9999 0.001 0.5 2")
        claw_geom = ET.SubElement(pretarsus, "geom", **dict(geom.attrib))
        claw_geom.set("name", f"{prefix}_pretarsal_geom"); claw_geom.set("mesh", distal_mesh)
        claw_geom.set("pos", vector(-pivot)); claw_geom.set("quat", "1 0 0 0"); claw_geom.set("mass", str(0.25 * mass))
        geom.set("mesh", prox_mesh); geom.set("pos", "0 0 0"); geom.set("quat", "1 0 0 0"); geom.set("mass", str(0.75 * mass))
        extra_geoms[tarsus_name] = [claw_geom.get("name")]
        replacement_meshes[tarsus_name] = prox_mesh
        structures[limb] = dict(trochanter_body=trochanter.get("name"), femur_offset_mm=offset.tolist(),
            pretarsal_body=pretarsus.get("name"), pretarsal_pivot_mm=pivot.tolist(),
            plate_local_mm=(0.02 * length * axis - 0.12 * length * dorsal).tolist(),
            joint_names=[*joint_names, claw_name], terminal_length_mm=length,
            femur_armature_g_mm2=float(femur_armature), pretarsal_armature_g_mm2=float(claw_armature),
            joint_status="estimated_compliant_interface_and_collective_pretarsal_hinge")

    for key in root.findall("./keyframe/key"):
        for attribute in ("qpos", "qvel"):
            key.attrib.pop(attribute, None)
    new_spec = mj.MjSpec.from_string(ET.tostring(root, encoding="unicode"))
    new_spec.compiler.fusestatic = fly.mjcf_root.compiler.fusestatic
    new_spec.copy().compile()  # Validate before adopting; compilation mutates specs.
    mappings = {"bodyseg_to_mjcfbody": "body", "bodyseg_to_mjcfmesh": "mesh",
        "bodyseg_to_mjcfgeom": "geom", "jointdof_to_mjcfjoint": "joint",
        "anatomicaljoint_to_mjcfsites": "site", "sensorname_to_mjcfsensor": "sensor",
        "cameraname_to_mjcfcamera": "camera", "eyecameraname_to_mjcfcamera": "camera",
        "leg_to_adhesionactuator": "actuator"}
    refreshed = {}
    for attribute, kind in mappings.items():
        find = getattr(new_spec, kind)
        refreshed[attribute] = {key: [find(v.name) for v in value] if isinstance(value, list) else find(value.name)
            for key, value in getattr(fly, attribute).items()}
    actuators = {kind: {key: new_spec.actuator(value.name) for key, value in values.items()}
        for kind, values in fly.jointdof_to_mjcfactuator_by_type.items()}
    fly._mjcf_root = new_spec
    for attribute, mapping in refreshed.items():
        setattr(fly, attribute, mapping)
    fly.jointdof_to_mjcfactuator_by_type = actuators
    fly._neutral_keyframe = new_spec.key("neutral")
    for name, extra in extra_geoms.items():
        fly.bodyseg_to_mjcfmesh[name] = new_spec.mesh(replacement_meshes[name])
    fly._rebuild_neutral_keyframe()
    return structures


def _thoracic_origin(model, data, limb, dorsal, lateral_fraction=0.5):
    """Estimated attachment patch on sternum/tergum beside the named coxa."""
    vertices, _ = _mesh_in_body(model, data, "c_thorax")
    body = data.body("c_thorax")
    coxa = body.xmat.reshape(3, 3).T @ (data.body(f"{limb}_coxa").xpos - body.xpos)
    center_y = lateral_fraction * abs(coxa[1])
    patch = vertices[(abs(vertices[:, 0] - coxa[0]) < 0.08 * np.ptp(vertices[:, 0]))
                     & (abs(vertices[:, 1] - center_y) < 0.12 * np.ptp(vertices[:, 1]))]
    if len(patch) < 3:
        raise ValueError(f"No thoracic cuticle patch for {limb}")
    ranked = patch[np.argsort(patch[:, 2])]
    count = max(3, len(patch) // 5)
    point = (ranked[-count:] if dorsal else ranked[:count]).mean(axis=0)
    if limb[0] == "r":
        point[1] *= -1
    return point.tolist()


def add_leg_muscles(fly, *, group_force_uN=28.0, activation_time_s=(0.01, 0.04)):
    """Add leg MTUs, compliant trochanter/femur interfaces and pretarsal bodies.

    All force/length/kinetic parameters and all inter-rig registrations are estimates.
    group_force_uN is capacity PER muscle group, split across source a/b bundles.
    Original joint properties are preserved. New passive interfaces are explicit
    mechanical estimates. No control signals, CNS IDs or current state are assigned.
    """
    if fly.skeleton is None or fly.skeleton.axis_order != AxisOrder.YAW_PITCH_ROLL:
        raise ValueError("Add YAW_PITCH_ROLL leg joints before adding leg muscles")
    times = np.asarray(activation_time_s, dtype=float)
    if (not np.isfinite(group_force_uN) or group_force_uN <= 0
            or times.shape != (2,) or not np.isfinite(times).all() or np.any(times < 0.001)):
        raise ValueError("Force must be positive; two activation times must be >= 1 ms")
    spec = fly.mjcf_root
    if any(e.name.startswith("leg_muscle_") for e in (*spec.actuators, *spec.tendons, *spec.sites)):
        raise ValueError("Leg muscles already present; refusing duplicate actuators")
    leg_joints = {j.name for d, j in fly.jointdof_to_mjcfjoint.items() if d.child.is_leg()}
    if any(f"{limb}_tibia-{limb}_tarsus1-pitch" not in leg_joints for limb in ("lf", "lm", "lh", "rf", "rm", "rh")):
        raise ValueError("Tibia-tarsus pitch joints are required for distal muscles")
    if any(a.target in leg_joints for a in spec.actuators):
        raise ValueError("Remove joint-transmission leg actuators before adding muscles")

    source_model, source_data, paths = _source_geometry()
    target_spec = spec.copy()
    target_spec.compiler.fusestatic = False
    target_model = target_spec.compile()
    target_data = mj.MjData(target_model)
    mj.mj_kinematics(target_model, target_data)  # qpos0, NOT neutral joint rotations
    neutral_data = mj.MjData(target_model)
    neutral_data.qpos[:] = fly._get_neutral_qpos(target_model)
    mj.mj_kinematics(target_model, neutral_data)

    # A source femur point first enters the trochanter frame through its actual
    # fixed body transform. The destination has a merged trochanter/femur body.
    source_segments = (
        ("LFCoxa", "LFTrochanter", "joint_LFCoxa_pitch", "coxa"),
        ("LFTrochanter", "LFTibia", "joint_LFTrochanter_pitch", "trochanterfemur"),
        ("LFTibia", "LFTarsus1", "joint_LFTibia_pitch", "tibia"),
    )
    owner_segments = {"Thorax": 0, "LFCoxa": 0, "LFTrochanter": 1, "LFFemur": 1, "LFTibia": 2}
    records, transforms_by_limb, dorsal_by_limb = [], {}, {}
    for limb in ("lf", "lm", "lh", "rf", "rm", "rh"):
        # Replace ambiguous combined sterno/tergo prototypes with anatomical heads.
        selected = [m for m in MUSCLES if m[2] is not None and (limb[1] == "f" or m[3])]
        counts = Counter(m[2] or "sterno_tergo_trochanter_extensor" for m in selected)
        transforms = []
        for s_prox, s_dist, s_joint, segment in source_segments:
            t_prox = f"{limb}_{segment}"
            t_dist = f"{limb}_" + {"coxa": "trochanterfemur", "trochanterfemur": "tibia", "tibia": "tarsus1"}[segment]
            parent = "c_thorax" if segment == "coxa" else f"{limb}_" + {"trochanterfemur": "coxa", "tibia": "trochanterfemur"}[segment]
            t_joint = f"{parent}-{t_prox}-pitch"
            s_origin, t_origin = source_data.body(s_prox).xpos, target_data.body(t_prox).xpos
            s_frame, s_length = _segment_frame(s_origin, source_data.body(s_dist).xpos,
                source_data.xaxis[source_model.joint(s_joint).id])
            t_frame, t_length = _segment_frame(t_origin, target_data.body(t_dist).xpos,
                target_data.xaxis[target_model.joint(t_joint).id])
            reflection = np.diag([1, -1 if limb[0] == "r" else 1, 1])
            transform = (t_length / s_length) * t_frame @ reflection @ s_frame.T
            transforms.append((s_origin, t_origin, transform))
        transforms_by_limb[limb] = transforms

        for source_name, slug, target, serial in selected:
            name = f"leg_muscle_{limb}_{slug}"
            group = target or "sterno_tergo_trochanter_extensor"
            sites, neutral_points = [], []
            for index, source_site in enumerate(paths[source_name]):
                sid = source_model.site(source_site).id
                source_body = source_model.body(source_model.site_bodyid[sid]).name
                segment_index = owner_segments[source_body]
                owner = "c_thorax" if source_body == "Thorax" else f"{limb}_{source_segments[segment_index][3]}"
                s_origin, t_origin, transform = transforms[segment_index]
                world_pos = t_origin + transform @ (source_data.site_xpos[sid] - s_origin)
                body = target_data.body(owner)
                local_pos = body.xmat.reshape(3, 3).T @ (world_pos - body.xpos)
                neutral_body = neutral_data.body(owner)
                neutral_points.append(neutral_body.xpos + neutral_body.xmat.reshape(3, 3) @ local_pos)
                sites.append(dict(local_name=f"{name}_site{index}", body=owner,
                    pos_mm=local_pos.tolist(), source_site=source_site, source_body=source_body,
                    source_pos_mm=source_model.site_pos[sid].tolist()))
            reference_length = float(np.linalg.norm(np.diff(neutral_points, axis=0), axis=1).sum())
            if not np.isfinite(reference_length) or reference_length <= 1e-8:
                raise ValueError(f"Invalid registered length for {name}")
            records.append(dict(limb=limb, side="left" if limb[0] == "l" else "right",
                neuromere={"f": "T1", "m": "T2", "h": "T3"}[limb[1]],
                muscle_name=slug, target_muscle=target, source_actuator=source_name,
                muscle_group=group, group_capacity_fraction=1 / counts[group],
                subdivision_mapping_required=counts[group] > 1,
                motor_neuron_ids=[], mapping_status="unmapped",
                local_actuator_name=name, actuator_name=f"{fly.name}/{name}",
                local_tendon_name=f"{name}_tendon", tendon_name=f"{fly.name}/{name}_tendon",
                sites=sites, source_sha256=SOURCE_SHA256,
                source_geometry_status="published_converted_optimized_asset_not_raw_anatomy",
                geometry_status=("estimated_inter_rig_registration" if limb == "lf" else
                    "estimated_bilateral_mirror" if limb == "rf" else "estimated_serial_homology_transfer"),
                homology_source=HOMOLOGY_SOURCE if serial else None,
                reference_length_mm=reference_length, optimal_fiber_length_mm=reference_length,
                tendon_length_mm=0.0, force_uN=group_force_uN / counts[group],
                activation_time_s=times.tolist(), parameter_status="estimated_not_motion_fitted"))

        # Accessory flexor origins/endpoints come from traced XNH fibers, not the
        # main flexor tendon. Two independent paths preserve the two compartments.
        for region, sid, digest, node_ids, endpoints in ACCESSORY_FIBERS:
            sites = []
            for index, (source_body, segment_index, owner) in enumerate((
                    ("LFFemur", 1, f"{limb}_trochanterfemur"), ("LFTibia", 2, f"{limb}_tibia"))):
                rotation, translation = XNH_TO_DONOR[index]
                source_pos = rotation @ (np.asarray(endpoints[index]) / 1e6) + translation
                source_body_data = source_data.body(source_body)
                source_world = source_body_data.xpos + source_body_data.xmat.reshape(3, 3) @ source_pos
                s_origin, t_origin, transform = transforms[segment_index]
                target_world = t_origin + transform @ (source_world - s_origin)
                body = target_data.body(owner)
                local = body.xmat.reshape(3, 3).T @ (target_world - body.xpos)
                sites.append(dict(body=owner, pos_mm=local.tolist(), source_body=source_body,
                    source_pos_mm=source_pos.tolist(), source_node_id=node_ids[index],
                    source_xnh_pos_nm=list(endpoints[index]),
                    attachment_status="traced_fiber_origin" if index == 0 else "estimated_rigid_tibia_apodeme_endpoint"))
            records.append(_extra_record(fly, neutral_data, limb, f"accessory_tibia_flexor_{region}",
                "Acc. ti flexor", sites, 0.5, group_force_uN, times,
                source_skeleton_id=sid, source_sha256=digest,
                source_urls=[f"{XNH_SOURCE}/skeletons/{sid}/compact-detail", ANATOMY_APPENDIX],
                source_geometry_status="traced_XNH_fiber_with_estimated_registration_and_rigid_apodeme",
                geometry_status="estimated_XNH_transfer" if limb[1] == "f" else "estimated_serial_XNH_transfer",
                homology_source=HOMOLOGY_SOURCE, anatomical_region=region,
                missing_geometry=["fiber-specific MN assignment", "distal thin-tendon insertion/compliance"]))

        # Soler/Azevedo locate the levator dorsally and depressor ventrally in the
        # tibia. Determine dorsal from actual donor tibial insertion coordinates,
        # then use the destination cuticle; no search over motion or joint signs.
        pair = {r["target_muscle"]: r for r in records if r["limb"] == limb and r["target_muscle"] in ("Ti extensor", "Ti flexor")}
        dorsal_local = (np.asarray(pair["Ti extensor"]["sites"][-1]["pos_mm"])
                        - np.asarray(pair["Ti flexor"]["sites"][-1]["pos_mm"]))
        dorsal_world = target_data.body(f"{limb}_tibia").xmat.reshape(3, 3) @ dorsal_local
        dorsal_by_limb[limb] = dorsal_world
        for slug, target, side, origin_fraction in (
                ("tarsus_levator", "Ta levator", 1, 0.8),
                ("tarsus_depressor", "Ta depressor", -1, 0.55)):
            sites = []
            for bone, distal, fraction in ((f"{limb}_tibia", f"{limb}_tarsus1", origin_fraction),
                                            (f"{limb}_tarsus1", f"{limb}_tarsus2", 0.05)):
                point = _bone_surface_point(target_model, target_data, bone, distal, fraction, side * dorsal_world)
                sites.append(dict(body=bone, pos_mm=point.tolist(), source_site=None, source_pos_mm=None,
                    attachment_status="estimated_from_cuticle_mesh_and_anatomical_compartment",
                    longitudinal_fraction=fraction, inner_cuticle_fraction=0.8))
            records.append(_extra_record(fly, neutral_data, limb, slug, target, sites, 1.0, group_force_uN, times,
                source_sha256=None, source_geometry_status="primary_topology_with_estimated_cuticle_attachments",
                source_urls=[ANATOMY_APPENDIX, "https://doi.org/10.1242/dev.01527"],
                geometry_status="estimated_bone_surface_geometry", homology_source="https://doi.org/10.1242/dev.01527",
                missing_geometry=["measured tibia-tarsus insertions", "fiber-specific MN assignment"]
                    + (["retro-depressor fiber paths"] if target == "Ta depressor" else [])))

    # Structural edits occur only on this supplied, uncompiled fly, never on a
    # running model. Its original names and initial cuticle coordinates survive.
    structures = _add_articulations(fly, target_model, target_data, dorsal_by_limb)
    spec = fly.mjcf_root  # Structural editing refreshed the native spec/references.
    for record in records:
        limb = record["limb"]
        for site in record["sites"]:
            if site["body"] == f"{limb}_trochanterfemur":
                if site.get("source_body") == "LFTrochanter":
                    site["body"] = structures[limb]["trochanter_body"]
                else:
                    site["pos_mm"] = (np.asarray(site["pos_mm"]) - structures[limb]["femur_offset_mm"]).tolist()
    new_copy = spec.copy(); new_copy.compiler.fusestatic = False
    new_model = new_copy.compile(); new_data = mj.MjData(new_model)
    mj.mj_kinematics(new_model, new_data)
    neutral_data = mj.MjData(new_model); neutral_data.qpos[:] = fly._get_neutral_qpos(new_model)
    mj.mj_kinematics(new_model, neutral_data)

    def donor_site(limb, source_body, source_pos, **provenance):
        segment = owner_segments[source_body]
        source_b = source_data.body(source_body)
        world = source_b.xpos + source_b.xmat.reshape(3, 3) @ source_pos
        s_origin, t_origin, transform = transforms_by_limb[limb][segment]
        world = t_origin + transform @ (world - s_origin)
        owner = structures[limb]["trochanter_body"] if source_body == "LFTrochanter" else f"{limb}_{source_segments[segment][3]}"
        b = new_data.body(owner)
        local = b.xmat.reshape(3, 3).T @ (world - b.xpos)
        return dict(body=owner, pos_mm=local.tolist(), source_body=source_body,
            source_pos_mm=np.asarray(source_pos).tolist(), **provenance)

    def xnh_site(limb, source_body, raw, **provenance):
        rotation, translation = (XNH_TO_TROCHANTER if source_body == "LFTrochanter"
                                 else XNH_TO_DONOR[0 if source_body == "LFFemur" else 1])
        return donor_site(limb, source_body, rotation @ (np.asarray(raw) / 1e6) + translation,
                          source_xnh_pos_nm=list(raw), **provenance)

    for limb, structure in structures.items():
        contact_names = [f"{fly.name}/leg_muscle_{limb}_trochanter_geom",
                         f"{fly.name}/leg_muscle_{limb}_pretarsal_geom"]
        extra = dict(structures=structure, contact_geom_names=contact_names,
            structural_joint_names=[f"{fly.name}/{n}" for n in structure["joint_names"]])
        # Different thoracic origins feed the same extensor apodeme. The old
        # combined source a/b coordinates locate a representative shared route;
        # they are not relabeled as individually identified muscle heads.
        common = []
        for index, source_body in ((-2, "LFCoxa"), (-1, "LFTrochanter")):
            source_sites = [paths[f"LFF_sterno-tergo-trochanter_extensor_{s}"][index] for s in "ab"]
            point = np.mean([source_model.site_pos[source_model.site(n).id] for n in source_sites], axis=0)
            common.append(donor_site(limb, source_body, point, source_sites=source_sites,
                attachment_status="estimated_shared_extensor_apodeme_from_source_paths"))
        for slug, target, dorsal in (("sternotrochanter", "Sternotrochanter", False), ("tergotrochanter", "Tergotr.", True)):
            sites = [dict(body="c_thorax", pos_mm=_thoracic_origin(target_model, target_data, limb, dorsal),
                source_pos_mm=None, attachment_status="estimated_sternal_or_tergal_cuticle_origin"), *[dict(s) for s in common]]
            records.append(_extra_record(fly, neutral_data, limb, slug, target, sites, 1, group_force_uN, times,
                source_sha256=SOURCE_SHA256, source_urls=[ANATOMY_APPENDIX],
                source_geometry_status="primary_separate_heads_shared_tendon_with_estimated_origins",
                geometry_status="estimated_anatomical_head_transfer", homology_source=HOMOLOGY_SOURCE, **extra))
        if limb[1] == "m":
            # TDT/TTM originates at dorsal thoracic cuticle and pulls the middle
            # leg's extensor apodeme. This is not the intrinsic Tr extensor.
            # The exact T2 Tergotr. vs TTM/STTM fiber partition is unresolved:
            # share ONE estimated complex capacity instead of counting it twice.
            terg = records[-1]
            budget = "T2_tergotrochanteral_complex"
            terg.update(muscle_group=budget, group_capacity_fraction=0.5,
                        force_uN=0.5 * group_force_uN,
                        capacity_partition_status="estimated_Tergotr_TTM_half_split_not_fiber_mapping")
            sites = [dict(body="c_thorax", pos_mm=_thoracic_origin(target_model, target_data, limb, True, 1.0),
                source_pos_mm=None, attachment_status="estimated_dorsal_T2_jump_muscle_origin"), *[dict(s) for s in common]]
            record = _extra_record(fly, neutral_data, limb, "tergotrochanteral_jump", "TTM", sites,
                0.5, group_force_uN, times, source_sha256=None,
                source_urls=["https://pmc.ncbi.nlm.nih.gov/articles/PMC2849092/", "https://doi.org/10.1007/BF00603798"],
                source_geometry_status="primary_TDT_topology_with_estimated_dorsal_origin_and_extensor_apodeme",
                geometry_status="estimated_T2_jump_muscle_path", homology_source=None,
                semantic_muscle_key="wing.tergotrochanteral_jump",
                capacity_partition_status="estimated_Tergotr_TTM_half_split_not_fiber_mapping",
                missing_geometry=["TTMn/STTMm fiber-specific attachments", "whole-muscle PCSA"], **extra)
            record["muscle_group"] = budget
            records.append(record)

        for region, sid, digest, origin, insertion in FEMUR_REDUCTOR_FIBERS:
            sites = [xnh_site(limb, "LFTrochanter", origin, attachment_status="traced_trochanter_origin"),
                     xnh_site(limb, "LFFemur", insertion, attachment_status="traced_femoral_insertion")]
            records.append(_extra_record(fly, neutral_data, limb, f"femur_reductor_{region}", "Fe reductor", sites,
                0.5, group_force_uN, times, source_skeleton_id=sid, source_sha256=digest,
                source_urls=[f"{XNH_SOURCE}/skeletons/{sid}/compact-detail", ANATOMY_APPENDIX],
                source_geometry_status="traced_XNH_fiber_with_estimated_interface_compliance",
                geometry_status="estimated_compliant_bone_interface", homology_source=HOMOLOGY_SOURCE,
                missing_geometry=["measured articulation/compliance", "fiber-specific MN innervation"], **extra))

        common_long = [xnh_site(limb, bone, raw, source_node_id=node,
                       attachment_status="estimated_apodeme_guide_from_traced_centerline")
                       for bone, node, raw in LONG_TENDON_POINTS]
        distal = []
        for number in range(1, 6):
            bone = f"{limb}_tarsus{number}"
            end = f"{limb}_tarsus{number + 1}" if number < 5 else structure["pretarsal_body"]
            fraction = 0.5 if number < 5 else 0.7
            outer = _bone_surface_point(new_model, new_data, bone, end, fraction, -dorsal_by_limb[limb])
            b = new_data.body(bone)
            center = fraction * b.xmat.reshape(3, 3).T @ (new_data.body(end).xpos - b.xpos)
            point = center + 0.25 * (outer - center)  # 20% outer radius, estimated internal guide.
            distal.append(dict(body=bone, pos_mm=point.tolist(), source_pos_mm=None,
                attachment_status="estimated_internal_tarsal_apodeme_guide"))
        distal.append(dict(body=structure["pretarsal_body"], pos_mm=structure["plate_local_mm"],
            source_pos_mm=None, attachment_status="estimated_unguitractor_plate_attachment"))
        ltm_extra = dict(source_urls=[ANATOMY_APPENDIX, f"{XNH_SOURCE}/skeletons/601725/compact-detail"],
            source_geometry_status="traced_proximal_apodeme_with_estimated_distal_guides_and_pretarsus",
            geometry_status="estimated_shared_long_apodeme", homology_source=HOMOLOGY_SOURCE,
            shared_apodeme=f"{limb}_retractor_unguis", apodeme_source_sha256="12a568f6036fe013bd3ed72b7cda3595f43bbb87b70b69e503da7532afa6eca3",
            missing_geometry=["measured distal guide/plate geometry", "tendon compliance", "generic ltm compartment identity"], **extra)
        for region, sid, digest, origin, fiber_length in LTM2_FIBERS:
            sites = [xnh_site(limb, "LFFemur", origin, attachment_status="traced_femoral_ltm2_origin"),
                     *[dict(s) for s in common_long], *[dict(s) for s in distal]]
            record = _extra_record(fly, neutral_data, limb, f"ltm2_femur_{region}", "ltm2-femur", sites,
                0.5, group_force_uN, times, source_skeleton_id=sid, source_sha256=digest, **ltm_extra)
            scale = np.linalg.norm(transforms_by_limb[limb][1][2][:, 0])
            record["optimal_fiber_length_mm"] = fiber_length * scale
            record["tendon_length_mm"] = record["reference_length_mm"] - record["optimal_fiber_length_mm"]
            records.append(record)
        # ltm1's exact origins were not present among the public fiber traces.
        # Use the measured long-apodeme side and an explicit mid-tibial attachment.
        b = new_data.body(f"{limb}_tibia")
        radial_world = b.xmat.reshape(3, 3) @ np.asarray(common_long[3]["pos_mm"])
        origin = _bone_surface_point(new_model, new_data, f"{limb}_tibia", f"{limb}_tarsus1", 0.35, radial_world)
        sites = [dict(body=f"{limb}_tibia", pos_mm=origin.tolist(), source_pos_mm=None,
                      attachment_status="estimated_ltm1_cuticle_origin"), dict(common_long[-1]), *[dict(s) for s in distal]]
        record = _extra_record(fly, neutral_data, limb, "ltm1_tibia", "ltm1-tibia", sites,
            1, group_force_uN, times, source_sha256=None, **ltm_extra)
        record["optimal_fiber_length_mm"] = 0.25 * np.linalg.norm(new_data.body(f"{limb}_tarsus1").xpos - b.xpos)
        record["tendon_length_mm"] = record["reference_length_mm"] - record["optimal_fiber_length_mm"]
        records.append(record)

    for record in records:
        record["peripheral_limb"] = record["limb"]
        # A requirement for the caller's physics integrator, not a global option
        # mutation. Neural/NMJ clocks need not equal the mechanical substep.
        record["physics_max_timestep_s"] = 1e-5
        if record["tendon_length_mm"] < 0:
            raise ValueError(f"Negative inferred tendon length: {record['muscle_name']}")
        for site in record["sites"]:
            spec.body(site["body"]).add_site(
                name=site["local_name"], pos=site["pos_mm"], size=(0.004, 0, 0),
                rgba=(0.9, 0.3, 0.15, 0.7))
        tendon = spec.add_tendon(name=record["local_tendon_name"], width=0.003,
            stiffness=0, damping=0, rgba=(0.9, 0.3, 0.15, 0.7))
        for site in record["sites"]:
            tendon.wrap_site(site["local_name"])
        # ponytail: whole-path L0 and zero rigid-tendon length; replace with measured
        # fiber/tendon lengths when available. This is not an anatomical ROM estimate.
        # range=[0,1], lengthrange=[0,L0] makes inferred LT exactly zero, including
        # floating-point subtraction. These are calibration pairs, not joint targets.
        prm = [0, 1, record["force_uN"], 200, 0.5, 1.6, 1.5, 1.3, 1.2, 0]
        name = record["local_actuator_name"]
        actuator = spec.add_actuator(name=name, trntype=mj.mjtTrn.mjTRN_TENDON,
            target=record["local_tendon_name"], gear=(1, 0, 0, 0, 0, 0),
            lengthrange=(record["tendon_length_mm"], record["tendon_length_mm"] + record["optimal_fiber_length_mm"]),
            ctrllimited=True, ctrlrange=(0, 1), actlimited=True, actrange=(0, 1),
            dyntype=mj.mjtDyn.mjDYN_MUSCLE, dynprm=[*times, 0, 0, 0, 0, 0, 0, 0, 0],
            gaintype=mj.mjtGain.mjGAIN_MUSCLE, gainprm=prm,
            biastype=mj.mjtBias.mjBIAS_MUSCLE, biasprm=prm)
        # FlyGym's muscle accessor accepts named entries (as its FlyMimic class does).
        fly.jointdof_to_mjcfactuator_by_type[ActuatorType.MUSCLE][name] = actuator
        fly.jointdof_to_neutralaction_by_type[ActuatorType.MUSCLE][name] = 0.0
    fly._rebuild_neutral_keyframe()
    return records
