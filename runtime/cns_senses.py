"""Physical source observations -> verified MaleCNS receptor identities.

Unresolved modalities are reported rather than mapped to convenient neurons.
No motor neurons, target actions or muscle commands are accepted here.
"""
import hashlib
import json
from pathlib import Path

from arena import sample_sources
from cns_vision import Vision
from cns_proprio import Proprioception
from cns_thermal import Thermoreception

ROOT = Path(__file__).resolve().parent


class Senses:
    def __init__(self):
        path = ROOT / 'neural-motor/malecns-sensory-map.json'
        raw = path.read_bytes()
        self.mapping = json.loads(raw)
        if self.mapping['dataset'] != 'male-cns:v1.0':
            raise ValueError('Sensory mapping dataset does not match the CNS')
        self.groups = {g['id']: g for g in self.mapping['input_groups']}
        self.sha256 = hashlib.sha256(raw + b''.join((ROOT / f).read_bytes()
            for f in ('cns_senses.py', 'cns_vision.py', 'cns_proprio.py', 'cns_thermal.py', 'cns-model.json'))).hexdigest()
        self.vision = Vision(self.mapping)
        self.proprio = Proprioception(self.mapping)
        self.thermal = Thermoreception(self.mapping)
        self.wired_ids = set()
        for name in ('ORN_DM1', 'ORN_DM2', 'ORN_DM4', 'ORN_VM2', 'ORN_VA2', 'contact_bitter', 'contact_sugar'):
            g = self.groups[name]
            if not g['can_reuse_body_signal_after_id_join']:
                raise ValueError(f'{name} lacks a supported input correspondence')
            if name.startswith('contact_'):
                self.wired_ids.update(i for ids in g['body_ids_by_root_side'].values() for i in ids)
            else:
                self.wired_ids.update(i for side in ('L', 'R') for i in g['body_ids_by_root_side'].get(side, []))
        self.wired_ids.update(self.thermal.ids)
        chemical_count = len(self.wired_ids)
        self.wired_ids.update(self.vision.ids)
        self.wired_ids.update(self.proprio.ids)
        self.coverage = dict(total_sensory_neurons=self.mapping['counts']['sensory_entries'],
            wired_sensory_neurons=len(self.wired_ids), wired_ids=sorted(self.wired_ids),
            chemical_temperature_neurons=chemical_count, vision=self.vision.coverage,
            proprioception=self.proprio.coverage,
            thermoreception=self.thermal.coverage,
            transduction='Estimated plume, adapting thermal receptors and side-specific labellar contact; not calibrated receptor physiology',
            missing='Water transduction, other odor tuning, complete visual/proprioceptive physiology, tactile organ mechanics, sacculus cooling/humidity and other body senses',
            mapping_sha256=self.sha256)

    def reset(self):
        self.vision.reset()
        self.proprio.reset()
        self.thermal.reset()

    def observe(self, sim, sources):
        sensed = sample_sources(sim, sources)
        proprio_rates, proprio_observation = self.proprio.observe(sim)
        sensed.update(proprio_observation)
        irradiance = self.vision.observe(sim, sources)
        sensed['mean_irradiance'] = float(irradiance.mean())
        sensed['visual_receptors'] = len(self.vision.ids)
        rates = proprio_rates
        for name in ('ORN_DM1', 'ORN_DM2', 'ORN_DM4', 'ORN_VM2', 'ORN_VA2'):
            for side, rate in zip(('L', 'R'), sensed['odor_hz']):
                rates.update({int(i): float(rate) for i in self.groups[name]['body_ids_by_root_side'].get(side, [])})
        thermal_rates, thermal_observation = self.thermal.observe(sim, sources)
        rates.update(thermal_rates)
        sensed.update(thermal_observation)
        for group, signal in (('contact_bitter', 'bitter_hz'), ('contact_sugar', 'sugar_hz')):
            for index, side in enumerate(('L', 'R')):
                ids = self.groups[group]['body_ids_by_root_side'].get(side, [])
                rates.update({int(i): float(sensed[signal + '_by_side'][index]) for i in ids})
        sensed['sugar_mapping'] = '34 published LB3b/c IDs; side-specific physical contact, estimated sensillum/rate model'
        sensed['wired_sensory_neurons'] = len(self.wired_ids)
        return rates, irradiance, sensed
