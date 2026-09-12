"""One local mapping/capacity/force check; diagnostic spikes never enter runtime."""
from collections import defaultdict
import json
from pathlib import Path

import mujoco
import numpy as np

from cns_body import MotorUnits, body_signature, make_body
from flight_integration import FlightMotorUnits


def main():
    sim, _, coverage = make_body(tethered=True)
    try:
        model, data = sim.mj_model, sim.mj_data
        assert model.opt.solver == mujoco.mjtSolver.mjSOL_NEWTON and model.opt.noslip_iterations == 0
        assert min((c.dist for c in data.contact), default=0) >= -.001, 'Deep initial proxy overlap would inject artificial forces'
        motors = MotorUnits(model, coverage)
        flight = FlightMotorUnits(model, coverage['flight_motor_units'])
        assert not set(motors.ids) & set(flight.ids)
        assert len(motors.ids) + len(flight.ids) == coverage['connected_motor_neurons']
        assert np.all(model.actuator_trntype == mujoco.mjtTrn.mjTRN_TENDON)
        asynchronous = {model.actuator(u['actuator_name']).id for u in flight.units if u['kind'] == 'asynchronous'}
        assert model.na == model.nu - len(asynchronous)
        assert all(kind == (mujoco.mjtDyn.mjDYN_NONE if i in asynchronous else mujoco.mjtDyn.mjDYN_MUSCLE)
                   for i, kind in enumerate(model.actuator_dyntype))
        # Passive wall/joint elasticity stores mechanical energy. It does not
        # receive a target-angle command; every active actuator is a tendon force.
        assert np.isfinite(model.jnt_stiffness).all() and np.all(model.jnt_stiffness >= 0)
        capacities = defaultdict(float)
        for unit in coverage['motor_units']:
            index = model.actuator(unit['actuator_name']).id
            capacities[unit['source_muscle_path']] += model.actuator_gainprm[index, 2]
        for path in coverage['muscle_paths']:
            if path['motor_neuron_ids']:
                np.testing.assert_allclose(capacities[path['actuator_name']], path['force_uN'])
        for body_id, expected_sides in ((10156, {'left'}), (535501, {'left', 'right'}), (19823, {'unpaired'})):
            actual = {u['side'] for u in coverage['motor_units'] if u['bodyId'] == body_id}
            assert actual == expected_sides, f'Crossed/bilateral/unpaired anatomy mismatch for {body_id}'
        events = np.zeros(len(motors.ids), dtype=bool)
        selected_id = 16949
        events[motors.index[selected_id]] = True
        active_indices = [model.actuator(u['actuator_name']).id for u in coverage['motor_units'] if u['bodyId'] == selected_id]
        assert len(active_indices) == 1
        first_due_tick = motors.nmjs[0].delay_steps + 1
        for tick in range(first_due_tick + 20):
            motors.advance(data, events if tick == 0 else np.zeros_like(events))
            flight.advance(data, np.zeros(len(flight.ids), dtype=bool))
            if tick < first_due_tick:
                assert not data.ctrl[motors.actuators].any()
            else:
                assert sorted(motors.actuators[np.flatnonzero(data.ctrl[motors.actuators])].tolist()) == active_indices
            sim.step()
            mujoco.mj_forward(model, data)
        assert np.isfinite(data.qpos).all() and not np.any(data.warning.number)
        # A release block on fresh state must not create excitation or activation.
        sim.reset(); motors.reset(); flight.reset()
        mujoco.mj_forward(model, data)
        block_ticks = first_due_tick + 50
        for _ in range(block_ticks):
            motors.advance(data, np.ones_like(events), release_block=True)
            flight.advance(data, np.ones(len(flight.ids), dtype=bool), release_block=True)
            sim.step()
            mujoco.mj_forward(model, data)
        assert not data.ctrl[motors.actuators].any() and not data.act.any()
        assert all(v['active_force_uN'] == 0 and v['activation'] == 0 for v in flight.last_forces.values())
        assert all(n.received == block_ticks and n.delivered == 0 for n in motors.nmjs)
        receipt = dict(status='PASS: exact motor identities, capacity accounting and causal force delivery',
            body_sha=body_signature(), connected_motor_neurons=len(motors.ids) + len(flight.ids),
            connected_flight_motor_neurons=len(flight.ids), asynchronous_units=len(asynchronous),
            physics_timestep_s=model.opt.timestep, first_due_tick=first_due_tick,
            native_actuators=model.nu, named_motor_unit_actuators=len(coverage['motor_units']),
            release_block='pass', no_joint_servo=True, no_gait_controller=True,
            input_event='isolated right MN9 test only; not an environmental behavior',
            limitations=coverage['unimplemented_body'])
        output = (Path(__file__).resolve().parents[1] / 'runtime') / '../runs/cns/body-check.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))
    finally:
        sim.close()


if __name__ == '__main__':
    main()
