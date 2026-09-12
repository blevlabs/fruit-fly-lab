"""Physical sources and sensory transduction. This module never chooses behavior."""
import math

import mujoco
import numpy as np

SOURCE_COUNT = 2
SOURCE_RADIUS_MM = 0.7
SOURCE_Z_MM = 0.35
ODOR_SIGMA_MM = 5.0
HEAT_SIGMA_MM = 2.0
CONTACT_MARGIN_MM = 0.02
AMBIENT_C = 22.0


def default_sources(enabled=True):
        return [dict(enabled=enabled and i == 0, x=6.0 if i == 0 else -6.0, y=0.0,
                 odor=1.0, taste='sweet' if i == 0 else 'bitter', temperature=AMBIENT_C, liquid=True)
            for i in range(SOURCE_COUNT)]


def validate_sources(sources):
    if not isinstance(sources, list) or len(sources) != SOURCE_COUNT:
        raise ValueError(f'Expected {SOURCE_COUNT} source objects')
    result = []
    for source in sources:
        if not isinstance(source, dict) or type(source.get('enabled')) is not bool:
            raise ValueError('Source enabled must be boolean')
        x, y, odor, temperature = [float(source[k]) for k in ('x', 'y', 'odor', 'temperature')]
        if not all(map(math.isfinite, (x, y, odor, temperature))):
            raise ValueError('Source values must be finite')
        if abs(x) > 100 or abs(y) > 100 or not 0 <= odor <= 1 or not 22 <= temperature <= 45:
            raise ValueError('Source position, odor, or temperature is out of range')
        if source.get('taste') not in ('neutral', 'sweet', 'bitter'):
            raise ValueError('Unknown taste')
        if type(source.get('liquid', True)) is not bool:
            raise ValueError('Source liquid-surface flag must be boolean')
        result.append(dict(enabled=source['enabled'], x=x, y=y, odor=odor,
                           temperature=temperature, taste=source['taste'], liquid=source.get('liquid', True)))
    return result


def add_sources(world, *, register_as_ground=True):
    for i in range(SOURCE_COUNT):
        body = world.mjcf_root.worldbody.add_body(
            name=f'source_{i}', mocap=True, pos=(999, 999, SOURCE_Z_MM))
        food = body.add_geom(name=f'food_{i}', type=mujoco.mjtGeom.mjGEOM_SPHERE,
            size=(SOURCE_RADIUS_MM, 0, 0), rgba=(0.5, 0.8, 0.2, 0), contype=0, conaffinity=0)
        body.add_geom(name=f'odor_halo_{i}', type=mujoco.mjtGeom.mjGEOM_CYLINDER,
            size=(ODOR_SIGMA_MM, 0.004, 0), pos=(0, 0, -SOURCE_Z_MM + 0.008),
            group=5,
            rgba=(0.1, 0.55, 0.95, 0), contype=0, conaffinity=0)
        if register_as_ground:
            world.ground_geoms.append(food)


def apply_sources(sim, sources):
    colors = {'neutral': (0.65, 0.65, 0.65), 'sweet': (0.65, 0.85, 0.15),
              'bitter': (0.65, 0.2, 0.7)}
    for i, source in enumerate(sources):
        mocap = sim.mj_model.body(f'source_{i}').mocapid[0]
        sim.mj_data.mocap_pos[mocap] = ((source['x'], source['y'], SOURCE_Z_MM)
            if source['enabled'] else (999, 999, SOURCE_Z_MM))
        sim.mj_model.geom(f'food_{i}').rgba[:] = (*colors[source['taste']], float(source['enabled']))
        if hasattr(sim, 'source_contact_masks'):
            food = sim.mj_model.geom(f'food_{i}')
            food.contype, food.conaffinity = sim.source_contact_masks if source['enabled'] else (0, 0)
            # MuJoCo caches aggregate body masks for broad-phase collision.
            # This source body contains only the food collider and a non-colliding halo.
            source_body = sim.mj_model.geom_bodyid[food.id]
            sim.mj_model.body_contype[source_body] = food.contype[0]
            sim.mj_model.body_conaffinity[source_body] = food.conaffinity[0]
        sim.mj_model.geom(f'odor_halo_{i}').rgba[3] = 0.07 * source['odor'] if source['enabled'] else 0
    mujoco.mj_forward(sim.mj_model, sim.mj_data)


def fields_at(positions, sources):
    """An explicitly approximate static plume, sampled at sensor positions in mm."""
    odor = np.zeros(len(positions))
    temperature = np.full(len(positions), AMBIENT_C)
    for source in sources:
        if not source['enabled']:
            continue
        d2 = np.sum((positions - (source['x'], source['y'], SOURCE_Z_MM)) ** 2, axis=1)
        odor += source['odor'] * np.exp(-d2 / (2 * ODOR_SIGMA_MM ** 2))
        temperature = np.maximum(temperature, AMBIENT_C + (source['temperature'] - AMBIENT_C)
                                  * np.exp(-d2 / (2 * HEAT_SIGMA_MM ** 2)))
    return np.clip(odor * 200, 0, 200), temperature


