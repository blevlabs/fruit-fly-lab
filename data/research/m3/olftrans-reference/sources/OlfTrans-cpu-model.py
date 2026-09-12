"""CPU Models
"""
import numpy as np
from abc import abstractmethod
from collections.abc import Iterable
from numbers import Number
from functools import wraps
import copy
from tqdm import tqdm
import typing as tp
from .. import utils


class Model:
    Time_Scale = 1.0
    States = dict()
    Params = dict()

    def __init__(self, num=1, floatType=np.double, **states_or_params):
        self.num = num
        self.states = {key: copy.deepcopy(val) for key, val in self.States.items()}
        self.params = {key: copy.deepcopy(val) for key, val in self.Params.items()}
        for key, val in states_or_params.items():
            if key in self.states:
                self.states[key] = val
            elif key in self.params:
                self.params[key] = val
            else:
                raise ValueError(
                    f"Argument '{key}' with value '{val}' is neither state nor params."
                )

        self._float = floatType
        self.bounds = {k: (-np.inf, np.inf) for k in self.states}
        self.recorder = {}
        self._recorder_ctr = 0

        _states = copy.deepcopy(self.states)
        for key, val in _states.items():
            if isinstance(val, Iterable):
                assert all(
                    [isinstance(v, Number) for v in val]
                ), "values of array should all be scalar valued"
                if len(val) == 3:
                    self.bounds[key] = (val[1], val[2])
                    self.states[key] = np.full((num,), val[0], dtype=self._float)
                elif len(val) == num:
                    pass
                else:
                    raise ValueError(
                        f"""If a state is iterable, it has to either be a 3-tuple of form (initial, min, max), or an array of length = num ({num})
                    For State '{key}' got {len(val)} instead: {val}"""
                    )
            elif isinstance(val, Number):
                self.states[key] = np.full((num,), val, dtype=self._float)
            else:
                raise TypeError(
                    f"State '{key}' has value that is neither iterable nor number {val}"
                )

        _params = copy.deepcopy(self.params)
        for key, val in _params.items():
            if isinstance(val, Iterable):
                assert (
                    len(val) == num
                ), f"Param '{key}' is iterable of length {len(val)} but num = {num}"
            elif isinstance(val, Number):
                self.params[key] = np.full((num,), val, dtype=self._float)
            else:
                raise TypeError(
                    f"Param '{key}' has value that is neither iterable nor number {val}"
                )
        self.d_states = copy.deepcopy(self.states)

    def update(self, dt, **inputs):
        self.d_states = self.gradient(**inputs)
        for key in self.d_states:
            self.states[key] += (dt * self.Time_Scale) * self.d_states[key]
            np.clip(self.states[key], *self.bounds[key], out=self.states[key])
        self.states.update(self.non_gradient())
        for key in self.recorder:
            self.recorder[key][self._recorder_ctr] = self.states[key]
        self._recorder_ctr += 1

    def __getattr__(self, attr):
        if attr in self.states:
            return self.states[attr]
        elif attr in self.params:
            return self.params[attr]
        else:
            raise AttributeError(f"Attribute '{attr}' not found")

    @abstractmethod
    def gradient(self, **inputs):
        """Update function of the ODE dx/dt = f(x)

        Computes gradient of all states, returned as dictionary
        """

    def non_gradient(self):
        """Non-gradient Update"""
        return {}

    def record(self, steps, states):
        if not hasattr(states, "__len__"):
            states = [states]
        for key in states:
            if key not in self.states:
                assert KeyError(f"Variable '{key}' not in States: {self.states.keys()}")
            self.recorder[key] = np.zeros(
                (steps, self.num), dtype=self.states[key].dtype
            )


class OTP(Model):
    States = dict(
        v=(0.0, 0, 1e9),
        I=0.0,
        uh=(0.0, 0.0, 50000.0),
        duh=0.0,
        x1=(0.0, 0.0, 1.0),
        x2=(0.0, 0.0, 1.0),
        x3=(0.0, 0.0, 1000.0),
    )
    Params = dict(
        br=1.0,
        dr=1.0,
        gamma=0.215,
        b1=0.8,
        a1=45.0,
        a2=146.1,
        b2=117.2,
        a3=2.539,
        b3=0.9096,
        kappa=8841,
        p=1.0,
        c=0.06546,
        Imax=62.13,
    )

    def gradient(self, stimulus=0.0):
        d_x1 = self.br * self.v * (1.0 - self.x1) - self.dr * self.x1
        d_x2 = (
            self.a2 * self.x1 * (1.0 - self.x2)
            - self.b2 * self.x2
            - self.kappa * np.cbrt(self.x2 * self.x2) * np.cbrt(self.x3 * self.x3)
        )
        d_x3 = self.a3 * self.x2 - self.b3 * self.x3
        d_uh = self.duh
        d_duh = -2 * self.a1 * self.b1 * self.duh + self.a1 * self.a1 * (
            stimulus - self.uh
        )
        return dict(x1=d_x1, x2=d_x2, x3=d_x3, uh=d_uh, duh=d_duh)

    def non_gradient(self):
        I = self.Imax * self.x2 / (self.x2 + self.c)
        v = self.uh + self.gamma * self.duh
        return dict(I=I, v=v)


