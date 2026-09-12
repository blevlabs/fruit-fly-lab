"""Isolated constitutive flight components, NOT a flight controller.

No phase, frequency, angle target, default neural drive, or motor-ID mapping.
The muscle is a small-strain estimated material law; the free-wing fixture
tests native fluid forces. ReducedThorax adds an explicitly hypothetical
rhombic scutum and planar ax1/ax2 linkage, not a reconstructed complete hinge.
See docs/research/whole-body-flight-mechanics.md for evidence and units.
"""
from dataclasses import dataclass, fields, replace
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from neuromuscular import NeuromuscularJunction


@dataclass(frozen=True)
class IFMParameters:
    """Reference-condition estimates, not a fitted adult DLM/DVM parameter set."""

    reference_length_mm: float = 1.0
    area_mm2: float = 0.01
    isometric_stress_pa: float = 1400.0
    passive_prestress_pa: float = 2800.0
    passive_modulus_pa: float = 570000.0
    stretch_modulus_pa: float = 500000.0
    stretch_rise_s: float = 0.001
    stretch_decay_s: float = 0.010
    activation_tau_s: float = 0.050
    max_abs_strain: float = 0.03
    nmj_delay_s: float = 0.001
    nmj_decay_s: float = 0.100
    nmj_recovery_s: float = 0.100
    nmj_gain: float = 0.2
    nmj_depression: float = 0.2


class StretchActivatedMuscle:
    """Spike -> delayed NMJ -> availability -> stretch-dependent tensile force.

    advance() samples physical length at the interval start and accepts a spike
    emitted at its end (the existing NMJ convention). It returns a midpoint
    force approximation under held length/excitation over that interval.
    Activation is dimensionless availability, NOT measured calcium concentration.
    """

    def __init__(self, dt_s, parameters=IFMParameters()):
        p = parameters
        if not math.isfinite(dt_s) or dt_s <= 0:
            raise ValueError('dt_s must be finite and positive')
        if any(not math.isfinite(getattr(p, f.name)) for f in fields(p)):
            raise ValueError('Muscle parameters must be finite')
        positive = ('reference_length_mm', 'area_mm2', 'stretch_rise_s',
                    'stretch_decay_s', 'activation_tau_s', 'max_abs_strain')
        if any(getattr(p, name) <= 0 for name in positive):
            raise ValueError('Lengths, area, time constants and strain bound must be positive')
        if not p.stretch_rise_s < p.stretch_decay_s or p.max_abs_strain >= 1:
            raise ValueError('Require rise < decay and a strain bound below one')
        if min(p.isometric_stress_pa, p.passive_prestress_pa,
               p.passive_modulus_pa, p.stretch_modulus_pa) < 0:
            raise ValueError('Stress and modulus scales must be nonnegative')
        self.p, self.dt = p, dt_s
        self.nmj = NeuromuscularJunction(dt_s, dict(
            delay_s=p.nmj_delay_s, tau_exc_s=p.nmj_decay_s,
            tau_recovery_s=p.nmj_recovery_s, spike_gain=p.nmj_gain,
            depression=p.nmj_depression))
        self.reset()

    def reset(self):
        self.activation = self.fast_strain = self.slow_strain = 0.0
        self.nmj.reset()

    def advance(self, length_mm, spike_at_end=False, *, release_block=False):
        if not math.isfinite(length_mm) or length_mm <= 0:
            raise ValueError('Physical fiber length must be finite and positive')
        p = self.p
        strain = length_mm / p.reference_length_mm - 1
        if abs(strain) > p.max_abs_strain + 1e-12:
            raise ValueError('Outside the declared small-strain material domain')
        excitation = self.nmj.advance(spike_at_end, release_block=release_block)
        midpoints = []
        for name, target, tau in (
            ('activation', excitation, p.activation_tau_s),
            ('fast_strain', strain, p.stretch_rise_s),
            ('slow_strain', strain, p.stretch_decay_s),
        ):
            old = getattr(self, name)
            half_decay = math.exp(-self.dt / (2 * tau))
            midpoints.append(target + (old - target) * half_decay)
            setattr(self, name, target + (old - target) * half_decay ** 2)
        activation, fast, slow = midpoints
        # ponytail: linear small-strain response; replace with measured nonlinear
        # cross-bridge kinetics before making full-stroke or power-budget claims.
        stretch_stress = activation * p.stretch_modulus_pa * (fast - slow)
        active_stress = max(0.0, activation * p.isometric_stress_pa + stretch_stress)
        passive_stress = max(0.0, p.passive_prestress_pa + p.passive_modulus_pa * strain)
        # Pa * mm^2 = microNewtons exactly; tensile power is -F * fiber velocity.
        return dict(excitation=excitation, activation=activation, strain=strain,
                    stretch_stress_pa=stretch_stress,
                    active_force_uN=p.area_mm2 * active_stress,
                    passive_force_uN=p.area_mm2 * passive_stress,
                    tension_uN=p.area_mm2 * (active_stress + passive_stress))