def mouth_geometries(model):
    """Resolved labella when present; original coarse assay geometry otherwise."""
    labella = {side: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM,
        f'fly/proboscis_labellum_{name}') for side, name in (('L', 'left'), ('R', 'right'))}
    if all(value >= 0 for value in labella.values()):
        return labella
    if any(value >= 0 for value in labella.values()):
        raise ValueError('Only one member of the paired labellar geometry exists')
    coarse = model.geom('fly/c_haustellum').id
    return {'L': coarse, 'R': coarse}


def sample_contact_taste(sim, sources):
    tastes = {'sweet': [0.0, 0.0], 'bitter': [0.0, 0.0]}
    contacts = {'L': [], 'R': []}
    mouths = mouth_geometries(sim.mj_model)
    for i, source in enumerate(sources):
        if not source['enabled']:
            continue
        for index, (side, mouth) in enumerate(mouths.items()):
            distance = mujoco.mj_geomDistance(sim.mj_model, sim.mj_data,
                sim.mj_model.geom(f'food_{i}').id, mouth, 0.05, np.zeros(6))
            if distance <= CONTACT_MARGIN_MM:
                contacts[side].append(i)
                if source['taste'] in tastes:
                    tastes[source['taste']][index] = 200.0
    touched = sorted(set(contacts['L'] + contacts['R']))
    return dict(sugar_hz=max(tastes['sweet']), bitter_hz=max(tastes['bitter']),
                sugar_hz_by_side=tastes['sweet'], bitter_hz_by_side=tastes['bitter'],
                contacts=touched, labellar_contacts=contacts,
                wet_contacts=[i for i in touched if sources[i].get('liquid', True)],
                taste_contact_geometry='bilateral_labella' if len(set(mouths.values())) == 2 else 'coarse_haustellum')


def sample_sources(sim, sources):
    antennae = np.array([sim.mj_data.body(f'fly/{side}_funiculus').xpos
                         for side in ('l', 'r')])
    odor, temperature = fields_at(antennae, sources)
    return dict(odor_hz=odor.tolist(), temperature_c=temperature.tolist(),
                warmth_hz=(np.clip((temperature - 30) / 10, 0, 1) * 200).tolist(),
                **sample_contact_taste(sim, sources))


def source_at_mouth(sim, index):
    """Place a sphere at the mouth surface, rather than embedding it in the fly."""
    if type(index) is not int or not 0 <= index < SOURCE_COUNT:
        raise ValueError('Invalid source index')
    model, data = sim.mj_model, sim.mj_data
    mocap = model.body(f'source_{index}').mocapid[0]
    original = data.mocap_pos[mocap].copy()
    mouths = set(mouth_geometries(model).values())
    x, y, _ = np.mean([data.geom_xpos[mouth] for mouth in mouths], axis=0)
    lo, hi = float(x), float(x + 2 * SOURCE_RADIUS_MM + 1)
    try:
        for _ in range(35):
            mid = (lo + hi) / 2
            data.mocap_pos[mocap] = (mid, y, SOURCE_Z_MM)
            mujoco.mj_forward(model, data)
            distance = min(mujoco.mj_geomDistance(model, data, model.geom(f'food_{index}').id,
                                                  mouth, 10, np.zeros(6)) for mouth in mouths)
            if distance < CONTACT_MARGIN_MM / 2:
                lo = mid
            else:
                hi = mid
        if lo == x:
            raise ValueError('Mouth is outside the source height; place the source manually')
        return np.array([(lo + hi) / 2, y])
    finally:
        data.mocap_pos[mocap] = original
        mujoco.mj_forward(model, data)


def motor_drive(p9_hz, steering_hz, gain_hz):
    """Calibrated DN-to-leg interface; accepts no source position or sensory value."""
    bias = np.clip((steering_hz[0] - steering_hz[1]) / gain_hz, -1, 1)
    # Steering changes stride balance; it must not invent locomotor drive.
    return np.clip(np.asarray(p9_hz) / gain_hz * np.array([1 - bias, 1 + bias]), 0, 1.5)


def check_arena():
    sources = default_sources()
    sensors = np.array([[0, 0, 1], [0, 0.2, 1]])
    near, _ = fields_at(sensors, sources)
    sources[0]['x'] = 40
    far, _ = fields_at(sensors, sources)
    assert np.all(near > far)
    before = fields_at(sensors, sources)[0]
    sources[0]['taste'] = 'bitter'
    assert np.array_equal(before, fields_at(sensors, sources)[0]), 'Taste changed odor'
    assert np.array_equal(motor_drive([0, 0], [0, 0], 100), [0, 0])
    assert np.array_equal(motor_drive([0, 0], [100, 0], 100), [0, 0]), 'Steering invented walking'
    assert np.array_equal(motor_drive([0, 0], [0, 100], 100), [0, 0]), 'Steering invented walking'
    assert np.array_equal(motor_drive([100, 100], [20, 20], 100), [1, 1])
    try:
        validate_sources([dict(sources[0], x=float('nan')), sources[1]])
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid source accepted')


if __name__ == '__main__':
    check_arena()
    print('Sensory field and motor-isolation checks passed')
