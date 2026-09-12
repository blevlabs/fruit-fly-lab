"""Native Mac viewer for a compatible CUDA neural and physical simulation worker."""
import argparse
import copy
import json
from pathlib import Path
import sys
import threading
import time

import mujoco
import mujoco.viewer
import glfw
import numpy as np
from AppKit import (NSEvent, NSEventMaskKeyDown, NSEventMaskKeyUp, NSEventMaskLeftMouseDown,
                    NSEventTypeKeyUp, NSEventTypeLeftMouseDown, NSEventModifierFlagControl,
                    NSEventModifierFlagCommand, NSWindowDidResignKeyNotification)
from Foundation import NSNotificationCenter
from PyObjCTools import AppHelper
from body import make_body
from arena import apply_sources, check_arena, default_sources, source_at_mouth, validate_sources
from arena_ui import ArenaPanel
from transport import Backend

ROOT = Path(__file__).resolve().parent
RUNS = ROOT.parent / 'runs'


def apply_shortcut(controls, code, control):
    if code == glfw.KEY_ESCAPE:
        return True
    if code == glfw.KEY_SPACE or (control and code == glfw.KEY_0):
        controls['paused'] = not controls['paused']
    elif control and code == glfw.KEY_3:
        controls['reset'] += 1
    elif control and code == glfw.KEY_2:
        controls.update(stimulus_hz=[0, 0], sugar_hz=0, bitter_hz=0)
        for source in controls.get('sources', []):
            source['enabled'] = False
    elif control and code in (glfw.KEY_6, glfw.KEY_7):
        if controls.get('manual_mode', False):
            field = 'sugar_hz' if code == glfw.KEY_6 else 'bitter_hz'
            controls[field] = 0 if controls[field] else 200
        else:
            source = controls['sources'][controls.get('selected_source', 0)]
            taste = 'sweet' if code == glfw.KEY_6 else 'bitter'
            source['taste'] = 'neutral' if source['taste'] == taste else taste
    elif control and code == glfw.KEY_8:
        controls['camera'] = 0 if controls.get('camera') == 1 else 1
    elif control and code == glfw.KEY_9:
        controls['camera'] = 2
    elif control and code == glfw.KEY_M:
        controls['muscle_view'] = not controls.get('muscle_view', True)
    return False


def check_shortcuts():
    controls = dict(stimulus_hz=[0, 0], sugar_hz=0, bitter_hz=0, paused=False, reset=0, manual_mode=True)
    apply_shortcut(controls, glfw.KEY_1, False)
    assert controls['stimulus_hz'] == [0, 0], 'Unmodified number triggered a command'
    apply_shortcut(controls, glfw.KEY_1, True)
    assert controls['stimulus_hz'] == [0, 0], 'Direct walking input is disabled'
    for key, field in [(glfw.KEY_6, 'sugar_hz'), (glfw.KEY_7, 'bitter_hz')]:
        apply_shortcut(controls, key, True)
        assert controls[field] == 200
        apply_shortcut(controls, key, True)
        assert controls[field] == 0
    controls.update(sugar_hz=200, bitter_hz=200)
    apply_shortcut(controls, glfw.KEY_2, True)
    assert controls['stimulus_hz'] == [0, 0] and controls['sugar_hz'] == controls['bitter_hz'] == 0
    apply_shortcut(controls, glfw.KEY_3, True)
    apply_shortcut(controls, glfw.KEY_0, True)
    assert controls['reset'] == 1 and controls['paused']
    apply_shortcut(controls, glfw.KEY_8, True)
    assert controls['camera'] == 1
    apply_shortcut(controls, glfw.KEY_8, True)
    assert controls['camera'] == 0
    controls.update(manual_mode=False, sources=default_sources(), selected_source=0)
    apply_shortcut(controls, glfw.KEY_1, True)
    assert controls['stimulus_hz'] == [0, 0], 'Arena enabled direct walking stimulation'
    apply_shortcut(controls, glfw.KEY_7, True)
    assert controls['sources'][0]['taste'] == 'bitter' and controls['bitter_hz'] == 0
    apply_shortcut(controls, glfw.KEY_M, True)
    assert controls['muscle_view'] is False
    apply_shortcut(controls, glfw.KEY_M, True)
    assert controls['muscle_view'] is True