def free_wing_xml(*, side='left', dt_s=0.00001,
                  density_g_per_mm3=1.28e-6, viscosity_g_per_mm_s=1.85e-5,
                  fluid_coefficients=(0.5, 0.25, 1.5, 1.0, 1.0)):
    """Meshless free wing from the local FlyBody primitive, in mm-g-s.

    No joints to a thorax, muscles, springs, commands or prescribed movement.
    Coefficients are native MuJoCo defaults, not FlyBody's hover-fitted values.
    Returns XML for a new isolated model; does not modify the source asset.
    """
    if side not in ('left', 'right'):
        raise ValueError('side must be left or right')
    values = (dt_s, density_g_per_mm3, viscosity_g_per_mm_s, *fluid_coefficients)
    if (len(fluid_coefficients) != 5 or not all(math.isfinite(x) for x in values)
            or dt_s <= 0 or min(values[1:]) < 0):
        raise ValueError('Require positive dt and five finite nonnegative fluid coefficients')
    from flygym import assets_dir
    source = assets_dir / 'model/flybody/fruitfly.xml'
    root = ET.parse(source).getroot()
    wing = root.find(f'.//body[@name="wing_{side}"]')
    fluid = wing.find(f'geom[@name="wing_{side}_fluid"]')
    inertia = wing.find(f'geom[@name="wing_{side}_inertial"]')
    mass = root.find('.//default[@class="wing-inertial"]/geom').get('mass')
    model = ET.Element('mujoco', model='isolated_free_wing_fluid_assay')
    ET.SubElement(model, 'compiler', angle='radian')
    ET.SubElement(model, 'option', timestep=str(dt_s), gravity='0 0 0',
                  density=str(density_g_per_mm3), viscosity=str(viscosity_g_per_mm_s),
                  integrator='implicitfast')
    body = ET.SubElement(ET.SubElement(model, 'worldbody'), 'body', name='wing')
    ET.SubElement(body, 'freejoint')
    for name, geom, kind, geom_mass in [('inertia', inertia, 'box', mass),
                                         ('air', fluid, 'ellipsoid', '0')]:
        attrs = dict(name=name, type=kind, mass=geom_mass, contype='0', conaffinity='0')
        for key in ('pos', 'size'):
            attrs[key] = ' '.join(str(float(x) * 10) for x in geom.get(key).split())
        attrs['quat'] = geom.get('quat')
        if name == 'air':
            attrs.update(fluidshape='ellipsoid', fluidcoef=' '.join(map(str, fluid_coefficients)))
        ET.SubElement(body, 'geom', **attrs)
    return ET.tostring(model, encoding='unicode')