class NoisyConnorStevens(Model):
    Time_Scale = 1e3  # s to ms
    States = dict(
        spike=0.0,
        v1=-60.0,
        v2=-60.0,
        v=(-60, -80, 80),
        n=(0.0, 0.0, 1.0),
        m=(0.0, 0.0, 1.0),
        h=(1.0, 0.0, 1.0),
        a=(1.0, 0.0, 1.0),
        b=(1.0, 0.0, 1.0),
        refactory=0.0,
    )
    Params = dict(
        ms=-5.3,
        ns=-4.3,
        hs=-12.0,
        gNa=120.0,
        gK=20.0,
        gL=0.3,
        ga=47.7,
        ENa=55.0,
        EK=-72.0,
        EL=-17.0,
        Ea=-75.0,
        sigma=2.05,
        refperiod=1.0,
    )

    def gradient(self, stimulus=0.0):

        alpha = np.exp(-(self.v + 50.0 + self.ns) / 10.0) - 1.0
        _mask = np.abs(alpha) <= 1e-7
        alpha[_mask] = 0.1
        alpha[~_mask] = (
            -0.01 * (self.v[~_mask] + 50.0 + self.ns[~_mask]) / alpha[~_mask]
        )

        beta = 0.125 * np.exp(-(self.v + 60.0 + self.ns) / 80.0)
        n_inf = alpha / (alpha + beta)
        tau_n = 2.0 / (3.8 * (alpha + beta))

        alpha = np.exp(-(self.v + 35.0 + self.ms) / 10.0) - 1.0
        _mask = np.abs(alpha) <= 1e-7
        alpha[_mask] = 1.0
        alpha[~_mask] = -0.1 * (self.v[~_mask] + 35.0 + self.ms[~_mask]) / alpha[~_mask]

        beta = 4.0 * np.exp(-(self.v + 60.0 + self.ms) / 18.0)
        m_inf = alpha / (alpha + beta)
        tau_m = 1.0 / (3.8 * (alpha + beta))

        alpha = 0.07 * np.exp(-(self.v + 60.0 + self.hs) / 20.0)
        beta = 1.0 / (1.0 + np.exp(-(self.v + 30.0 + self.hs) / 10.0))
        h_inf = alpha / (alpha + beta)
        tau_h = 1.0 / (3.8 * (alpha + beta))

        a_inf = np.cbrt(
            0.0761
            * np.exp((self.v + 94.22) / 31.84)
            / (1.0 + np.exp((self.v + 1.17) / 28.93))
        )
        tau_a = 0.3632 + 1.158 / (1.0 + np.exp((self.v + 55.96) / 20.12))
        b_inf = np.power(1 / (1 + np.exp((self.v + 53.3) / 14.54)), 4.0)
        tau_b = 1.24 + 2.678 / (1 + np.exp((self.v + 50) / 16.027))

        i_na = self.gNa * np.power(self.m, 3) * self.h * (self.v - self.ENa)
        i_k = self.gK * np.power(self.n, 4) * (self.v - self.EK)
        i_l = self.gL * (self.v - self.EL)
        i_a = self.ga * np.power(self.a, 3) * self.b * (self.v - self.Ea)

        d_v = stimulus - i_na - i_k - i_l - i_a
        d_n = (n_inf - self.n) / tau_n + np.random.randn(self.num) * self.sigma
        d_m = (m_inf - self.m) / tau_m + np.random.randn(self.num) * self.sigma
        d_h = (h_inf - self.h) / tau_h + np.random.randn(self.num) * self.sigma
        d_a = (a_inf - self.a) / tau_a + np.random.randn(self.num) * self.sigma
        d_b = (b_inf - self.b) / tau_b + np.random.randn(self.num) * self.sigma
        d_refactory = self.refactory < 0
        return dict(v=d_v, n=d_n, m=d_m, h=d_h, a=d_a, b=d_b, refactory=d_refactory)

    def non_gradient(self):
        spike = (self.v1 <= self.v2) * (self.v <= self.v2) * (self.v2 > -30.0)
        v1 = self.v2
        v2 = self.v
        spike = (spike > 0.0) * (self.refactory >= 0)
        refactory = self.refactory - (spike > 0.0) * self.refperiod
        return dict(spike=spike, v1=v1, v2=v2, refactory=refactory)


def compute_fi(
    NeuronModel,
    Is,
    repeat=1,
    input_var="stimulus",
    spike_var="spike",
    voltage_var="v",
    dur=2.0,
    start=0.5,
    dt=1e-5,
    verbose=True,
    neuron_params=None,
) -> tp.Tuple[tp.Tuple[np.ndarray, np.ndarray], Model]:
    neuron_params = neuron_params or {}
    Is = np.atleast_1d(Is)
    N_amps = len(Is)
    N_comps = repeat * N_amps
    wav = np.ascontiguousarray(
        utils.generate_stimulus("step", dt, dur, (start, dur), Is).T
    )  # shape (NT, NComp)
    t = np.arange(0, dur, dt)
    assert len(t) == wav.shape[0]
    wav = np.repeat(wav, repeat, axis=1)
    assert wav.shape[1] == N_comps
    neurons = NeuronModel(num=N_comps, **neuron_params)
    neurons.record(len(t), (spike_var, voltage_var))

    if verbose:
        pbar = tqdm(enumerate(wav), total=wav.shape[0], desc=f"F-I of {NeuronModel}")
        iterator = pbar
    else:
        iterator = enumerate(wav)
    for tt, inp in iterator:
        neurons.update(dt, **{input_var: inp})
    Nspikes = neurons.recorder["spike"][t > start].sum(0)
    Nspikes = Nspikes.reshape((-1, repeat))
    Nspikes = Nspikes.mean(1) / (dur - start)
    return (Is, Nspikes), neurons
