"""Source-informed adult neck mechanics on NeuroMechFly; no motor policy.

add_head_muscles(fly) returns the same semantic/side/actuator metadata contract
as add_proboscis_muscles. Call before world attachment, in either order.
Gorko 2024 Extended Data Fig. 7 supplies attachment topology, not these metrics.
"""
import mujoco as mj
import numpy as np
from flygym.anatomy import BodySegment
from flygym.compose import NeuroMechFly

from proboscis_muscles import _add_mtu


ANATOMY_SOURCE = "https://www.nature.com/articles/s41586-024-07222-5/figures/11"
MUSCLE_TARGETS = ("VL1", "VL2", "TH1", "TH2", "AD", "LEV")
HEAD_JOINTS = ("neck_head_yaw", "neck_head_roll", "neck_head_pitch")
SUPPORT_JOINTS = ("neck_support_yaw", "neck_support_roll")
ANTENNA_SOURCE = "https://pmc.ncbi.nlm.nih.gov/articles/PMC9992063/#F2"
RETINA_SOURCE = "https://pmc.ncbi.nlm.nih.gov/articles/PMC10103069/#F1"


def _add_sensory_head_muscles(fly, times, force_uN):
    """Suver's four scape muscles and Fenk's MOT/MOS, no guessed MN assignments."""
    spec = fly.mjcf_root
    head = fly.bodyseg_to_mjcfbody[BodySegment("c_head")]
    snapshot = spec.copy()
    snapshot.compiler.fusestatic = False
    model = snapshot.compile()
    records = []
    for side, sign, prefix in (("left", 1, "l"), ("right", -1, "r")):
        pedicel = fly.bodyseg_to_mjcfbody[BodySegment(f"{prefix}_pedicel")]
        funiculus = fly.bodyseg_to_mjcfbody[BodySegment(f"{prefix}_funiculus")]
        rotation = np.empty(9)
        mj.mju_quat2Mat(rotation, pedicel.quat / np.linalg.norm(pedicel.quat))
        rotation = rotation.reshape(3, 3)
        active_joints = {}
        for label, axis in (("pitch", (0, 1, 0)), ("yaw", (0, 0, sign))):
            name = f"antenna_{side}_{label}"
            pedicel.add_joint(name=name, type=mj.mjtJoint.mjJNT_HINGE, axis=axis,
                limited=True, range=(-0.4, 0.4), stiffness=0.01, damping=0.0001)
            active_joints[label] = f"{fly.name}/{name}"
        # The funicular hook is a passive pivot, not a fifth antennal muscle.
        axis = np.asarray(funiculus.pos) / np.linalg.norm(funiculus.pos)
        funiculus.add_joint(name=f"antenna_{side}_funicular", type=mj.mjtJoint.mjJNT_HINGE,
            axis=axis, limited=True, range=(-0.3, 0.3), stiffness=0.004, damping=0.00003)
        # Ordered anterior-to-posterior as Suver Fig. 2. These are metric estimates
        # in the pedicel reference frame; scape origins stay fixed to the head.
        antennal_paths = (
            ("m1", (0.025, -0.016, 0.035), (0.005, -0.009, -0.007)),
            ("m2", (0.010, 0.022, 0.012), (-0.004, 0.008, -0.004)),
            ("m3", (-0.005, 0.025, -0.025), (0.006, 0.009, 0.005)),
            ("m4", (-0.020, -0.018, 0.030), (0.006, -0.008, -0.007)),
        )
        paths = []
        for target, origin, insertion in antennal_paths:
            origin, insertion = np.array(origin) * [1, sign, 1], np.array(insertion) * [1, sign, 1]
            paths.append(("antenna", target, np.asarray(pedicel.pos) + rotation @ origin,
                pedicel, insertion, np.linalg.norm(insertion - origin), active_joints, ANTENNA_SOURCE))

        eye = fly.bodyseg_to_mjcfbody[BodySegment(f"{prefix}_eye")]
        donor = spec.geom(f"{prefix}_eye")
        mass = max(1e-6, spec.compiler.boundmass)
        if donor.mass <= mass:
            raise ValueError("Insufficient eye mass for an internal retina")
        center = np.asarray(eye.pos) + model.geom_pos[model.geom(f"{prefix}_eye").id]
        retina = head.add_body(name=f"retina_{side}_orbital_ridge", pos=center)
        retina.add_geom(name=f"retina_{side}_internal", type=mj.mjtGeom.mjGEOM_ELLIPSOID,
            size=(0.08, 0.02, 0.10), mass=mass, group=3, contype=0, conaffinity=0)
        donor.mass -= mass
        retinal_joints = {}
        # No fixed anatomical rotary pivot is established: use two small compliant
        # translational modes of the orbital ridge, not rotation of the lens mesh.
        for label, axis in (("anterior", (1, 0, 0)), ("dorsal", (0, 0, 1))):
            name = f"retina_{side}_{label}"
            retina.add_joint(name=name, type=mj.mjtJoint.mjJNT_SLIDE, axis=axis,
                limited=True, range=(-0.012, 0.012), stiffness=2000, damping=0.1)
            retinal_joints[label] = f"{fly.name}/{name}"
        for target, origin, insertion in (
            ("MOT", (0.080, 0.080, -0.020), (0.050, -0.035, -0.030)),
            ("MOS", (0.420, 0.085, 0.080), (0.040, -0.035, 0.045)),
        ):
            origin, insertion = np.array(origin) * [1, sign, 1], np.array(insertion) * [1, sign, 1]
            paths.append(("retina", target, origin, retina, insertion,
                np.linalg.norm(center + insertion - origin), retinal_joints, RETINA_SOURCE))

        for limb, target, origin, owner, insertion, length, joint_names, source in paths:
            name = f"{limb}_muscle_{side}_{target}"
            record = dict(limb=limb, side=side, peripheral_target_side=side[0].upper(),
                peripheral_target_sides=[side[0].upper()], peripheral_target_topology="unilateral",
                muscle_target=target, target_muscle=target, semantic_muscle_key=f"{limb}.{target}",
                muscle_group=target, group_capacity_fraction=1.0,
                local_actuator_name=name, actuator_name=f"{fly.name}/{name}",
                local_tendon_name=f"{name}_tendon", tendon_name=f"{fly.name}/{name}_tendon",
                joint_names=joint_names,
                sites=[dict(local_name=f"{name}_origin", body=head.name, pos_mm=origin.tolist()),
                       dict(local_name=f"{name}_insertion", body=owner.name, pos_mm=insertion.tolist())],
                reference_length_mm=float(length), optimal_fiber_length_mm=float(0.9 * length),
                tendon_length_mm=float(0.1 * length), force_uN=float(force_uN),
                activation_time_s=list(times), motor_neuron_ids=[], mapping_status="unmapped",
                anatomy_source=source, geometry_status="primary_attachment_topology_estimated_metric_paths",
                force_provenance="Unmeasured per-side sensory-head capacity estimate; not motion fitted",
                parameter_status="estimated_not_behavior_fitted",
                neuronal_correspondence="No exact MaleCNS neuron-to-muscle match established",
                sensory_encoding_status="Not supplied by this mechanical component")
            _add_mtu(fly, record, (0.5, 1.6, 1.5, 1.3, 1.2))
            records.append(record)
    return records


