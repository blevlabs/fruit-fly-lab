"""One end-to-end check of the real sensory-only CUDA arena; no attraction criterion."""
import json
from pathlib import Path

import numpy as np
from arena import check_arena, default_sources, source_at_mouth
from body import make_body, reset_body
from transport import Backend


def main():
    check_arena()
    backend = Backend()
    sim, fly, controller = make_body()
    reset_body(sim, fly, controller)
    mouth = source_at_mouth(sim, 0)
    command = dict(stimulus_hz=[0, 0], sugar_hz=0, bitter_hz=0,
                   paused=False, reset=0, manual_mode=False,
                   arena_enabled=True, sources=default_sources(False))
    try:
        for _ in range(5):
            quiet = backend.update(command)
        assert quiet['total_spikes'] == 0 and quiet['muscle']['active_tension_uN'] == 0
        try:
            backend.update(dict(command, stimulus_hz=[100, 100]))
        except ValueError:
            pass
        else:
            raise AssertionError('Unapproved direct walking stimulation was accepted')
        command.update(reset=1, paused=True, sources=default_sources())
        far = backend.update(command)
        assert max(far['sensed']['odor_hz']) > 0 and far['sensed']['sugar_hz'] == 0
        source = command['sources'][0]
        source['taste'] = 'bitter'
        changed = backend.update(command)
        assert changed['sensed']['odor_hz'] == far['sensed']['odor_hz']
        assert changed['sensed']['bitter_hz'] == 0, 'Taste activated without contact'
        command['paused'] = False
        for _ in range(30):
            odor = backend.update(command)
        assert max(odor['odor_hz']) > 0 and odor['manual_mode'] is False
        assert odor['stimulus_hz'] == [0, 0]
        assert backend.info['motor_scope'] == 'tethered right MN9-M9'
        # Record motion without demanding an approach, turn, or any other behavior.
        command.update(reset=2, paused=True)
        source.update(x=float(mouth[0]), y=float(mouth[1]), odor=0, taste='sweet')
        contact = backend.update(command)
        assert contact['sensed']['contacts'] == [0] and contact['sugar_hz'] == 200
        command['paused'] = False
        sweet_frames = [backend.update(command) for _ in range(30)]
        object_sweet = sweet_frames[-1]
        assert sum(object_sweet['mn9_spikes']) > 0
        assert max(f['muscle']['active_tension_uN'] for f in sweet_frames) > 0
        source['taste'] = 'bitter'
        command.update(reset=3, paused=True)
        bitter = backend.update(command)
        assert bitter['bitter_hz'] == 200 and bitter['sugar_hz'] == 0
        command['paused'] = False
        for _ in range(30):
            object_bitter = backend.update(command)
        # Neural and physical outcomes are recorded, never forced to a taste-specific angle.
        source.update(taste='neutral', temperature=45)
        command.update(reset=4, paused=True)
        heat = backend.update(command)
        assert max(heat['sensed']['warmth_hz']) > 0
        command['paused'] = False
        for _ in range(10):
            heat = backend.update(command)
        assert max(heat['warmth_hz']) > 0
        assert backend.info['pain']['supported'] is False
        record = dict(backend=backend.info, silent_baseline='pass', contact_gating='pass',
            odor_taste_independence='pass', direct_stimulation_guard='pass',
            odor_trial={k: odor[k] for k in ('time', 'odor_hz', 'p9_hz', 'steering_hz', 'qpos', 'total_spikes')},
            object_taste_trial=dict(sweet_mn9_spikes=object_sweet['mn9_spikes'],
                bitter_mn9_spikes=object_bitter['mn9_spikes'],
                sweet_extension_degrees=float(-np.degrees(object_sweet['proboscis_angle'])),
                bitter_extension_degrees=float(-np.degrees(object_bitter['proboscis_angle'])),
                manual_mode=object_sweet['manual_mode'], sweet_muscle=object_sweet['muscle'],
                bitter_muscle=object_bitter['muscle']),
            temperature_receptor_hz=heat['warmth_hz'],
            note='No attraction/avoidance condition was imposed; pain/nociception remains unmapped.')
        output = (Path(__file__).resolve().parents[1] / 'runtime') / '../runs/muscle-control/arena-check.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2) + '\n')
        print('PASS: receptor activation, contact gating, independent taste, sensory-only guard; '+str(output))
        print('Observed odor-only P9/DNa02 output:', odor['p9_hz'], odor['steering_hz'])
    finally:
        sim.close()
        backend.close()


if __name__ == '__main__':
    main()
