"""Estimated adult proboscis mechanics on the existing NeuroMechFly bodies.

Call add_proboscis_muscles(fly) once, before world attachment. It returns one
metadata record per independently excited muscle, with world-qualified names.
ctrl is bounded excitation, not an angle; MuJoCo integrates muscle activation.
No neuron IDs, NMJ events, policies, initial movements or sensory mappings live here.
See docs/research/whole-proboscis-mechanics.md for anatomy and estimate provenance.
"""
import hashlib
import json
from pathlib import Path

import mujoco as mj
import numpy as np
from flygym.anatomy import BodySegment
from flygym.compose import NeuroMechFly
from flygym.compose.fly.base_fly import ActuatorType


M9_CONFIG = Path(__file__).with_name("muscle9.json")
ANATOMY_SOURCE = "https://elifesciences.org/articles/54978"
JOINT_NAMES = {"rostrum": "proboscis_rostrum_pitch", "haustellum": "proboscis_haustellum_pitch"}
REACHING_TARGETS = ("m1", "m2D", "m2V", "m3L", "m3M", "m4", "m9")
PUMP_TARGETS = ("m5", "m8", "m10", "m11D", "m11V", "m12D", "m12V")
MUSCLE_TARGETS = REACHING_TARGETS + ("m6", "m7") + PUMP_TARGETS + ("m13",)
UNIMPLEMENTED_TARGETS = {}  # All McKellar muscle targets now have mechanical paths.
LABELLUM_GEOMS = ("proboscis_labellum_left", "proboscis_labellum_right")


def _add_mtu(fly, record, curve):
    """Install the same native constitutive law for proboscis and neck paths."""
    spec = fly.mjcf_root
    for site in record["sites"]:
        spec.body(site["body"]).add_site(name=site["local_name"], pos=site["pos_mm"],
                                        size=(0.003, 0, 0), group=3)
    tendon = spec.add_tendon(name=record["local_tendon_name"], width=0.002,
                            stiffness=0, damping=0, group=3)
    for site in record["sites"]:
        tendon.wrap_site(site["local_name"])
    lengthrange = [record["tendon_length_mm"] + r * record["optimal_fiber_length_mm"] for r in (0.25, 1.25)]
    prm = [0.25, 1.25, record["force_uN"], 200, *curve, 0]
    name = record["local_actuator_name"]
    actuator = spec.add_actuator(name=name, trntype=mj.mjtTrn.mjTRN_TENDON,
        target=record["local_tendon_name"], gear=(1, 0, 0, 0, 0, 0), lengthrange=lengthrange,
        ctrllimited=True, ctrlrange=(0, 1), actlimited=True, actrange=(0, 1),
        dyntype=mj.mjtDyn.mjDYN_MUSCLE, dynprm=[*record["activation_time_s"], 0, 0, 0, 0, 0, 0, 0, 0],
        gaintype=mj.mjtGain.mjGAIN_MUSCLE, gainprm=prm,
        biastype=mj.mjtBias.mjBIAS_MUSCLE, biasprm=prm)
    fly.jointdof_to_mjcfactuator_by_type[ActuatorType.MUSCLE][name] = actuator
    fly.jointdof_to_neutralaction_by_type[ActuatorType.MUSCLE][name] = 0.0