def show_muscle_path(model, enabled, original_alpha):
    """Rendering only: make obstructing cuticle/appendages translucent."""
    model.geom_rgba[:, 3] = original_alpha
    if enabled:
        for i in range(model.ngeom):
            name = model.geom(i).name
            if name == 'fly/c_head' or name.startswith(('fly/l', 'fly/r')):
                model.geom_rgba[i, 3] = 0.15


def check(backend, controls):
    check_shortcuts()
    check_arena()
    controls.update(manual_mode=True, arena_enabled=False, sources=default_sources(False),
                    paused=True, stimulus_hz=[0, 0], sugar_hz=0, bitter_hz=0, reset=0)
    initial = backend.update(controls)

    def trial(reset, sugar=0, bitter=0, blocked=False, steps=100, total_steps=5000):
        command = dict(controls, reset=reset, sugar_hz=sugar, bitter_hz=bitter,
                       mn9_release_block=blocked, steps=steps, paused=False)
        frames = [backend.update(command) for _ in range(total_steps // steps)]
        return frames[-1], max(f['muscle']['active_tension_uN'] for f in frames)

    quiet, quiet_force = trial(1)
    assert quiet['total_spikes'] == 0 and quiet_force == 0
    sweet, peak_force = trial(2, sugar=200)
    bitter, _ = trial(3, sugar=200, bitter=200)
    blocked, blocked_force = trial(4, sugar=200, blocked=True)
    assert sweet['mn9_spikes'] == blocked['mn9_spikes'] and sum(sweet['mn9_spikes']) > 0
    assert peak_force > 0 and blocked_force == 0 and blocked['muscle']['activation'] == 0
    np.testing.assert_allclose(blocked['qpos'], quiet['qpos'], atol=1e-10)
    assert blocked['muscle']['delivered_spikes'] == 0
    assert sweet['muscle']['received_spikes'] == sum(sweet['mn9_spikes'])
    assert sweet['muscle']['received_spikes'] == sweet['muscle']['delivered_spikes'] + sweet['muscle']['pending_spikes']
    coarse, _ = trial(5, sugar=200, steps=100, total_steps=2000)
    fine, _ = trial(6, sugar=200, steps=25, total_steps=2000)
    for field in ('qpos', 'qvel', 'act', 'ctrl', 'mn9_spikes', 'total_spikes', 'step'):
        assert coarse[field] == fine[field], f'Packet size changed {field}'
    paused = backend.update(dict(controls, reset=6, paused=True))
    assert paused['qpos'] == fine['qpos'] and paused['act'] == fine['act'] and paused['time'] == fine['time']
    for invalid in ({'stimulus_hz': [100, 100]}, {'sugar_hz': -1}, {'steps': 0}, {'feeding_gain_hz': 80},
                    {'manual_mode': False, 'sugar_hz': 100}, {'mn9_release_block': 1}):
        try:
            backend.update(dict(controls, **invalid))
        except ValueError:
            pass
        else:
            raise AssertionError(f'Invalid input accepted: {invalid}')
    reset = backend.update(dict(controls, reset=7, paused=True))
    assert reset['time'] == 0 and reset['muscle']['received_spikes'] == 0 and reset['act'] == [0]
    assert reset['qpos'] == initial['qpos']
    receipt = dict(status='PASS: CUDA neural-to-muscle integration; estimated physiology',
                   backend=backend.info, seconds=sweet['time'], pause='pass', reset='pass',
                   packet_invariance='exact physical and spike state at 25 vs 100 steps',
                   transmission_block='same neural spikes, zero active force',
                   input_validation='pass', sweet_mn9_spikes=sweet['mn9_spikes'],
                   bitter_mn9_spikes=bitter['mn9_spikes'], peak_active_tension_uN=peak_force,
                   sweet_muscle=sweet['muscle'], bitter_muscle=bitter['muscle'],
                   note='Tethered right M9; no angle target, preset gait, or food-response acceptance threshold.')
    output = RUNS / 'muscle-control'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'cuda-check.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS:', json.dumps(receipt))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check the CUDA session without opening a window')
    parser.add_argument('--cns', action='store_true', help='Use the complete MaleCNS graph and supported whole-body muscles (incomplete peripheral coverage)')
    parser.add_argument('--backend-command', help='Explicit command for a compatible CUDA worker; defaults to local Python')
    parser.add_argument('--checkpoint-name', default='current', help='Named individual checkpoint slot')
    parser.add_argument('--restore', action='store_true', help='Restore that individual before opening the viewer; start paused')
    parser.add_argument('--paused', action='store_true', help='Start without advancing the individual')
    parser.add_argument('--controls-file', type=Path, default=RUNS/'arena-controls.json', help='Separate saved scene controls for an isolated native assay')
    args = parser.parse_args()
    if args.cns and args.check:
        sys.path.insert(0, str(ROOT.parent / 'tests'))
        from check_cns import main as check_whole_cns
        check_whole_cns(backend_command=args.backend_command)
        return
    controls = dict(stimulus_hz=[0, 0], sugar_hz=0, bitter_hz=0,
                    steps=1 if args.cns else 100,
                    paused=args.paused or args.restore, reset=0, camera=0 if args.cns else 1, muscle_view=not args.cns, manual_mode=False,
                    arena_enabled=True, sources=default_sources(), selected_source=0, cns_mode=args.cns, release_block=False)
    control_path = args.controls_file
    control_path.parent.mkdir(parents=True, exist_ok=True)
    if control_path.exists() and not args.check:
        saved = json.loads(control_path.read_text())
        controls['sources'] = validate_sources(saved['sources'])
        if saved.get('selected_source') in (0, 1):
            controls['selected_source'] = saved['selected_source']
    lock = threading.Lock()
    quit_requested = threading.Event()
    held_keys = set()
    panel = None

    def key_event(event):
        if event.window() is None or not str(event.window().title()).startswith('MuJoCo'):
            return event
        control = bool(event.modifierFlags() & NSEventModifierFlagControl)
        if event.type() == NSEventTypeLeftMouseDown:
            if control:
                point, size = event.locationInWindow(), event.window().contentView().bounds().size
                with lock:
                    controls['place_source'] = [point.x / size.width, point.y / size.height]
                return None
            return event
        char = str(event.charactersIgnoringModifiers() or '')
        if event.type() == NSEventTypeKeyUp:
            with lock:
                held_keys.discard(char.lower())
            return event
        if not control and not (event.modifierFlags() & NSEventModifierFlagCommand):
            with lock:
                if controls['camera'] == 2 and char.lower() in ('w', 'a', 's', 'd', 'q', 'e'):
                    held_keys.add(char.lower())
                    if not event.isARepeat():
                        controls.setdefault('camera_nudges', []).append(char.lower())
                    return None
        # Cocoa can report control characters (e.g. Tab for Ctrl+I) instead of letters.
        if control and (char.lower() == 'i' or event.keyCode() == 0x22):
            if panel is not None:
                panel.panel.makeKeyAndOrderFront_(None)
            return None
        if control and (char.lower() == 'p' or event.keyCode() == 0x23):
            with lock:
                controls['place_source'] = 'camera'
            return None
        code = {' ': glfw.KEY_SPACE, '\x1b': glfw.KEY_ESCAPE,
                '\uf700': glfw.KEY_UP, '\uf701': glfw.KEY_DOWN}.get(char)
        if control and (char.lower() == 'm' or event.keyCode() == 0x2E):
            code = glfw.KEY_M
        if control and len(char) == 1 and char in '0123456789':
            code = ord(char)
        if code is None:
            return event
        if event.isARepeat() and code not in (glfw.KEY_UP, glfw.KEY_DOWN):
            return None
        with lock:
            if apply_shortcut(controls, code, control):
                quit_requested.set()
        if panel is not None:
            panel.refresh()
        return None  # Consume the shortcut before MuJoCo's geometry/group shortcuts.

    monitor = []
    focus_observer = []
    monitor_ready = threading.Event()

    def install_shortcuts():
        nonlocal panel
        monitor.append(NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskKeyDown | NSEventMaskKeyUp | NSEventMaskLeftMouseDown, key_event))
        def lost_focus(notification):
            with lock:
                held_keys.clear()
        focus_observer.append(NSNotificationCenter.defaultCenter().addObserverForName_object_queue_usingBlock_(
            NSWindowDidResignKeyNotification, None, None, lost_focus))
        panel = ArenaPanel.alloc().init().build(controls, lock)
        monitor_ready.set()

    print('Loading CUDA brain and body physics...', flush=True)
    backend = Backend(mode='cns' if args.cns else 'mn9', command=args.backend_command)
    sim = None
    try:
        if args.restore:
            restored = backend.checkpoint('restore', args.checkpoint_name)
            controls.update(sources=restored['sources'], reset=restored['reset'], paused=True, release_block=restored['release_block'])
        if args.check:
            check(backend, controls)
            return
        if args.cns:
            from cns_body import make_body as make_cns_body
            sim, _, _ = make_cns_body()
        else:
            sim, _, _ = make_body()
        original_alpha = sim.mj_model.geom_rgba[:, 3].copy()
        muscle_view = None
        if (sim.mj_model.nq, sim.mj_model.nv) != (backend.info['nq'], backend.info['nv']):
            raise RuntimeError('Body state dimensions do not match')
        with mujoco.viewer.launch_passive(sim.mj_model, sim.mj_data,
                show_left_ui=False, show_right_ui=False) as viewer:
            AppHelper.callAfter(install_shortcuts)
            if not monitor_ready.wait(5):
                raise RuntimeError('Could not install the Mac window shortcuts')
            with viewer.lock():
                viewer.opt.geomgroup[5] = 1  # UI odor halos; excluded from the fly's optical rays.
                viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
                viewer.cam.lookat[:] = (3, 0, 0.6)
                viewer.cam.distance = 14
                viewer.cam.azimuth, viewer.cam.elevation = 90, -35
            camera = 2
            pick_scene = mujoco.MjvScene(sim.mj_model,
                maxgeom=max(1000, sim.mj_model.ngeom + sim.mj_model.nsite + 2*sim.mj_model.nwrap))
            print('Arena live: Ctrl+click places selected source. Ctrl+I controls. Ctrl+9 free camera; WASD/QE move. No direct stimulation by default.', flush=True)
            previous = time.monotonic()
            status_time = 0
            saved_controls = None
            while viewer.is_running() and not quit_requested.is_set():
                with lock:
                    checkpoint_action = controls.pop('checkpoint_action', None)
                    placement = controls.pop('place_source', None)
                    nudges = controls.pop('camera_nudges', [])
                    keys = set(held_keys)
                    command = copy.deepcopy(controls)
                with viewer.lock():
                    if command['muscle_view'] != muscle_view:
                        muscle_view = command['muscle_view']
                        show_muscle_path(sim.mj_model, muscle_view, original_alpha)
                    if command['camera'] != camera:
                        camera = command['camera']
                        if camera == 2:
                            viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
                            viewer.cam.lookat[:] = sim.mj_data.body('fly/c_thorax').xpos
                            viewer.cam.distance = 14
                            viewer.cam.azimuth, viewer.cam.elevation = 90, -35
                        else:
                            viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
                            viewer.cam.fixedcamid = camera
                    if (camera == 2 and (keys or nudges)) or isinstance(placement, list):
                        mujoco.mjv_updateScene(sim.mj_model, sim.mj_data, viewer.opt, None,
                            viewer.cam, mujoco.mjtCatBit.mjCAT_ALL, pick_scene)
                    if camera == 2 and (keys or nudges):
                        forward = np.array(pick_scene.camera[0].forward)
                        right = np.cross(forward, pick_scene.camera[0].up)
                        motion = (int('w' in keys) - int('s' in keys)) * forward
                        motion += (int('d' in keys) - int('a' in keys)) * right
                        motion += (int('e' in keys) - int('q' in keys)) * np.array([0, 0, 1])
                        viewer.cam.lookat[:] += motion * 8 * min(time.monotonic() - previous, 0.1)
                        for nudge in nudges:
                            viewer.cam.lookat[:] += 0.2 * {'w': forward, 's': -forward,
                                'd': right, 'a': -right, 'q': np.array([0, 0, -1]),
                                'e': np.array([0, 0, 1])}[nudge]
                    position = None
                    if placement == 'camera':
                        position = viewer.cam.lookat[:2].copy()
                    elif placement == 'mouth':
                        try:
                            position = source_at_mouth(sim, command['selected_source'])
                        except ValueError as error:
                            AppHelper.callAfter(panel.status.setStringValue_, str(error))
                    elif isinstance(placement, list):
                        point = np.zeros(3)
                        hit = mujoco.mjv_select(sim.mj_model, sim.mj_data, viewer.opt,
                            viewer.viewport.width / viewer.viewport.height, *placement,
                            pick_scene, point, np.zeros(1, dtype=np.int32),
                            np.zeros(1, dtype=np.int32), np.zeros(1, dtype=np.int32))
                        if hit >= 0:
                            position = point[:2]
                if position is not None:
                    with lock:
                        source = controls['sources'][controls['selected_source']]
                        source.update(enabled=True, x=float(np.clip(position[0], -100, 100)),
                                      y=float(np.clip(position[1], -100, 100)))
                        command = copy.deepcopy(controls)
                    AppHelper.callAfter(panel.refresh)
                if checkpoint_action:
                    try:
                        if checkpoint_action == 'save':
                            backend.update(dict(command, paused=True))
                        result = backend.checkpoint(checkpoint_action, args.checkpoint_name)
                        with lock:
                            controls.update(sources=result['sources'], reset=result['reset'], paused=True, release_block=result['release_block'])
                            command = copy.deepcopy(controls)
                        AppHelper.callAfter(panel.refresh)
                        AppHelper.callAfter(panel.status.setStringValue_,
                            f'{"Saved" if checkpoint_action == "save" else "Restored"} {args.checkpoint_name} at {result["time"]:.4f} s')
                    except ValueError as error:
                        AppHelper.callAfter(panel.status.setStringValue_, str(error))
                    status_time = time.monotonic()+4
                persistent = {key: command[key] for key in ('sources', 'selected_source')}
                if persistent != saved_controls:
                    temporary = control_path.with_suffix('.tmp')
                    temporary.write_text(json.dumps(persistent, indent=2) + '\n')
                    temporary.replace(control_path)
                    saved_controls = copy.deepcopy(persistent)
                frame = backend.update(command)
                qpos, qvel = np.asarray(frame['qpos']), np.asarray(frame['qvel'])
                if qpos.shape != sim.mj_data.qpos.shape or qvel.shape != sim.mj_data.qvel.shape or not np.isfinite(qpos).all() or not np.isfinite(qvel).all():
                    raise RuntimeError('Invalid body state from CUDA worker')
                now = time.monotonic()
                fps = 1 / max(now - previous, 1e-6)
                previous = now
                with viewer.lock():
                    sim.mj_data.qpos[:] = qpos
                    sim.mj_data.qvel[:] = qvel
                    sim.mj_data.act[:] = frame['act']
                    sim.mj_data.ctrl[:] = frame['ctrl']
                    if 'qfrc_applied' in frame:
                        sim.mj_data.qfrc_applied[:] = frame['qfrc_applied']
                    sim.mj_data.time = frame['time']
                    apply_sources(sim, frame['sources'])  # Rendering transforms only; no local mj_step.
                if args.cns:
                    coverage = backend.info['body_coverage']
                    sensor_coverage = backend.info['sensory_coverage']
                    viewer.set_texts([
                        (None, mujoco.mjtGridPos.mjGRID_TOPLEFT,
                         'MALE CNS / EMBODIED MODEL\nCentral neurons\nConnected motor neurons\nConnected sensory neurons\nState\nSimulated time\nNeural spikes\nMotor spikes\nMapped motor spikes\nActive muscle units\nMax muscle tension\nReceptor temperature L/R\nContact taste\nStream',
                         f'\n{backend.info["neurons"]:,}\n{coverage["connected_motor_neurons"]} / {coverage["total_motor_neurons"]}\n'
                         f'{sensor_coverage["wired_sensory_neurons"]} / {sensor_coverage["total_sensory_neurons"]}\n'
                         f'{"PAUSED" if frame["paused"] else "RUNNING"}{" / release blocked" if frame["release_block"] else ""}\n{frame["time"]:.4f} s\n'
                         f'{frame["total_spikes"]:,}\n{frame["total_motor_spikes"]:,}\n{frame["connected_motor_spikes"]:,}\n'
                         f'{frame["active_muscle_units"]}\n{frame["max_muscle_tension_uN"]:.3f} uN\n'
                         f'{frame["sensed"]["thermoreceptor_temperature_c"][0]:.1f} / {frame["sensed"]["thermoreceptor_temperature_c"][1]:.1f} C\n'
                         f'taste sugar/bitter {frame["sugar_hz"]:.0f}/{frame["bitter_hz"]:.0f} Hz\n{fps:.0f} frames/s'),
                        (None, mujoco.mjtGridPos.mjGRID_BOTTOMLEFT,
                         'Ctrl+click: source | Ctrl+I: controls | Ctrl+M: muscle paths\n'
                         'Ctrl+9: free camera (WASD/QE) | Ctrl+8: body/feeding view\n'
                         'SPACE: pause | Ctrl+3: fresh individual | Ctrl+I: save/restore\n'
                         'No gait or action policy. Geometry/physiology are estimates.\n'
                         'Natural walking/flight unverified; peripheral and physiological gaps remain.', None),
                    ])
                else:
                    viewer.set_texts([
                    (None, mujoco.mjtGridPos.mjGRID_TOPLEFT,
                     'TETHERED MN9 MUSCLE ASSAY\nBackend\nNeurons\nState\nSimulated time\nSpikes\nP9 output L/R\nDNa02 output L/R\nOdor input L/R\nORN activity L/R\nTemperature L/R\nSugar / bitter input\nRight MN9 output\nM9 activation\nM9 tension\nRostrum angle\nMode\nStream',
                     f'\n{backend.info["gpu"]}\n{backend.info["neurons"]:,}\n'
                     f'{"PAUSED" if frame["paused"] else "RUNNING"}\n{frame["time"]:.2f} s\n'
                     f'{frame["total_spikes"]:,}\n{frame["p9_hz"][0]:.0f} / {frame["p9_hz"][1]:.0f} Hz\n'
                     f'{frame["steering_hz"][0]:.0f} / {frame["steering_hz"][1]:.0f} Hz\n'
                     f'{frame["sensed"]["odor_hz"][0]:.0f} / {frame["sensed"]["odor_hz"][1]:.0f} Hz\n'
                     f'{frame["odor_hz"][0]:.0f} / {frame["odor_hz"][1]:.0f} Hz\n'
                     f'{frame["sensed"]["temperature_c"][0]:.1f} / {frame["sensed"]["temperature_c"][1]:.1f} C\n'
                     f'{frame["sugar_hz"]:.0f} / {frame["bitter_hz"]:.0f} Hz\n'
                     f'{frame["mn9_hz"][0]:.0f} Hz\n{frame["muscle"]["activation"]:.1%}\n'
                     f'{frame["muscle"]["total_tension_uN"]:.3f} uN\n{np.degrees(frame["proboscis_angle"]):.1f} deg\n'
                     f'{"MANUAL OVERRIDES" if frame["manual_mode"] else "SENSORY ONLY"}\n{fps:.0f} frames/s'),
                    (None, mujoco.mjtGridPos.mjGRID_BOTTOMLEFT,
                     'Ctrl+click: place source  |  Ctrl+I: source controls\n'
                     'Ctrl+9 free camera: WASD move, Q/E height, drag to look\n'
                     'Ctrl+6 sweet / Ctrl+7 bitter: selected object taste\n'
                     'Ctrl+8 feeding view  |  SPACE pause  |  Ctrl+3 reset\n'
                     'Ctrl+M: show/hide muscle path through the cuticle\n'
                     'Estimated M9 physiology; fixed body, no walking controller.\n'
                     'Pain pathway unavailable; warmth is a separate input.', None),
                    ])
                viewer.sync()
                if now - status_time > 0.25:
                    contact = ', '.join(str(i + 1) for i in frame['sensed']['contacts']) or 'none'
                    muscle_status = (f'{frame["active_muscle_units"]} active units' if args.cns else
                        f'M9: {frame["muscle"]["activation"]:.1%} | {frame["muscle"]["total_tension_uN"]:.3f} uN')
                    AppHelper.callAfter(panel.status.setStringValue_, f'Mouth contact: {contact}\n{muscle_status}')
                    status_time = now
                if frame['paused']:
                    time.sleep(0.04)
    finally:
        if monitor:
            AppHelper.callAfter(NSEvent.removeMonitor_, monitor[0])
        if focus_observer:
            AppHelper.callAfter(NSNotificationCenter.defaultCenter().removeObserver_, focus_observer[0])
        if panel is not None:
            AppHelper.callAfter(panel.panel.close)
        if sim is not None:
            sim.close()
        backend.close()


if __name__ == '__main__':
    main()
