"""Scene radiance at published retinal directions, with no object/taste labels.

The author vectors are measured estimates; their registration to this body's
head/eye meshes and broadband optical constants are explicit model hypotheses.
"""
import json
from pathlib import Path

import mujoco as mj
import numpy as np


class Vision:
    def __init__(self, mapping):
        self.params = json.loads((Path(__file__).parent / 'cns-model.json').read_text())['vision']
        visual = mapping['visual_columns']
        self.columns = [r for r in visual['column_to_view_direction']['rows'] if r['column'] is not None]
        lookup = {r['column']: i for i, r in enumerate(self.columns)}
        if len(lookup) != len(self.columns):
            raise ValueError('Duplicate optical columns')
        table = visual['receptor_column_coverage']
        receptors = [dict(zip(table['columns'], r)) for r in table['rows']]
        wired = sorted((r for r in receptors if r['view_direction_available']), key=lambda r:r['bodyId'])
        self.ids = [r['bodyId'] for r in wired]
        self.receptor_columns = np.array([lookup[r['column']] for r in wired])
        self.directions = np.array([[r['x'], r['y'], r['z']] for r in self.columns])
        norms = np.linalg.norm(self.directions, axis=1)
        if np.max(np.abs(norms - 1)) > 1e-5 or len(set(self.ids)) != len(self.ids):
            raise ValueError('Invalid optical mapping')
        self.directions /= norms[:, None]
        self.origins = None
        self.reset()
        self.coverage = dict(wired_photoreceptors=len(self.ids), optical_columns=len(self.columns),
            photoreceptors_without_direction=len(receptors)-len(self.ids),
            registration='Author +x forward/+y left/+z dorsal frame aligned to NMF head; ray origins at eye-mesh surface. Estimated inter-specimen registration.',
            transduction=self.params, chemical_ui_colors_visible=False, odor_halos_visible=False)

    def reset(self):
        self.last_tick = None
        self.source_state = None
        self.irradiance = np.zeros(len(self.ids))
        self.hits = np.full(len(self.columns), -1, dtype=np.int32)

    def _register(self, sim):
        model, data = sim.mj_model, sim.mj_data
        head = data.body('fly/c_head')
        rotation = head.xmat.reshape(3, 3)
        points = []
        for row, direction in zip(self.columns, self.directions):
            eye = model.geom(f'fly/{row["side"].lower()}_eye').id
            center = data.geom_xpos[eye]
            ray = rotation @ direction
            distance = mj.mj_rayMesh(model, data, eye, center, ray)
            if distance < 0 or not np.isfinite(distance):
                raise ValueError('Eye mesh has no corneal intersection for an optical ray')
            # Move just outside the cornea; the head and remaining fly still occlude.
            points.append(rotation.T @ (center + (distance + 1e-5) * ray - head.xpos))
        self.origins = np.array(points)
        self.ground = set(np.flatnonzero(model.geom_type == mj.mjtGeom.mjGEOM_PLANE))
        self.food = {model.geom(f'food_{i}').id for i in range(2)}

    def observe(self, sim, sources):
        tick = int(round(sim.time / sim.timestep))
        interval = int(round(self.params['sample_interval_s'] / sim.timestep))
        if interval < 1 or not np.isclose(interval * sim.timestep, self.params['sample_interval_s']):
            raise ValueError('Optical interval must be an integer number of physical ticks')
        # Taste/color and plume display changes cannot change optical input.
        source_state = tuple((s['enabled'], s['x'], s['y']) for s in sources)
        if (self.last_tick is not None and source_state == self.source_state
                and (tick == self.last_tick or tick % interval)):
            return self.irradiance
        if self.origins is None:
            self._register(sim)
        head = sim.mj_data.body('fly/c_head')
        rotation = head.xmat.reshape(3, 3)
        origins = self.origins @ rotation.T + head.xpos
        directions = self.directions @ rotation.T
        groups = np.array([1, 1, 1, 1, 1, 0], dtype=np.uint8)
        values = np.empty(len(self.columns))
        geom_id = np.empty(1, dtype=np.int32)
        p = self.params
        # ponytail: one native ray per column at 500 Hz; batch per-origin rays if profiling requires it.
        for i, (origin, direction) in enumerate(zip(origins, directions)):
            mj.mj_ray(sim.mj_model, sim.mj_data, origin, direction, groups, True, -1, geom_id)
            hit = int(geom_id[0])
            self.hits[i] = hit
            albedo = 1.0 if hit < 0 else (p['ground_albedo'] if hit in self.ground else
                     p['food_albedo'] if hit in self.food else p['body_albedo'])
            values[i] = p['sky_radiance'] * albedo
        self.irradiance = values[self.receptor_columns]
        if not np.isfinite(self.irradiance).all() or np.any(self.irradiance < 0):
            raise ValueError('Invalid scene radiance')
        self.last_tick, self.source_state = tick, source_state
        return self.irradiance