def reduced_thorax_xml(*, dt_s=1e-5, geometry_scale=1.0,
                       hinge_stiffness=0.1, hinge_damping=0.0001,
                       clamp_notum=False):
    """Physical hypothesis in mm-g-s, not segmented Drosophila joint geometry.

    Four articulated bars approximate sagittal scutal compliance. DLM spans its
    AP diagonal; DVM spans sternum-to-notum. A pin-connected ax1 link joins the
    notum to the medial arm of ax2, which pivots on the pleural wing process.
    i1/i2 pull ax1 through native muscle/tendon actuators. See report for the
    published topology, dimensional scale and every unmeasured assumption.
    """
    if (not all(math.isfinite(x) for x in
                (dt_s, geometry_scale, hinge_stiffness, hinge_damping))
            or min(dt_s, geometry_scale) <= 0 or dt_s > 1e-5
            or min(hinge_stiffness, hinge_damping) < 0
            or type(clamp_notum) is not bool):
        raise ValueError('Require 0 < dt <= 10 us, positive scale, nonnegative compliance and boolean clamp')
    s = geometry_scale
    def xyz(*coords):
        return ' '.join(str(x * s) for x in coords)
    root = ET.Element('mujoco', model='hypothesized_thorax_axillary_linkage')
    ET.SubElement(root, 'compiler', angle='radian')
    option = ET.SubElement(root, 'option', timestep=str(dt_s), gravity='0 0 0',
        density='1.28e-6', viscosity='1.85e-5', integrator='implicitfast',
        iterations='100', tolerance='1e-12')
    ET.SubElement(option, 'flag', energy='enable')
    default = ET.SubElement(root, 'default')
    ET.SubElement(default, 'joint', damping=str(hinge_damping),
                  stiffness=str(hinge_stiffness))
    ET.SubElement(default, 'geom', contype='0', conaffinity='0')
    ET.SubElement(default, 'site', size=str(.008 * s))
    world = ET.SubElement(root, 'worldbody')
    ET.SubElement(world, 'site', name='sternum', pos='0 0 0')
    tendon = ET.SubElement(root, 'tendon')
    actuator = ET.SubElement(root, 'actuator')
    equality = ET.SubElement(root, 'equality')
    def connect(a, b):
        ET.SubElement(equality, 'connect', site1=a, site2=b,
                      solref='.00002 1', solimp='.9999 .9999 .0001')
    def fiber(name, origin, insertion):
        t = ET.SubElement(tendon, 'spatial', name=name, width=str(.008*s))
        ET.SubElement(t, 'site', site=origin)
        ET.SubElement(t, 'site', site=insertion)
    # ponytail: symmetric rhombus approximates dome deformation; replace with
    # registered scutum/scutellum surfaces for independent plate modes and folding.
    for name, sign in (('anterior', -1), ('posterior', 1)):
        lower = ET.SubElement(world, 'body', name=name)
        ET.SubElement(lower, 'joint', name=name+'_flexure', axis='0 1 0')
        ET.SubElement(lower, 'geom', type='capsule', size=str(.012*s),
                      fromto=xyz(0, 0, 0, sign*.45, 0, .325), mass=str(2e-6*s**3))
        ET.SubElement(lower, 'site', name='DLM_'+name, pos=xyz(sign*.45, 0, .325))
        upper = ET.SubElement(lower, 'body', name=name+'_scutum', pos=xyz(sign*.45, 0, .325))
        ET.SubElement(upper, 'joint', name=name+'_scutal_flexure', axis='0 1 0')
        ET.SubElement(upper, 'geom', type='capsule', size=str(.012*s),
                      fromto=xyz(0, 0, 0, -sign*.45, 0, .325), mass=str(2e-6*s**3))
        ET.SubElement(upper, 'site', name=name+'_notum_contact', pos=xyz(-sign*.45, 0, .325))
        connect(name+'_notum_contact', 'notum_contact')
    notum = ET.SubElement(world, 'body', name='notum', pos=xyz(0, 0, .65))
    ET.SubElement(notum, 'joint', name='notum_heave', type='slide', axis='0 0 1',
                  stiffness='0', damping='0')
    ET.SubElement(notum, 'geom', type='box', size=xyz(.15, .25, .01), mass=str(1e-5*s**3))
    ET.SubElement(notum, 'site', name='notum_contact')
    fiber('DLM', 'DLM_anterior', 'DLM_posterior')
    fiber('DVM', 'sternum', 'notum_contact')
    for name in ('DLM', 'DVM'):
        ET.SubElement(actuator, 'motor', name=name, tendon=name, gear='-1',
                      ctrllimited='true', ctrlrange='0 10000')
    # Inboard notal/ax1 connection and outboard PWP fulcrum: geometry, not gains.
    ax1 = ET.SubElement(notum, 'body', name='ax1', pos=xyz(.1, .25, .05))
    ET.SubElement(ax1, 'joint', name='notal_ax1_flexure', axis='1 0 0')
    ET.SubElement(ax1, 'geom', type='capsule', size=str(.01*s),
                  fromto=xyz(0, 0, 0, 0, .1, -.05), mass=str(5e-8*s**3))
    ET.SubElement(ax1, 'site', name='ax1_distal', pos=xyz(0, .1, -.05))
    ET.SubElement(ax1, 'site', name='ax1_muscle_insertion', pos=xyz(0, .07, -.035))
    wing = ET.SubElement(world, 'body', name='ax2_wing', pos=xyz(.1, .45, .65))
    ET.SubElement(wing, 'joint', name='PWP_ax2_flexure', axis='1 0 0')
    ET.SubElement(wing, 'geom', type='capsule', size=str(.01*s),
                  fromto=xyz(0, -.1, 0, 0, 0, 0), mass=str(5e-8*s**3))
    ET.SubElement(wing, 'site', name='ax2_medial', pos=xyz(0, -.1, 0))
    ET.SubElement(wing, 'site', name='wing_tip', pos=xyz(0, 2.28, 0))
    ET.SubElement(wing, 'geom', type='box', size=xyz(.551, 1.14, .005),
                  pos=xyz(0, 1.14, 0), mass=str(8e-6*s**3))
    ET.SubElement(wing, 'geom', type='ellipsoid', size=xyz(.551, 1.14, .005),
                  pos=xyz(0, 1.14, 0), mass='0', fluidshape='ellipsoid',
                  fluidcoef='.5 .25 1.5 1 1', rgba='.5 .7 1 .3')
    connect('ax1_distal', 'ax2_medial')
    # 2% PCA end-cap differences from Lindsay's calibrated segmented muscles.
    # Estimated orientation: image x -> AP, image y -> -DV, stack z -> lateral.
    # Translate both distal ends to ax1 and extend the same axis by 30 um for tendon.
    for name, axis in (('i1', (-.21534, .03024, -.18078)),
                       ('i2', (.01620, .02335, -.25104))):
        fiber_length = math.sqrt(sum(x*x for x in axis))
        origin = tuple(p + (1+.03/fiber_length)*v for p, v in zip((.1, .32, .665), axis))
        ET.SubElement(world, 'site', name=name+'_origin', pos=xyz(*origin))
        fiber(name, name+'_origin', 'ax1_muscle_insertion')
        slack, optimal = .03*s, fiber_length*s
        # Reference length is physical fiber/tendon normalization, not an angle command.
        ET.SubElement(actuator, 'muscle', name=name, tendon=name,
                      force=str(2.8*s*s), timeconst='.001 .004',
                      lengthrange=f'{slack+.25*optimal} {slack+1.25*optimal}',
                      range='.25 1.25', lmin='.5', lmax='1.6', vmax='10',
                      fpmax='1.3', fvmax='1.2', ctrlrange='0 1')
    if clamp_notum:
        ET.SubElement(equality, 'joint', joint1='notum_heave',
                      polycoef='0 0 0 0 0', solref='.00002 1', solimp='.9999 .9999 .0001')
    return ET.tostring(root, encoding='unicode')


