"""Isolated mechanical input checks, not a walking controller or success score."""
import copy
import json
from pathlib import Path

import mujoco as mj
import numpy as np

from cns_body import make_body
from cns_proprio import LIMBS, Proprioception, population_rates


def main():
    mapping = json.loads(((Path(__file__).resolve().parents[1] / 'runtime')/'neural-motor/malecns-sensory-map.json').read_text())
    sense = Proprioception(mapping)
    sim, _, _ = make_body(tethered=True)
    try:
        assert len(sense.ids) == 291
        assert {x['bodyId'] for x in sense.unresolved} == {906066, 933699}
        q0 = sim.mj_data.qpos.copy()
        joint = sim.mj_model.joint('fly/lf_trochanterfemur-lf_tibia-pitch')
        adr = int(joint.qposadr[0])

        def probe(offset):
            sim.mj_data.qpos[:] = q0
            sim.mj_data.time = 0
            mj.mj_forward(sim.mj_model, sim.mj_data)
            sense.reset()
            baseline, before = sense.observe(sim)
            # An externally rotated tibia is a bench stimulus, never runtime motion.
            sim.mj_data.qpos[adr] += offset
            sim.mj_data.time = .001
            mj.mj_forward(sim.mj_model, sim.mj_data)
            result, observation = sense.observe(sim)
            repeated, _ = sense.observe(sim)
            assert result == repeated, 'Repeated observation advanced the sensory filter'
            for binding in sense.bindings:
                if binding['limb'] != 'lf':
                    assert result[binding['bodyId']] == baseline[binding['bodyId']], 'Tibia signal leaked to another leg'
            assert observation['femur_tibia_velocity_rad_s'][0] != 0
            return result, before, observation

        flex, before, f = probe(.2)
        extend, _, e = probe(-.2)
        assert f['femur_tibia_angle_rad'][0] < before['femur_tibia_angle_rad'][0] < e['femur_tibia_angle_rad'][0]
        for binding in sense.bindings:
            if binding['limb'] != 'lf' or binding['kind'] == 'claw':
                continue
            key = binding['bodyId']
            if binding['kind'] == 'club':
                assert flex[key] > 0 and extend[key] > 0
            elif binding['polarity'] == 'flexion':
                assert flex[key] > 0 and extend[key] == 0
            else:
                assert extend[key] > 0 and flex[key] == 0
        # Published population features: tonic extremes, quiet midpoint, motion
        # channels quiet at rest. Polarity names remain hypotheses in metadata.
        angles = np.deg2rad([18., 90., 180.])
        r = population_rates(angles, np.zeros(3), sense.params)
        assert r['claw','flexion'].tolist() == [200, 0, 0]
        assert r['claw','extension'].tolist() == [0, 0, 200]
        assert not r['club','both'].any() and not r['hook','flexion'].any()
        repeat, _, _ = probe(.2)
        assert repeat == flex
        for bad in [dict(sense.params, movement_scale_rad_s=float('nan')),
                    dict(sense.params, position_midpoint_rad=0)]:
            try: population_rates(angles, np.zeros(3), bad)
            except ValueError: pass
            else: raise AssertionError('Invalid physiology accepted')
        # Record sensitivity without selecting whichever hypothesis moves the fly.
        sensitivity = {}
        for factor in (.5, 2.):
            p = copy.deepcopy(sense.params); p['movement_scale_rad_s'] *= factor
            sensitivity[str(factor)] = float(population_rates(np.array([np.pi/2]), np.array([1.]), p)['club','both'][0])
        original = copy.deepcopy(sense.bindings)
        for binding in sense.bindings:
            if binding['kind'] != 'club':
                binding['polarity'] = 'extension' if binding['polarity'] == 'flexion' else 'flexion'
        alternative, _, _ = probe(.2)
        polarity_changes = sum(alternative[i] != flex[i] for i in sense.ids)
        assert polarity_changes > 0
        assert all(alternative[b['bodyId']] == flex[b['bodyId']] for b in sense.bindings if b['kind'] == 'club')
        sense.bindings = original  # No choice between hypotheses is made using motor behavior.
        receipt = dict(status='PASS: physical FeCO input isolation, timing and reset; not biological validation',
            connected_neurons=len(sense.ids), by_limb=sense.coverage['by_limb'], by_kind=sense.coverage['by_kind'],
            femur_tibia_angle_before_rad=before['femur_tibia_angle_rad'][0],
            flexion_angle_rad=f['femur_tibia_angle_rad'][0], extension_angle_rad=e['femur_tibia_angle_rad'][0],
            movement_scale_sensitivity_hz=sensitivity, polarity_status=sense.params['polarity_status'])
        receipt['polarity_reversal_changed_input_neurons'] = polarity_changes
        receipt['polarity_not_selected_by_behavior'] = True
        path = (Path(__file__).resolve().parents[1] / 'runtime')/'outputs/cns/proprio-check.json';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
    finally:
        sim.close()


if __name__ == '__main__':
    main()