def _labellar_mesh_parts(fly):
    """Partition existing triangles, preserving the complete q=0 outer surface."""
    spec = fly.mjcf_root.copy()
    spec.compiler.fusestatic = False
    model = spec.compile()
    gid = model.geom("c_haustellum").id
    mid = model.geom_dataid[gid]
    start, count = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
    rotation = np.empty(9)
    mj.mju_quat2Mat(rotation, model.geom_quat[gid])
    vertices = model.mesh_vert[start:start + count] @ rotation.reshape(3, 3).T + model.geom_pos[gid]
    start, count = model.mesh_faceadr[mid], model.mesh_facenum[mid]
    faces = model.mesh_face[start:start + count].copy()
    centers = vertices[faces].mean(axis=1)
    # ponytail: estimated anatomical segmentation of the fused NMF distal mesh;
    # replace these cuts with registered tissue labels when those are available.
    distal = (centers[:, 0] > 0.105) & (centers[:, 2] < -0.080)
    masks = {"shaft": ~distal, "left": distal & (centers[:, 1] >= 0),
             "right": distal & (centers[:, 1] < 0)}
    assert sum(int(mask.sum()) for mask in masks.values()) == len(faces)
    parts = {}
    for name, mask in masks.items():
        selected = faces[mask]
        used, inverse = np.unique(selected, return_inverse=True)
        if len(used) < 4:
            raise ValueError("Haustellum mesh cannot support the estimated labellar partition")
        parts[name] = (vertices[used].copy(), inverse.reshape(-1, 3))
    return parts


def _add_distal_and_pump_bodies(fly, bodies, offsets):
    """Fig. 6 serial wall patches/valve and Fig. 9 paired labella, without fluid policy."""
    spec = fly.mjcf_root
    parts = _labellar_mesh_parts(fly)
    haustellum_geom = spec.geom("c_haustellum")
    rostrum_geom = spec.geom("c_rostrum")
    # Redistribute existing soft-tissue mass instead of adding duplicated mass.
    wall_mass = max(1e-6, spec.compiler.boundmass)
    h_mass, r_mass = haustellum_geom.mass - 2 * wall_mass, rostrum_geom.mass - 6 * wall_mass
    if h_mass / 3 < spec.compiler.boundmass or r_mass <= 0:
        raise ValueError("Insufficient proboscis mass for resolved walls/labella")
    extras = {"left": [], "right": []}
    for part, (vertices, faces) in parts.items():
        pivot = np.zeros(3) if part == "shaft" else np.array([0.13, 0.045 if part == "left" else -0.045, -0.09])
        mesh_name = f"proboscis_{part}_surface"
        spec.add_mesh(name=mesh_name, uservert=(vertices - pivot).ravel().tolist(), userface=faces.ravel().tolist())
        if part == "shaft":
            haustellum_geom.meshname = mesh_name
            haustellum_geom.mass = h_mass / 3
            continue
        body_key = f"labellum_{part}"
        body = bodies["haustellum"].add_body(name=f"proboscis_{body_key}", pos=pivot)
        bodies[body_key], offsets[body_key] = body, offsets["haustellum"] + pivot
        sign = 1 if part == "left" else -1
        body.add_joint(name=f"proboscis_{body_key}_extension", type=mj.mjtJoint.mjJNT_HINGE,
            axis=(0, 1, 0), limited=True, range=(-0.3, 0.8), stiffness=0.02, damping=0.0002)
        body.add_joint(name=f"proboscis_{body_key}_abduction", type=mj.mjtJoint.mjJNT_HINGE,
            axis=(sign, 0, 0), limited=True, range=(-0.05, 0.8), stiffness=0.02, damping=0.0002)
        body.add_geom(name=f"proboscis_{body_key}", type=mj.mjtGeom.mjGEOM_MESH,
            meshname=mesh_name, mass=h_mass / 3, group=haustellum_geom.group,
            material=haustellum_geom.material, rgba=haustellum_geom.rgba,
            contype=0, conaffinity=0)
        extras[part] += [
            ("m6", "haustellum", np.array([0.03, 0.045, -0.02]), body_key, np.array([0.02, 0, -0.035]), None, 1.0),
            ("m7", "haustellum", np.array([0.035, 0.020, -0.015]), body_key, np.array([-0.015, 0.015, 0.025]), None, 1.0),
        ]
    rostrum_geom.mass = r_mass
    # Order/owners follow Fig. 6A. Coordinates and directions are projected rig
    # estimates; each wall translates OUT toward its own cuticular origins.
    wall_paths = (
        ("m10", "rostrum", (-0.035, 0, 0.140), (0.095, 0.060, 0.170)),
        ("m11D", "rostrum", (-0.110, 0, 0.090), (0.020, 0.075, 0.100)),
        ("m11V", "rostrum", (-0.180, 0, 0.050), (-0.020, 0.065, 0.045)),
        ("m12D", "rostrum", (-0.245, 0, 0.010), (-0.065, 0.065, 0.025)),
        ("m12V", "rostrum", (-0.315, 0, -0.015), (-0.245, 0.050, -0.025)),
        ("m13", "rostrum", (-0.335, 0, -0.020), (-0.345, 0.045, 0.060)),
        ("m5", "haustellum", (0.070, 0, -0.035), (0.095, 0.045, 0.020)),
        ("m8", "haustellum", (0.130, 0, -0.075), (0.070, 0.050, -0.125)),
    )
    for target, owner, position, origin in wall_paths:
        position, origin = np.array(position), np.array(origin)
        axis = origin - position
        axis[1] = 0
        axis /= np.linalg.norm(axis)
        key = f"wall_{target}"
        body = bodies[owner].add_body(name=f"proboscis_{key}", pos=position)
        bodies[key], offsets[key] = body, offsets[owner] + position
        body.add_joint(name=f"proboscis_{target}_dilation", type=mj.mjtJoint.mjJNT_SLIDE,
            axis=axis, limited=True, range=(-0.004, 0.025), stiffness=2000, damping=0.1)
        rotation = np.empty(4)
        mj.mju_quatZ2Vec(rotation, axis)
        body.add_geom(name=f"proboscis_{key}", type=mj.mjtGeom.mjGEOM_BOX, quat=rotation,
            size=(0.018, 0.035, 0.002), mass=wall_mass, contype=0, conaffinity=0,
            rgba=(0.7, 0.3, 0.35, 1), group=3)
        for side in extras:
            extras[side].append((target, owner, origin, key, np.array([0, 0.012, 0]), None, 1.0))
    return extras


