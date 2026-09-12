"""Synthetic MuJoCo muscle mechanics check; NOT anatomy, NMJ, or MN9 validation.

Run with ../.venv/bin/python -B muscle_mechanics_probe.py (or from project root).
Units: mm, g, seconds; force = microNewtons, hinge torque = nN*m.
Only ctrl is assigned during integration. No viewer, network, files, or FlyGym.
"""

import json

import mujoco as mj
import numpy as np


XML = """
<mujoco model="synthetic_muscle_hinge">
  <compiler angle="radian"/>
  <option timestep="0.0001" gravity="0 0 0" integrator="RK4"/>
  <worldbody>
    <site name="origin" pos="0 0.5 0" size="0.01"/>
    <body name="lever">
      <joint name="hinge" type="hinge" axis="0 0 1" limited="false"/>
      <geom type="capsule" fromto="0 0 0 1 0 0" size="0.02"
            mass="0.001" contype="0" conaffinity="0"/>
      <site name="insertion" pos="1 0 0" size="0.01"/>
    </body>
  </worldbody>
  <tendon>
    <spatial name="line" width="0.005">
      <site site="origin"/>
      <site site="insertion"/>
    </spatial>
  </tendon>
  <actuator>
    <muscle name="pull" tendon="line" gear="1" ctrllimited="true"
            ctrlrange="0 1" lengthrange="0.5 1.5" range="0.25 1.25"
            force="0.02" timeconst="0.01 0.04" tausmooth="0"
            lmin="0.5" lmax="1.6" vmax="1.5" fpmax="1.3" fvmax="1.2"/>
  </actuator>
  <sensor>
    <actuatorpos name="length" actuator="pull"/>
    <actuatorvel name="velocity" actuator="pull"/>
    <actuatorfrc name="force" actuator="pull"/>
    <jointpos name="angle" joint="hinge"/>
    <jointvel name="angular_velocity" joint="hinge"/>
    <jointactuatorfrc name="torque" joint="hinge"/>
  </sensor>
</mujoco>
"""


def run(model, pulse):
    data = mj.MjData(model)
    lr = model.actuator_lengthrange[0]
    acc0 = model.actuator_acc0[0]
    prm = model.actuator_gainprm[0, :9]
    biasprm = model.actuator_biasprm[0, :9]
    actadr = model.actuator_actadr[0]
    rows = []
    for step in range(round(0.3 / model.opt.timestep)):
        # Synthetic excitation pulse; no spike-to-excitation model is claimed.
        data.ctrl[0] = float(pulse and 0.02 <= step * model.opt.timestep < 0.12)
        mj.mj_step(model, data)
        mj.mj_forward(model, data)  # Refresh outputs at the integrated state.
        length, velocity = data.actuator_length[0], data.actuator_velocity[0]
        activation = data.act[actadr]
        active = activation * mj.mju_muscleGain(length, velocity, lr, acc0, prm)
        passive = mj.mju_muscleBias(length, lr, acc0, biasprm)
        force = data.actuator_force[0]
        start, count = data.moment_rowadr[0], data.moment_rownnz[0]
        columns = data.moment_colind[start:start + count]
        moment = data.actuator_moment[start:start + count]
        torque = np.zeros(model.nv)
        torque[columns] = moment * force
        np.testing.assert_allclose(force, active + passive, atol=1e-12)
        np.testing.assert_allclose(data.qfrc_actuator, torque, atol=1e-12)
        np.testing.assert_allclose(torque @ data.qvel, force * velocity, atol=1e-12)
        np.testing.assert_allclose(data.sensordata,
                                   [length, velocity, force, data.qpos[0],
                                    data.qvel[0], torque[0]], atol=1e-12)
        rows.append([data.time, data.qpos[0], activation, length, velocity,
                     force, active, passive, torque[0]])
    assert not np.any(data.warning.number), "MuJoCo reported a numerical warning"
    result = np.array(rows)
    assert np.isfinite(result).all()
    return result


def main():
    model = mj.MjModel.from_xml_string(XML)
    assert (model.nq, model.nv, model.nu, model.na) == (1, 1, 1, 1)
    assert not model.jnt_limited[0] and not np.any(model.jnt_stiffness)
    lr, prm = model.actuator_lengthrange[0], model.actuator_gainprm[0, :9]
    l0 = (lr[1] - lr[0]) / (prm[1] - prm[0])
    lt = lr[0] - prm[0] * l0
    f0, acc0 = prm[2], model.actuator_acc0[0]
    gain = lambda length, velocity: mj.mju_muscleGain(length, velocity, lr, acc0, prm)
    bias = lambda length: mj.mju_muscleBias(length, lr, acc0, prm)
    np.testing.assert_allclose(gain(lt + l0, 0), -f0)
    np.testing.assert_allclose(gain(lt + l0, -l0 * prm[6]), 0, atol=1e-12)
    np.testing.assert_allclose(gain(lt + l0, l0 * prm[6]), -f0 * prm[8])
    np.testing.assert_allclose(gain(lt + l0 * prm[4], 0), 0, atol=1e-12)
    np.testing.assert_allclose(gain(lt + l0 * prm[5], 0), 0, atol=1e-12)
    np.testing.assert_allclose(bias(lt + l0), 0, atol=1e-12)
    # 3.9 source yields 1.5*fpmax at lmax; documentation says fpmax.
    passive_at_lmax = -bias(lt + l0 * prm[5]) / f0
    np.testing.assert_allclose(passive_at_lmax, 1.5 * prm[7])
    rest, driven = run(model, False), run(model, True)
    np.testing.assert_allclose(rest[:, [1, 2, 5, 8]], 0, atol=1e-12)
    assert driven[-1, 1] > 0.01 and driven[-1, 3] < driven[0, 3]
    assert 0 < driven[:, 2].max() < 1 and driven[-1, 2] < driven[:, 2].max() / 10
    assert driven[:, 5].min() < 0 and driven[:, 8].max() > 0
    print(json.dumps({
        "status": "PASS: synthetic mechanics only; no NMJ/MN9 validation",
        "mujoco": mj.__version__, "timestep_s": model.opt.timestep,
        "rest_angle_rad": float(rest[-1, 1]),
        "pulse_angle_rad": float(driven[-1, 1]),
        "peak_activation": float(driven[:, 2].max()),
        "final_activation": float(driven[-1, 2]),
        "final_length_mm": float(driven[-1, 3]),
        "peak_tension_uN": float(-driven[:, 5].min()),
        "peak_torque_nNm": float(driven[:, 8].max()),
        "passive_at_lmax_over_F0": float(passive_at_lmax),
    }, indent=2))


if __name__ == "__main__":
    main()