def add_head_muscles(fly, *, group_force_uN=28.0, activation_time_s=(0.01, 0.04), sensory_force_uN=1.0):
    """Add 12 neck, eight antennal and four retinal MTUs on native bodies/joints.

    Five hinge coordinates plus two independent condylar constraints give three
    effective rotational DOFs. AD/LEV act on the cervical sclerite, not the head
    directly. VL1/VL2/TH1/TH2 attach to the posterior head. All metrics estimated.
    Head/appendage handles and existing joint/passive properties are preserved.
    """
    times = np.asarray(activation_time_s, dtype=float)
    if (not isinstance(fly, NeuroMechFly) or times.shape != (2,)
            or not np.isfinite(times).all() or np.any(times < 0.001)
            or not np.isfinite(group_force_uN) or group_force_uN <= 0
            or not np.isfinite(sensory_force_uN) or sensory_force_uN <= 0):
        raise ValueError("Require NeuroMechFly, positive force and two activation times >= 1 ms")
    spec = fly.mjcf_root
    head = fly.bodyseg_to_mjcfbody[BodySegment("c_head")]
    thorax = fly.bodyseg_to_mjcfbody[BodySegment("c_thorax")]
    if list(head.joints) or any(e.name.startswith("neck_") for e in (*spec.bodies, *spec.actuators, *spec.tendons)):
        raise ValueError("Neck mechanics already present; refusing duplicate joints/actuators")
    if any(list(fly.bodyseg_to_mjcfbody[BodySegment(f"{side}_{segment}")].joints)
           for side in ("l", "r") for segment in ("pedicel", "funiculus")):
        raise ValueError("Antennal joints already present; refusing duplicate mechanics")
    if (head.parent.name != "c_thorax" or not np.allclose(head.pos, (0.0287, 0, 0.000698), atol=1e-9, rtol=0)
            or not np.allclose(head.quat, (1, 0, 0, 0), atol=1e-9, rtol=0)):
        raise ValueError("Head rig changed; cervical attachment estimates need re-registration")
    pivot = np.array(head.pos, copy=True)
    support_mass = max(1e-6, spec.compiler.boundmass)
    donor = spec.geom("c_thorax")
    if donor.mass <= support_mass:
        raise ValueError("Insufficient thoracic mass for cervical support")

    # The reference placement is the existing rig, not the paper's fitted posture.
    support = thorax.add_body(name="neck_cervical_sclerite", pos=pivot)
    support.add_geom(name="neck_cervical_sclerite", type=mj.mjtGeom.mjGEOM_BOX,
        size=(0.020, 0.100, 0.025), mass=support_mass, group=3, contype=0, conaffinity=0)
    donor.mass -= support_mass
    for owner, names in ((head, HEAD_JOINTS), (support, SUPPORT_JOINTS)):
        for name, axis in zip(names, ((0, 0, 1), (1, 0, 0), (0, 1, 0))):
            owner.add_joint(name=name, type=mj.mjtJoint.mjJNT_HINGE, axis=axis,
                limited=True, range=(-0.5, 0.5), stiffness=0, damping=0.005)
    # Two head condyles retain bilateral contact with a single rigid support.
    # This point articulation leaves head pitch relative to the support free.
    # No qpos target, fitted action field or feedback controller is installed.
    for side, sign in (("left", 1), ("right", -1)):
        spec.add_equality(name=f"neck_condyle_{side}", type=mj.mjtEq.mjEQ_CONNECT,
            objtype=mj.mjtObj.mjOBJ_BODY,
            name1=support.name, name2=head.name, data=[0, sign * 0.075, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            solref=(0.0002, 1), solimp=(0.999, 0.999, 0.001, 0.5, 2))

    # origin relative to the neck pivot (thorax), insertion in head/support frame.
    # VL origins: sternal apodeme; TH origins: pleural/posterior thoracic wall;
    # AD/LEV origins: dorsal pronotal region. Lateral offsets are mirror estimates.
    paths = (
        ("VL1", (-0.330, 0.145, -0.200), head, (-0.010, 0.090, -0.060), 0.25),
        ("VL2", (-0.320, 0.100, -0.190), head, (-0.010, 0.055, -0.055), 0.25),
        ("TH1", (-0.360, 0.280, 0.100), head, (-0.008, 0.090, 0.065), 0.25),
        ("TH2", (-0.300, 0.260, 0.055), head, (-0.008, 0.084, 0.062), 0.25),
        ("AD", (-0.120, 0.025, 0.120), support, (-0.020, 0.080, -0.020), 0.05),
        ("LEV", (-0.100, 0.110, 0.160), support, (-0.025, 0.075, -0.030), 0.05),
    )
    records = []
    for side, sign in (("left", 1), ("right", -1)):
        for target, origin, owner, insertion, tendon_fraction in paths:
            origin = np.array(origin) * [1, sign, 1]
            insertion = np.array(insertion) * [1, sign, 1]
            length = float(np.linalg.norm(insertion - origin))
            name = f"neck_muscle_{side}_{target}"
            record = dict(limb="neck", side=side, peripheral_target_side=side[0].upper(),
                peripheral_target_sides=[side[0].upper()], peripheral_target_topology="unilateral",
                muscle_target=target, target_muscle=target, semantic_muscle_key=f"neck.{target}",
                muscle_group=target, group_capacity_fraction=1.0,
                local_actuator_name=name, actuator_name=f"{fly.name}/{name}",
                local_tendon_name=f"{name}_tendon", tendon_name=f"{fly.name}/{name}_tendon",
                joint_names={joint: f"{fly.name}/{joint}" for joint in (HEAD_JOINTS if owner is head else SUPPORT_JOINTS)},
                sites=[dict(local_name=f"{name}_origin", body=thorax.name, pos_mm=(pivot + origin).tolist()),
                       dict(local_name=f"{name}_insertion", body=owner.name, pos_mm=insertion.tolist())],
                reference_length_mm=length, optimal_fiber_length_mm=(1 - tendon_fraction) * length,
                tendon_length_mm=tendon_fraction * length, force_uN=float(group_force_uN),
                activation_time_s=times.tolist(), motor_neuron_ids=[], mapping_status="unmapped",
                anatomy_source=ANATOMY_SOURCE, geometry_status="anatomical_topology_rig_metric_estimate",
                geometry_provenance="Gorko Extended Data Fig. 7; explicit estimated coordinates in head_muscles.py",
                bilateral_geometry_status="assumed_mirror_not_measured",
                force_provenance="Unmeasured per-side group capacity; default 28 uN, no action-field fitting",
                parameter_status="estimated_not_behavior_fitted",
                mechanical_limitations=["Rigid condylar support approximation; no sclerite deformation",
                    "TH curvature and OH-to-TH tendon coupling are not reconstructed"])
            _add_mtu(fly, record, (0.5, 1.6, 1.5, 1.3, 1.2))
            records.append(record)
    records += _add_sensory_head_muscles(fly, times, sensory_force_uN)
    fly._rebuild_neutral_keyframe()
    return records
