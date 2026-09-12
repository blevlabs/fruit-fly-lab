"""Small walking demo using FlyGym's published hybrid turning controller."""
import argparse
from pathlib import Path

import mediapy
import numpy as np
from flygym.anatomy import BodySegment
from body import make_body, reset_body
from flygym_demo.complex_terrain import (
    HybridControllerObservation, apply_locomotion_action,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=2.0)
    args = parser.parse_args()
    if not np.isfinite(args.seconds) or args.seconds < 0.1:
        parser.error('--seconds must be finite and at least 0.1')
    output = Path(__file__).resolve().parents[1] / 'runs/walk'
    output.mkdir(parents=True, exist_ok=True)
    sim, fly, controller = make_body(locomotion=True)
    camera = sim.mj_model.camera(0).name
    try:
        renderer = sim.set_renderer([camera], camera_res=(480, 640),
                                    playback_speed=0.2, output_fps=25)
        reset_body(sim, fly, controller)
        thorax = fly.get_bodysegs_order().index(BodySegment('c_thorax'))
        start = sim.get_body_positions(fly.name)[thorax].copy()
        for _ in range(round(args.seconds / sim.timestep)):
            obs = HybridControllerObservation.from_sim(sim, fly.name)
            # This is a hand-set descending command, not output from the brain model.
            action = controller.step(np.array([1.0, 1.0]), obs)
            apply_locomotion_action(sim, fly.name, action)
            sim.step()
            sim.render_as_needed()
        displacement = sim.get_body_positions(fly.name)[thorax] - start
        frames = renderer.frames[camera]
        assert np.isfinite(sim.mj_data.qpos).all(), 'Non-finite physics state'
        assert np.linalg.norm(displacement[:2]) > 0.01, 'Fly did not move'
        assert len(frames) > 1 and np.std(frames[-1]) > 5, 'Blank rendering'
        renderer.save_video(output / 'walk.mp4')
        mediapy.write_image(output / 'walk.png', frames[len(frames) // 2])
        print(f'PASS: {args.seconds:g} s, {len(frames)} frames, '
              f'displacement {np.round(displacement, 3)} mm; {output / "walk.mp4"}')
    finally:
        sim.close()


if __name__ == '__main__':
    main()
