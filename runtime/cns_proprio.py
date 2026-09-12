"""Physical femur-tibia observations to identified FeCO sensory populations.

Neuron/type/limb identities use the released annotations. Subtype polarity is
an explicit circuit-consistent hypothesis; population tuning is approximate.
No motor target, desired joint angle, gait phase or body command enters here.
"""
from collections import Counter
import json
from pathlib import Path

import numpy as np

LIMBS = ('lf', 'rf', 'lm', 'rm', 'lh', 'rh')
LEG_NERVES = {'ProLN': 'f', 'MesoLN': 'm', 'MetaLN': 'h'}
KINDS = {'SNpp50': 'claw', 'SNpp51': 'claw', 'SNpp39': 'hook', 'SNpp41': 'hook',
         'SNpp40': 'club', 'SNpp47': 'club', 'SNpp56': 'club', 'SNpp57': 'club', 'SNpp60': 'club'}


def population_rates(angle, velocity, parameters):
    """Approximate class responses; angle 0 is folded and pi is extended."""
    angle, velocity = np.asarray(angle), np.asarray(velocity)
    if (angle.shape != velocity.shape or not np.isfinite(angle).all()
            or not np.isfinite(velocity).all() or np.any(angle < 0) or np.any(angle > np.pi)):
        raise ValueError('Expected finite physical joint angles in [0, pi] and velocities')
    p = parameters
    mid, low, high = [p[k] for k in ('position_midpoint_rad', 'position_flexion_reference_rad', 'position_extension_reference_rad')]
    if (not np.isfinite([low, mid, high, p['maximum_rate_hz'], p['movement_scale_rad_s']]).all()
            or not 0 <= low < mid < high <= np.pi or not 0 < p['maximum_rate_hz'] <= 500 or p['movement_scale_rad_s'] <= 0):
        raise ValueError('Invalid proprioceptive tuning parameters')
    maximum, scale = p['maximum_rate_hz'], p['movement_scale_rad_s']
    return {
        ('claw', 'flexion'): maximum * np.clip((mid-angle)/(mid-low), 0, 1),
        ('claw', 'extension'): maximum * np.clip((angle-mid)/(high-mid), 0, 1),
        ('hook', 'flexion'): maximum * np.tanh(np.maximum(-velocity, 0)/scale),
        ('hook', 'extension'): maximum * np.tanh(np.maximum(velocity, 0)/scale),
        ('club', 'both'): maximum * np.tanh(np.abs(velocity)/scale),
    }


class Proprioception:
    def __init__(self, mapping):
        self.params = json.loads((Path(__file__).parent/'cns-model.json').read_text())['proprioception']
        p = self.params
        if (not np.isfinite(p['velocity_filter_tau_s']) or p['velocity_filter_tau_s'] <= 0
                or set(p['polarity']) != {t for t, k in KINDS.items() if k != 'club'}
                or set(p['polarity'].values()) - {'flexion', 'extension'}):
            raise ValueError('Invalid FeCO transduction hypothesis')
        table = mapping['neurons']
        self.bindings, self.unresolved = [], []
        for raw in table['rows']:
            row = dict(zip(table['columns'], raw))
            if row['type'] not in KINDS:
                continue
            if (row['class'] != 'mechanosensory_proprioceptive'
                    or row['rootSide'] not in ('L', 'R') or row['entryNerve'] not in LEG_NERVES):
                self.unresolved.append(dict(bodyId=row['bodyId'], type=row['type'],
                    reason='Modality or exact FeCO leg-entry nerve/side conflicts with this correspondence'))
                continue
            limb = row['rootSide'].lower() + LEG_NERVES[row['entryNerve']]
            kind = KINDS[row['type']]
            self.bindings.append(dict(bodyId=row['bodyId'], type=row['type'], limb=limb,
                kind=kind, polarity=p['polarity'].get(row['type'], 'both'),
                identity_evidence='MaleCNS exact type, proprioceptive class, rootSide and leg entryNerve',
                polarity_evidence='MANC Fig 59 circuit-consistent hypothesis' if kind != 'club' else 'Published bidirectional motion response'))
        self.ids = {b['bodyId'] for b in self.bindings}
        if len(self.ids) != len(self.bindings):
            raise ValueError('Duplicate proprioceptor IDs')
        self.coverage = dict(connected_neurons=len(self.ids),
            by_limb=dict(Counter(b['limb'] for b in self.bindings)),
            by_kind=dict(Counter(b['kind'] for b in self.bindings)),
            bindings=self.bindings, unresolved=self.unresolved, parameters=self.params,
            missing='Individual tuning, arculum/tendon mechanics, hysteresis, club frequency selectivity, other proprioceptors and skin contact transduction')
        self.reset()

    def reset(self):
        self.last_time = None
        self.last_angles = None
        self.velocity = np.zeros(len(LIMBS))

    @staticmethod
    def angles(sim):
        points = np.array([[sim.mj_data.body(f'fly/{limb}_{segment}').xpos
                            for segment in ('trochanterfemur', 'tibia', 'tarsus1')]
                           for limb in LIMBS])
        proximal, distal = points[:, 0]-points[:, 1], points[:, 2]-points[:, 1]
        if np.any(np.linalg.norm(proximal, axis=1) < 1e-8) or np.any(np.linalg.norm(distal, axis=1) < 1e-8):
            raise ValueError('Degenerate femur/tibia geometry')
        return np.arctan2(np.linalg.norm(np.cross(proximal, distal), axis=1),
                          np.einsum('ij,ij->i', proximal, distal))

    def observe(self, sim):
        angle, now = self.angles(sim), float(sim.time)
        if self.last_time is not None:
            elapsed = now-self.last_time
            if elapsed < -1e-10:
                raise ValueError('Reset the proprioceptive state when the physical clock resets')
            if elapsed > 1e-12:
                raw = (angle-self.last_angles)/elapsed
                self.velocity += (1-np.exp(-elapsed/self.params['velocity_filter_tau_s']))*(raw-self.velocity)
        self.last_angles, self.last_time = angle, now
        values = population_rates(angle, self.velocity, self.params)
        rates = {b['bodyId']: float(values[b['kind'], b['polarity']][LIMBS.index(b['limb'])]) for b in self.bindings}
        return rates, dict(femur_tibia_angle_rad=angle.tolist(),
                           femur_tibia_velocity_rad_s=self.velocity.tolist(), proprioceptor_count=len(rates))