def _add_crop_entry_muscle(fly, force_uN, times):
    """One unpaired circumferential muscle group at the crop-entry junction.

    Yang 2024 Fig. 5b-c/6 support the organ/terminal topology and constriction;
    four radial wall patches are an estimated material discretization, not four
    identified muscles or neurons. The one closed tendon has one total capacity.
    """
    spec = fly.mjcf_root
    parent = fly.bodyseg_to_mjcfbody[BodySegment("c_abdomen12")]
    donor = spec.geom("c_abdomen12")
    wall_mass = max(1e-6, spec.compiler.boundmass)
    if donor.mass <= 4 * wall_mass:
        raise ValueError("Insufficient abdominal mass for crop-entry wall patches")
    center, radius = np.array([0.050, 0, 0.030]), 0.025
    sites, joints = [], {}
    for index, axis in enumerate(((0, 1, 0), (0, 0, 1), (0, -1, 0), (0, 0, -1))):
        axis = np.array(axis, dtype=float)
        name = f"gut_crop_entry_wall_{index}"
        body = parent.add_body(name=name, pos=center + radius * axis)
        joint = f"{name}_radial"
        body.add_joint(name=joint, type=mj.mjtJoint.mjJNT_SLIDE, axis=axis,
            limited=True, range=(-0.015, 0.005), stiffness=2000, damping=0.1)
        body.add_geom(name=name, type=mj.mjtGeom.mjGEOM_SPHERE, size=(0.004, 0, 0),
            mass=wall_mass, contype=0, conaffinity=0, group=3)
        sites.append(dict(local_name=f"{name}_site", body=name, pos_mm=[0, 0, 0]))
        joints[f"radial_{index}"] = f"{fly.name}/{joint}"
    donor.mass -= 4 * wall_mass
    # Close the polygon using a second co-located endpoint site; no force duplication.
    sites.append(dict(sites[0], local_name="gut_crop_entry_close_site"))
    length = 4 * np.sqrt(2) * radius
    name = "gut_crop_entry_muscle"
    record = dict(limb="gut", side="unpaired", peripheral_target_side=None,
        peripheral_target_sides=[], peripheral_target_topology="unpaired_organ_group",
        muscle_target="crop-entry muscles", target_muscle="crop-entry muscles",
        semantic_muscle_key="gut.crop_entry_muscles", muscle_group="crop-entry muscles",
        group_capacity_fraction=1.0, local_actuator_name=name, actuator_name=f"{fly.name}/{name}",
        local_tendon_name=f"{name}_tendon", tendon_name=f"{fly.name}/{name}_tendon",
        sites=sites, joint_names=joints, reference_length_mm=float(length),
        optimal_fiber_length_mm=float(0.95 * length), tendon_length_mm=float(0.05 * length),
        force_uN=float(force_uN), activation_time_s=list(times), motor_neuron_ids=[], mapping_status="unmapped",
        anatomy_source="https://pmc.ncbi.nlm.nih.gov/articles/PMC11398398/",
        geometry_status="unpaired_organ_group_with_estimated_radial_wall_discretization",
        geometry_provenance="Yang 2024 Fig. 5b-c; anterior abdominal registration and 25 um radius estimated",
        parameter_status="estimated_not_behavior_fitted", force_provenance="Unmeasured capacity of whole unpaired group",
        pumping_scope="crop_entry_constriction_only_no_fluid_transport",
        rest_radius_mm=radius, anatomical_cell_partition="unresolved")
    _add_mtu(fly, record, (0.5, 1.6, 1.5, 1.3, 1.2))
    return record


