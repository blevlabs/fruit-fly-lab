"""Isolated CUDA whole-CNS/body check; no natural-behavior success target."""
import json
from pathlib import Path
import sys
import time
import uuid

import numpy as np

from arena import default_sources, source_at_mouth
from cns_body import make_body
from transport import Backend

ROOT = (Path(__file__).resolve().parents[1] / 'runtime')


def main(backend_command=None, output=None):
    started = time.monotonic()
    backend = Backend(mode='cns', command=backend_command)
    controls = dict(paused=True, reset=0, sources=default_sources(False))
    try:
        initial = backend.update(controls)
        quiet = backend.update(dict(controls, paused=False))
        # The illuminated scene and declared tonic visual release are active
        # even without chemical sources. Zero spikes is no longer expected.
        assert quiet['sensed']['odor_hz'] == [0, 0] and quiet['sugar_hz'] == quiet['bitter_hz'] == 0
        paused = backend.update(dict(controls, paused=True))
        for key in ('qpos', 'qvel', 'act', 'ctrl', 'time', 'step'):
            assert paused[key] == quiet[key]
        slot = 'integration_'+uuid.uuid4().hex
        saved = backend.checkpoint('save', slot)
        backend.update(dict(controls, paused=False, steps=1))
        restored = backend.checkpoint('restore', slot)
        assert restored['sha256'] == saved['sha256'] and restored['individual_id'] == saved['individual_id']
        replay = backend.update(dict(controls, paused=True, reset=restored['reset'],
            sources=restored['sources'], release_block=restored['release_block']))
        for key in ('qpos', 'qvel', 'act', 'ctrl', 'time', 'step', 'qfrc_applied',
                    'motor_counts', 'total_spikes', 'total_motor_spikes', 'fluid', 'flight_ifm_activation'):
            assert replay[key] == quiet[key], f'Named checkpoint failed to preserve {key}'
        for invalid in ({'checkpoint':'erase', 'name':slot}, {'checkpoint':'restore', 'name':'missing_'+slot}):
            try:
                backend.update(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError('Invalid checkpoint command accepted')
        backend.process.stdin.write(json.dumps({'padding':'x'*5000})+'\n')
        backend.process.stdin.flush()
        try:
            backend.receive()
        except ValueError as error:
            assert 'Command too large' in str(error)
        else:
            raise AssertionError('Oversized command accepted')
        still_paused = backend.update(dict(controls, paused=True))
        assert still_paused['qpos'] == quiet['qpos'] and still_paused['step'] == quiet['step']
        for bad in ({'stimulus_hz':[100,100]}, {'manual_mode':True}, {'gain_hz':100}, {'steps':0}):
            try:
                backend.update(dict(controls, **bad))
            except ValueError:
                pass
            else:
                raise AssertionError(f'Direct/invalid command accepted: {bad}')
        print('CNS check: pause, named checkpoint, rejected commands and input guards passed', file=sys.stderr, flush=True)
        sources = default_sources()
        sources[0].update(x=3, y=0, taste='neutral', temperature=22, odor=0)
        visible_control = dict(paused=False, reset=10, sources=sources, steps=100)
        for _ in range(30):
            odorless = backend.update(visible_control)
        print('CNS check: odorless visible-source trial complete', file=sys.stderr, flush=True)
        sources[0]['odor'] = 1
        command = dict(paused=False, reset=1, sources=sources, steps=100)
        frames = [backend.update(command) for _ in range(30)]
        odor = frames[-1]
        assert odor['total_spikes'] > 0
        assert odor['total_spikes'] != odorless['total_spikes'], 'Odor did not change neural activity'
        assert np.isfinite(odor['qpos']).all() and np.isfinite(odor['act']).all()
        assert odor['sugar_hz'] == 0
        print('CNS check: odor trial complete', file=sys.stderr, flush=True)
        # A second packet schedule must produce the same neural and physical state.
        command.update(reset=2, steps=25)
        for _ in range(120):
            packet = backend.update(command)
        for key in ('qpos', 'qvel', 'act', 'ctrl', 'qfrc_applied', 'motor_counts', 'total_spikes', 'step', 'flight_ifm_activation', 'fluid'):
            assert packet[key] == odor[key], f'Transport packet changed {key}'
        print('CNS check: exact packet-schedule equality passed', file=sys.stderr, flush=True)
        command.update(reset=3, steps=100, release_block=True)
        blocked_frames = [backend.update(command) for _ in range(30)]
        assert all(not np.any(f['act']) and not np.any(f['flight_ifm_activation'])
                   and f['max_flight_active_force_uN'] == 0 for f in blocked_frames)
        print('CNS check: transmission-block trial passed', file=sys.stderr, flush=True)
        placement, _, _ = make_body()
        try:
            x, y = source_at_mouth(placement, 0)
        finally:
            placement.close()
        taste_trials = {}
        for reset_id, liquid in ((20, True), (21, False)):
            contact_sources = default_sources()
            contact_sources[0].update(x=float(x), y=float(y), odor=0, temperature=22, taste='sweet', liquid=liquid)
            request = dict(paused=True, reset=reset_id, sources=contact_sources, steps=100)
            contact = backend.update(request)
            assert contact['sugar_hz'] == 200 and bool(contact['sensed']['wet_contacts']) == liquid
            request['paused'] = False
            for _ in range(10):
                contact = backend.update(request)
            assert contact['max_fluid_conservation_residual_mm3'] < 1e-12
            if not liquid:
                assert contact['fluid']['net_boundary_volume_mm3']['inlet'] == 0
            indices = {body_id:i for i,body_id in enumerate(backend.info['connected_motor_ids'])}
            taste_trials['liquid' if liquid else 'dry'] = dict(
                simulated_seconds=contact['time'], total_motor_spikes=contact['total_motor_spikes'],
                mn9_spikes={str(body_id):contact['motor_counts'][indices[body_id]] for body_id in (10331,16949)},
                fluid=contact['fluid'], max_conservation_residual_mm3=contact['max_fluid_conservation_residual_mm3'])
        print('CNS check: contact-taste and wet/dry fluid-boundary trials passed', file=sys.stderr, flush=True)
        reset = backend.update(dict(controls, reset=4))
        assert reset['qpos'] == initial['qpos'] and reset['act'] == initial['act']
        assert reset['time'] == 0 and reset['connected_motor_spikes'] == 0
        assert not np.any(reset['flight_ifm_activation']) and not np.any(reset['fluid']['pressure_pa'])
        assert odor['max_fluid_conservation_residual_mm3'] < 1e-12
        receipt = dict(status='PASS: whole-CNS and supported-muscle integration', backend=backend.info,
            pause='pass', reset='pass', direct_drive_rejection='pass',
            named_checkpoint=saved, checkpoint_protocol='exact saved frame; rejected and oversized commands preserve the individual',
            packet_schedule='exact state equality at 25 vs 100 steps', transmission_block='no active muscle drive',
            simulated_seconds=odor['time'], wall_seconds=time.monotonic()-started,
            contact_taste_trials=taste_trials,
            odorless_visible_control={key:odorless[key] for key in ('total_spikes','total_motor_spikes','connected_motor_spikes')},
            odor_trial={key:odor[key] for key in ('total_spikes','total_motor_spikes','connected_motor_spikes',
                'active_muscle_units','thorax_position_mm','max_muscle_tension_uN')},
            initial_thorax_mm=initial['thorax_position_mm'],
            behavior_acceptance='None: no walk, approach, gait, posture or flight target',
            limitations=backend.info['body_coverage']['unimplemented_body'])
        output = ROOT.parent / 'runs/cns' if output is None else Path(output)
        output.mkdir(parents=True, exist_ok=True)
        (output / 'integration-check.json').write_text(json.dumps(receipt,indent=2)+'\n')
        np.savez_compressed(output / 'odor-trajectory.npz',
            time=[f['time'] for f in frames], qpos=[f['qpos'] for f in frames],
            act=[f['act'] for f in frames], tension=[f['muscle_tension_uN'] for f in frames])
        print(json.dumps(receipt,indent=2))
    finally:
        backend.close()


if __name__ == '__main__':
    main()