class ReducedThorax:
    """Unilateral mechanical hypothesis driven only by supplied muscle spikes.

    No MaleCNS IDs are automatically routed. DLM/DVM are representative fibers,
    not a pooled whole-muscle drive or a complete motor-unit allocation.
    """

    def __init__(self, **fixture_options):
        import mujoco
        self.model = mujoco.MjModel.from_xml_string(reduced_thorax_xml(**fixture_options))
        self.data = mujoco.MjData(self.model)
        mujoco.mj_forward(self.model, self.data)
        dt, scale = self.model.opt.timestep, fixture_options.get('geometry_scale', 1.0)
        self.ifms = {name: StretchActivatedMuscle(dt, replace(IFMParameters(),
            reference_length_mm=float(self.data.tendon(name).length[0]),
            area_mm2=.01*scale**2, passive_prestress_pa=0.0)) for name in ('DLM', 'DVM')}
        self.steering_nmjs = {name: NeuromuscularJunction(dt, dict(delay_s=.001,
            tau_exc_s=.002, tau_recovery_s=.1, spike_gain=.2, depression=.2))
            for name in ('i1', 'i2')}
        self.forces = {}

    def step(self, spikes=None, *, release_block=False):
        import mujoco
        spikes = {} if spikes is None else spikes
        if (not isinstance(spikes, dict) or set(spikes) - {'DLM', 'DVM', 'i1', 'i2'}
                or any(type(v) not in (bool, int) or v not in (0, 1) for v in spikes.values())
                or type(release_block) is not bool):
            raise ValueError('Only binary muscle spike events and a boolean release block are accepted')
        # Refresh lengths at the start of this force interval, after the last integration.
        mujoco.mj_forward(self.model, self.data)
        for name, muscle in self.ifms.items():
            result = muscle.advance(float(self.data.tendon(name).length[0]),
                                    spikes.get(name, False), release_block=release_block)
            self.forces[name] = result
            self.data.actuator(name).ctrl[0] = result['tension_uN']
        for name, nmj in self.steering_nmjs.items():
            self.data.actuator(name).ctrl[0] = nmj.advance(
                spikes.get(name, False), release_block=release_block)
        mujoco.mj_step(self.model, self.data)