def add_proboscis_muscles(fly, *, group_force_uN=28.0, activation_time_s=None):
    """Add 34 paired mouth MTUs plus one unpaired crop-entry muscle group.

    Geometry is schematic-informed, unmeasured, and unfitted. M9's existing
    geometry, force and curves are retained; only its geometric mirror is added.
    Other groups receive group_force_uN per side (M3 split equally between L/M).
    activation_time_s overrides both sides/all groups; default is M9's 10/40 ms.
    This function requires the unchanged head/rostrum/haustellum rig frames and
    no existing proboscis joints. Existing leg joints/actuators are preserved.
    """
    if not isinstance(fly, NeuroMechFly):
        raise ValueError("Proboscis attachment estimates require NeuroMechFly")
    spec = fly.mjcf_root
    bodies = {name: fly.bodyseg_to_mjcfbody[BodySegment(f"c_{name}")]
              for name in ("head", "rostrum", "haustellum")}
    for name, parent, position in (("rostrum", "head", (0.43, 0, -0.274)),
                                    ("haustellum", "rostrum", (-0.371, 0, -0.0196))):
        body = bodies[name]
        if list(body.joints):
            raise ValueError("Proboscis joints already present; refusing duplicate mechanics")
        if (body.parent.name != f"c_{parent}"
                or not np.allclose(body.pos, position, atol=1e-9, rtol=0)
                or not np.allclose(body.quat, (1, 0, 0, 0), atol=1e-9, rtol=0)):
            raise ValueError("Proboscis rig changed; attachment estimates require re-registration")
    if any(e.name.startswith("proboscis_") for e in (*spec.actuators, *spec.tendons, *spec.sites)):
        raise ValueError("Proboscis names already present; refusing duplicate mechanics")

    raw = M9_CONFIG.read_bytes()
    p = json.loads(raw)
    times = np.asarray(p["activation_time_s"] if activation_time_s is None else activation_time_s, dtype=float)
    if (times.shape != (2,) or not np.isfinite(times).all() or np.any(times < 0.001)
            or not np.isfinite(group_force_uN) or group_force_uN <= 0):
        raise ValueError("Require positive finite force and two activation times >= 1 ms")
    for key in ("origin_head_mm", "insertion_rostrum_mm"):
        point = np.asarray(p[key], dtype=float)
        if point.shape != (3,) or not np.isfinite(point).all() or point[1] >= 0:
            raise ValueError(f"Invalid right M9 attachment: {key}")
    positive = ("optimal_fiber_length_mm", "tendon_length_mm", "force_uN", "vmax", "fpmax", "fvmax")
    if (any(not np.isfinite(p[k]) or p[k] <= 0 for k in positive)
            or not 0 < p["lmin"] < 1 < p["lmax"] or not np.isfinite(p["lmax"])):
        raise ValueError("Require positive M9 fiber/tendon lengths and valid force curves")
    rostrum_range = np.asarray(p["joint_range_rad"], dtype=float)
    damping = p["passive_damping_nNm_s_per_rad"]
    if (rostrum_range.shape != (2,) or not np.isfinite(rostrum_range).all()
            or not rostrum_range[0] < 0 < rostrum_range[1]
            or not np.isfinite(damping) or damping < 0):
        raise ValueError("Invalid estimated joint limits or damping")

    pivot = np.asarray(bodies["rostrum"].pos)
    distal = np.asarray(bodies["haustellum"].pos)
    span = float(np.linalg.norm(distal))
    # Fractions of the rig's 0.3715 mm inter-pivot span, NOT image measurements.
    # m1/2 origins approximate the posterior head wall in Fig. 7M-O.
    # m3 crosses from anterior rostrum; m4 pulls the free dorsal Y-arm (Fig. 8).
    # muscle, origin owner/point, insertion owner/point, lateral depth, capacity share
    paths = [
        ("m1", "head", pivot + span * np.array([-1.10, 0, 1.40]),
         "rostrum", distal + span * np.array([0.02, 0, 0.02]), 0.07, 1.0),
        ("m2D", "head", pivot + span * np.array([-1.10, 0, 0.65]),
         "rostrum", distal + span * np.array([-0.015, 0, 0.04]), 0.07, 1.0),
        ("m2V", "head", pivot + span * np.array([-1.10, 0, 0.50]),
         "haustellum", span * np.array([0.08, 0, -0.08]), 0.07, 1.0),
        ("m3L", "rostrum", span * np.array([0.03, 0, -0.10]),
         "haustellum", span * np.array([0.10, 0, -0.09]), 0.09, 0.5),
        ("m3M", "rostrum", span * np.array([0.03, 0, -0.10]),
         "haustellum", span * np.array([0.10, 0, -0.09]), 0.04, 0.5),
        ("m4", "rostrum", distal + span * np.array([0.15, 0, 0.02]),
         "haustellum", span * np.array([-0.07, 0, 0.15]), 0.07, 1.0),
        ("m9", "head", np.asarray(p["origin_head_mm"], dtype=float),
         "rostrum", np.asarray(p["insertion_rostrum_mm"], dtype=float), None, 1.0),
    ]
    offsets = {"head": np.zeros(3), "rostrum": pivot, "haustellum": pivot + distal}
    extras = _add_distal_and_pump_bodies(fly, bodies, offsets)
    records = []
    for side in ("left", "right"):
        for target, origin_body, origin, insertion_body, insertion, depth, share in paths + extras[side]:
            name = f"proboscis_muscle_{side}_{target}"
            points = [np.array(origin, copy=True), np.array(insertion, copy=True)]
            for point in points:
                point[1] = (abs(point[1]) if depth is None else depth) * (1 if side == "left" else -1)
            length = float(np.linalg.norm(points[1] + offsets[insertion_body] - points[0] - offsets[origin_body]))
            # ponytail: straight, inextensible tendon with estimated fiber/tendon
            # partition; replace with measured paths/compliance when available.
            tendon_length = p["tendon_length_mm"] if target == "m9" else 0.05 * length
            fiber_length = p["optimal_fiber_length_mm"] if target == "m9" else length - tendon_length
            if not 0 < tendon_length < length or not np.isfinite(fiber_length) or fiber_length <= 0:
                raise ValueError(f"Invalid fiber/tendon geometry for {name}")
            if target in REACHING_TARGETS:
                joints = (("rostrum",) if target in ("m1", "m2D", "m9") else
                          ("rostrum", "haustellum") if target == "m2V" else ("haustellum",))
                joint_names = {joint: f"{fly.name}/{JOINT_NAMES[joint]}" for joint in joints}
            elif target in ("m6", "m7"):
                joint_names = {joint: f"{fly.name}/proboscis_labellum_{side}_{joint}" for joint in ("extension", "abduction")}
            else:
                joint_names = {"dilation": f"{fly.name}/proboscis_{target}_dilation"}
            records.append(dict(
                limb="proboscis", side=side, peripheral_target_side=side[0].upper(),
                peripheral_target_sides=[side[0].upper()], peripheral_target_topology="unilateral",
                muscle_target=target, target_muscle=target, semantic_muscle_key=f"proboscis.{target}",
                muscle_group="m3" if target.startswith("m3") else target,
                group_capacity_fraction=share, motor_neuron_ids=[], mapping_status="unmapped",
                local_actuator_name=name, actuator_name=f"{fly.name}/{name}",
                local_tendon_name=f"{name}_tendon", tendon_name=f"{fly.name}/{name}_tendon",
                joint_names=joint_names,
                sites=[dict(local_name=f"{name}_{end}", body=bodies[body].name, pos_mm=point.tolist())
                       for end, body, point in zip(("origin", "insertion"), (origin_body, insertion_body), points)],
                reference_length_mm=length, optimal_fiber_length_mm=fiber_length,
                tendon_length_mm=tendon_length,
                force_uN=p["force_uN"] if target == "m9" else group_force_uN * share,
                activation_time_s=times.tolist(),
                anatomy_source=ANATOMY_SOURCE + ("#fig7" if target in ("m1", "m2D", "m9") else
                    "#fig8" if target in ("m2V", "m3L", "m3M", "m4") else "#fig9" if target in ("m6", "m7") else "#fig6"),
                geometry_status="inherited_M9_estimate" if target == "m9" else
                    "schematic_informed_rig_fraction_estimate" if target in REACHING_TARGETS else
                    "primary_topology_estimated_internal_geometry",
                bilateral_geometry_status="assumed_mirror_not_measured",
                geometry_provenance=p["geometry_provenance"] if target == "m9" else
                    {"rig_span_mm": span, "method": "declared fractions; not digitized coordinates"} if target in REACHING_TARGETS else
                    {"method": "explicit estimated body-local coordinates; Fig. 6/9 topology; labellar surface partition preserves the existing q=0 scan"},
                m9_config_sha256=hashlib.sha256(raw).hexdigest() if target == "m9" else None,
                force_provenance=p["force_provenance"] if target == "m9" else
                    "Assumed group capacity; default 0.001 mm^2 PCSA x 28 mN/mm^2 cross-muscle estimate; M3 split equally",
                parameter_status="estimated_not_behavior_fitted",
                contact_geom_names=[f"{fly.name}/proboscis_labellum_{side}"] if target in ("m6", "m7") else [],
                wall_area_mm2=0.00252 if target in PUMP_TARGETS + ("m13",) else None,
                rest_lumen_gap_mm=0.012 if target in PUMP_TARGETS + ("m13",) else None,
                pumping_scope="elastic_wall_or_valve_only_no_fluid_transport" if target in PUMP_TARGETS + ("m13",) else None))

    # No existing joints change. The new walls recoil passively; no cycling input.
    for joint, limits in (("rostrum", rostrum_range), ("haustellum", (-0.1, 1.5))):
        bodies[joint].add_joint(name=JOINT_NAMES[joint], type=mj.mjtJoint.mjJNT_HINGE,
            axis=(0, 1, 0), limited=True, range=limits, stiffness=0, damping=damping)
    for record in records:
        _add_mtu(fly, record, [p[k] for k in ("lmin", "lmax", "vmax", "fpmax", "fvmax")])
    records.append(_add_crop_entry_muscle(fly, group_force_uN, times))
    fly._rebuild_neutral_keyframe()
    return records


