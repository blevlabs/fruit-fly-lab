"""Physical antennal temperature -> opponent, adapting thermoreceptor inputs.

The phasic/tonic distinction follows adult receptor recordings; numerical time
constants, baseline firing and gain are explicit uncalibrated estimates.
"""
import json
from pathlib import Path

import numpy as np

from arena import AMBIENT_C, fields_at


class Thermoreception:
    def __init__(self, mapping):
        self.params = json.loads((Path(__file__).parent/'cns-model.json').read_text())['thermoreception']
        self.groups = {g['id']: g for g in mapping['input_groups'] if g['id'] in ('TRN_VP2', 'TRN_VP3a')}
        if len(self.groups) != 2:
            raise ValueError('The primary heating/aristal-cooling correspondences are required')
        self.ids = {i for group in self.groups.values() for side in ('L', 'R')
                    for i in group['body_ids_by_root_side'].get(side, [])}
        p = self.params
        if (not np.isfinite([p[k] for k in ('baseline_rate_hz', 'gain_hz_per_c', 'maximum_rate_hz',
                'peripheral_time_constant_s', 'adaptation_time_constant_s')]).all()
                or not 0 < p['baseline_rate_hz'] < p['maximum_rate_hz'] <= 500
                or min(p['gain_hz_per_c'], p['peripheral_time_constant_s'], p['adaptation_time_constant_s']) <= 0):
            raise ValueError('Invalid thermoreceptor parameters')
        self.coverage = dict(connected_neurons=len(self.ids), groups=list(self.groups), parameters=p,
            identity='Published VP2 heating and VP3a aristal cooling types; VP3b remains separate/unmapped',
            physical_sample='Current left/right arista body positions, with estimated peripheral thermal exchange')
        self.reset()

    def reset(self):
        self.time = 0.0
        self.temperature = np.full(2, AMBIENT_C)
        self.adapted_temperature = self.temperature.copy()

    def advance(self, time_s, field_temperature_c):
        values = np.asarray(field_temperature_c, dtype=float)
        if values.shape != (2,) or not np.isfinite(values).all() or not np.isfinite(time_s) or time_s < self.time-1e-10:
            raise ValueError('Expected finite paired temperature and a monotonic physical clock')
        dt, p = max(0.0, time_s-self.time), self.params
        self.temperature += -np.expm1(-dt/p['peripheral_time_constant_s'])*(values-self.temperature)
        self.adapted_temperature += -np.expm1(-dt/p['adaptation_time_constant_s'])*(self.temperature-self.adapted_temperature)
        change = self.temperature-self.adapted_temperature
        warming = np.clip(p['baseline_rate_hz'] + p['gain_hz_per_c']*change, 0, p['maximum_rate_hz'])
        cooling = np.clip(p['baseline_rate_hz'] - p['gain_hz_per_c']*change, 0, p['maximum_rate_hz'])
        rates = {}
        for name, values in (('TRN_VP2', warming), ('TRN_VP3a', cooling)):
            for side, value in zip(('L', 'R'), values):
                rates.update({i: float(value) for i in self.groups[name]['body_ids_by_root_side'].get(side, [])})
        self.time = float(time_s)
        return rates, dict(warmth_hz=warming.tolist(), cooling_hz=cooling.tolist(),
            thermoreceptor_temperature_c=self.temperature.tolist(), thermal_adaptation_c=self.adapted_temperature.tolist())

    def observe(self, sim, sources):
        positions = np.array([sim.mj_data.body(f'fly/{side}_arista').xpos for side in ('l', 'r')])
        _, temperature = fields_at(positions, sources)
        return self.advance(sim.time, temperature)


def check():
    mapping = json.loads((Path(__file__).parent/'neural-motor/malecns-sensory-map.json').read_text())
    sense = Thermoreception(mapping)
    assert len(sense.ids) == 13
    results = []
    for _ in range(2):
        sense.reset()
        baseline, _ = sense.advance(0, [22, 22])
        for tick in range(1, 11):
            warm, w = sense.advance(tick*.01, [27, 22])
        assert w['warmth_hz'][0] > 30 and w['cooling_hz'][0] < 30
        assert w['warmth_hz'][1] == w['cooling_hz'][1] == 30
        assert warm == sense.advance(.1, [27, 22])[0], 'Paused read advanced thermal time'
        for tick in range(11, 1001):
            _, adapted = sense.advance(tick*.01, [27, 22])
        assert abs(adapted['warmth_hz'][0]-30) < 1
        for tick in range(1001, 1011):
            cold, c = sense.advance(tick*.01, [22, 22])
        assert c['cooling_hz'][0] > 30 and c['warmth_hz'][0] < 30
        results.append((baseline, warm, cold, sense.temperature.copy()))
    assert results[0][:3] == results[1][:3] and np.array_equal(results[0][3], results[1][3])
    print('PASS: opponent phasic thermal responses, adaptation, side isolation, pause and reset; constants remain estimates')


if __name__ == '__main__':
    check()
