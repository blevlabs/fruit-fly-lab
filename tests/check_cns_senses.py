"""Physical input isolation; no behavioral response is a pass criterion."""
import json
from pathlib import Path

import mujoco as mj
import numpy as np

from arena import apply_sources, default_sources, mouth_geometries, source_at_mouth
from cns_body import make_body
from cns_senses import Senses


def main():
    sim, _, _ = make_body()
    senses = Senses()
    non_taste_ids = senses.proprio.ids | senses.thermal.ids
    try:
        sources = default_sources()
        sources[0].update(x=2, y=1)
        apply_sources(sim, sources)
        rates, optical, observation = senses.observe(sim, sources)
        assert len(rates) == 354 + len(senses.proprio.ids) and len(optical) == 5713
        assert observation['sugar_hz'] == 0 and observation['bitter_hz'] == 0
        assert np.count_nonzero(senses.vision.hits == sim.mj_model.geom('food_0').id) > 0
        assert all(sim.mj_model.geom(int(i)).name[:9] != 'odor_halo' for i in senses.vision.hits if i >= 0)
        # Re-sample after changing purely chemical fields and their UI colors.
        sources[0].update(taste='bitter', odor=0, temperature=45)
        apply_sources(sim, sources)
        senses.vision.reset()
        _, chemical_change, _ = senses.observe(sim, sources)
        assert np.array_equal(optical, chemical_change), 'Chemical UI leaked into retinal input'
        sources[0].update(x=-3, y=-2)
        apply_sources(sim, sources)
        _, moved, _ = senses.observe(sim, sources)
        changed_receptors = int(np.count_nonzero(moved != optical))
        assert changed_receptors > 0, 'Visible object position did not change physical rays'
        # Source contact reaches the correct published taste IDs independently.
        x, y = source_at_mouth(sim, 0)
        sources[0].update(x=float(x), y=float(y), taste='sweet', odor=0, temperature=22)
        apply_sources(sim, sources)
        sweet, _, observation = senses.observe(sim, sources)
        assert len(observation['contacts']) == 1 and observation['sugar_hz'] == 200
        assert observation['wet_contacts'] == [0]
        sources[0]['liquid'] = False
        dry_rates, _, dry = senses.observe(sim, sources)
        assert dry['wet_contacts'] == [] and dry['sugar_hz'] == 200 and dry_rates == sweet
        sources[0]['liquid'] = True
        mouths = set(mouth_geometries(sim.mj_model).values())
        # A small additional displacement crosses from near-contact taste
        # sampling into native mechanical contact with a labellar surface.
        sources[0]['x'] -= .05
        apply_sources(sim, sources)
        food_id = sim.mj_model.geom('food_0').id
        assert any(food_id in (c.geom1, c.geom2) and bool(mouths & {int(c.geom1), int(c.geom2)})
                   for c in sim.mj_data.contact), 'Food did not mechanically contact the mouth'
        sources[0]['enabled'] = False
        apply_sources(sim, sources)
        assert sim.mj_model.geom('food_0').contype[0] == sim.mj_model.geom('food_0').conaffinity[0] == 0
        assert not any(food_id in (c.geom1, c.geom2) for c in sim.mj_data.contact)
        sources[0].update(enabled=True, x=float(x))
        apply_sources(sim, sources)
        sugar_ids = {i for ids in senses.groups['contact_sugar']['body_ids_by_root_side'].values() for i in ids}
        bitter_ids = {i for ids in senses.groups['contact_bitter']['body_ids_by_root_side'].values() for i in ids}
        assert {i for i, rate in sweet.items() if rate and i not in non_taste_ids} == sugar_ids and len(sugar_ids) == 34
        sources[0]['taste'] = 'bitter'
        apply_sources(sim, sources)
        bitter, _, _ = senses.observe(sim, sources)
        assert {i for i, rate in bitter.items() if rate and i not in non_taste_ids} == bitter_ids and len(bitter_ids) == 38
        if observation['taste_contact_geometry'] == 'bilateral_labella':
            mouths = mouth_geometries(sim.mj_model)
            center = np.mean([sim.mj_data.geom_xpos[i] for i in mouths.values()], axis=0)
            found = False
            # Geometric one-sided contact assay; no neural or muscle output is used.
            for offset in np.linspace(.2, 1.2, 81):
                sources[0].update(x=float(center[0]), y=float(center[1]+offset), taste='sweet')
                apply_sources(sim, sources)
                unilateral, _, side_observation = senses.observe(sim, sources)
                if side_observation['labellar_contacts']['L'] and not side_observation['labellar_contacts']['R']:
                    expected = set(senses.groups['contact_sugar']['body_ids_by_root_side']['L'])
                    assert {i for i, rate in unilateral.items() if rate and i not in non_taste_ids} == expected
                    found = True
                    break
            assert found, 'Could not isolate left labellar physical contact'
        # A global rigid-body rotation moves the optical frame with the head.
        before = senses.vision.directions @ sim.mj_data.body('fly/c_head').xmat.reshape(3, 3).T
        root = next(j for j in range(sim.mj_model.njnt) if sim.mj_model.jnt_type[j] == mj.mjtJoint.mjJNT_FREE)
        adr = sim.mj_model.jnt_qposadr[root]
        sim.mj_data.qpos[adr+3:adr+7] = (np.sqrt(.5), 0, 0, np.sqrt(.5))
        mj.mj_forward(sim.mj_model, sim.mj_data)
        after = senses.vision.directions @ sim.mj_data.body('fly/c_head').xmat.reshape(3, 3).T
        assert np.allclose(after[:, 0], -before[:, 1]) and np.allclose(after[:, 1], before[:, 0])
        receipt = dict(status='PASS: registered physical sensory inputs, not behavioral validation',
            senses_sha=senses.sha256, chemical_temperature_ids=len(rates)-len(senses.proprio.ids), optical_ids=len(optical),
            proprioceptive_ids=len(senses.proprio.ids),
            optical_columns=len(senses.vision.columns), receptors_changed_by_object_move=changed_receptors,
            sugar_ids=len(sugar_ids), bitter_ids=len(bitter_ids), chemical_optical_isolation=True,
            taste_contact_geometry=observation['taste_contact_geometry'],
            physical_source_contacts=True, disabled_source_has_no_collision=True,
            liquid_boundary_independent_of_taste=True,
            body_rotation_updates_optical_frame=True, limits=senses.coverage['missing'])
        path = (Path(__file__).resolve().parents[1] / 'runtime') / '../runs/cns/sensory-check.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps(receipt, indent=2))
    finally:
        sim.close()


if __name__ == '__main__':
    main()