class ProboscisHydraulics:
    """Primed, passive eight-cell fluid circuit driven by actual lumen geometry.

    Seven serial pharyngeal cells follow Fig. 6A; the eighth is the crop-entry
    junction, with a separate proventricular outlet. All dimensions, viscosity
    and effective compressibility are estimates. This is not a dry/air/liquid
    interface or a complete digestion model. No muscle excitation is produced.
    Call reset(data), then advance(data, dt_s, inlet_pressure_pa=...) and add
    generalized_forces(data) to this step's applied-force buffer before mj_step.
    A None inlet pressure seals the inlet; the caller must establish liquid contact.
    """
    ORDER = ("m8", "m5", "m12V", "m12D", "m11V", "m11D", "m10")

    def __init__(self, model, *, fly_name="fly", viscosity_pa_s=0.001, effective_bulk_modulus_pa=10000.0):
        if (not np.isfinite(viscosity_pa_s) or viscosity_pa_s <= 0
                or not np.isfinite(effective_bulk_modulus_pa) or effective_bulk_modulus_pa <= 0):
            raise ValueError("Require positive finite viscosity and effective bulk modulus")
        self.model, self.mu, self.bulk = model, viscosity_pa_s, effective_bulk_modulus_pa
        prefix = f"{fly_name}/" if fly_name else ""
        self.wall_joints = [model.joint(f"{prefix}proboscis_{target}_dilation") for target in self.ORDER]
        self.crop_joints = [model.joint(f"{prefix}gut_crop_entry_wall_{i}_radial") for i in range(4)]
        self.valve_joint = model.joint(f"{prefix}proboscis_m13_dilation")
        self.wall_area_mm2 = 0.00252
        self.duct_length_mm = 0.05
        self.crop_length_mm = 0.10
        self.pressure_pa = np.zeros(8)
        self.liquid_volume_mm3 = None

    def _geometry(self, data):
        gap = 0.012 + np.array([data.qpos[j.qposadr[0]] for j in self.wall_joints])
        radial = 0.025 + np.array([data.qpos[j.qposadr[0]] for j in self.crop_joints])
        valve_gap = 0.012 + float(data.qpos[self.valve_joint.qposadr[0]])
        if not np.isfinite(np.r_[gap, radial, valve_gap]).all() or min(*gap, *radial, valve_gap) <= 0:
            raise ValueError("Nonpositive or nonfinite physical lumen geometry")
        a, b = float(radial[[0, 2]].mean()), float(radial[[1, 3]].mean())
        volumes = np.r_[self.wall_area_mm2 * gap, np.pi * a * b * self.crop_length_mm]
        return volumes, gap / 2, a, b, valve_gap / 2

    def reset(self, data):
        """Explicit initial condition: liquid-filled cells at ambient pressure."""
        volumes, *_ = self._geometry(data)
        self.liquid_volume_mm3 = volumes.copy()
        self.capacitance_mm3_pa = volumes / self.bulk
        self.pressure_pa[:] = 0
        self.net_boundary_volume_mm3 = {name: 0.0 for name in ("inlet", "crop", "proventriculus", "saliva")}

    def advance(self, data, dt_s, *, inlet_pressure_pa=None, crop_pressure_pa=0.0,
                proventriculus_pressure_pa=0.0, salivary_pressure_pa=None):
        """Implicit conservation step; positive boundary flow enters the circuit."""
        pressures = (inlet_pressure_pa, crop_pressure_pa, proventriculus_pressure_pa, salivary_pressure_pa)
        if (not np.isfinite(dt_s) or dt_s <= 0
                or any(p is not None and not np.isfinite(p) for p in pressures)):
            raise ValueError("Require positive dt and finite boundary pressures or None")
        if self.liquid_volume_mm3 is None:
            raise ValueError("Call reset(data) to declare the primed initial condition")
        volumes, radius, a, b, valve_radius = self._geometry(data)
        # Poiseuille conductance in mm^3/(Pa s), without an SI/mm conversion factor.
        conductance = lambda r, length: np.pi * r**4 / (8 * self.mu * length)
        links = [(i, i + 1, conductance(min(radius[i], radius[i + 1]), self.duct_length_mm)) for i in range(6)]
        crop_g = np.pi * a**3 * b**3 / (4 * self.mu * self.crop_length_mm * (a*a + b*b))
        links.append((6, 7, crop_g))
        boundaries = [(0, "inlet", inlet_pressure_pa, conductance(radius[0], self.duct_length_mm)),
            (7, "crop", crop_pressure_pa, crop_g),
            (6, "proventriculus", proventriculus_pressure_pa, conductance(radius[-1], self.duct_length_mm)),
            (2, "saliva", salivary_pressure_pa, conductance(valve_radius, self.duct_length_mm))]
        matrix = np.diag(self.capacitance_mm3_pa / dt_s)
        rhs = (self.liquid_volume_mm3 - volumes) / dt_s
        for i, j, g in links:
            matrix[i, i] += g
            matrix[j, j] += g
            matrix[i, j] -= g
            matrix[j, i] -= g
        for i, name, pressure, g in boundaries:
            if pressure is not None:
                matrix[i, i] += g
                rhs[i] += g * pressure
        pressure = np.linalg.solve(matrix, rhs)
        liquid = volumes + self.capacitance_mm3_pa * pressure
        if not np.isfinite(liquid).all() or np.any(liquid <= 0):
            raise ValueError("Outside the primed linear-compliance domain; no fluid clipping or creation")
        flows = {name: 0.0 if p is None else float(g * (p - pressure[i])) for i, name, p, g in boundaries}
        residual = float(liquid.sum() - self.liquid_volume_mm3.sum() - dt_s * sum(flows.values()))
        self.pressure_pa, self.liquid_volume_mm3 = pressure, liquid
        for name, flow in flows.items():
            self.net_boundary_volume_mm3[name] += dt_s * flow
        dissipation = sum(g * (pressure[i] - pressure[j])**2 for i, j, g in links)
        dissipation += sum(g * (pressure[i] - p)**2 for i, name, p, g in boundaries if p is not None)
        return dict(pressure_pa=pressure.tolist(), geometry_volume_mm3=volumes.tolist(),
            liquid_volume_mm3=liquid.tolist(), boundary_flow_mm3_s=flows,
            net_boundary_volume_mm3=dict(self.net_boundary_volume_mm3),
            conservation_residual_mm3=residual, hydraulic_dissipation_nW=float(dissipation),
            scope="primed estimated pressure-flow circuit; not dry feeding or validated ingestion")

    def generalized_forces(self, data):
        """Return a fresh native uN/nNm force vector; never accumulate into data."""
        _, _, a, b, _ = self._geometry(data)
        forces = np.zeros(self.model.nv)
        for joint, pressure in zip(self.wall_joints, self.pressure_pa):
            forces[joint.dofadr[0]] = pressure * self.wall_area_mm2
        # Pressure times dV/dq is work-conjugate to each radial wall displacement.
        for i, joint in enumerate(self.crop_joints):
            forces[joint.dofadr[0]] = self.pressure_pa[-1] * np.pi * (b if i % 2 == 0 else a) * self.crop_length_mm / 2
        return forces
