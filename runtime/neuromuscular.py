"""Estimated spike-driven NMJ. Native MuJoCo muscle owns activation and force."""
from collections import deque
import math


class NeuromuscularJunction:
    """Events emitted at a step's END can affect only later force intervals."""

    def __init__(self, dt, params):
        values = [dt, *(params[k] for k in ('delay_s', 'tau_exc_s',
                  'tau_recovery_s', 'spike_gain', 'depression'))]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('NMJ parameters must be finite')
        if dt <= 0 or min(params['tau_exc_s'], params['tau_recovery_s']) <= 0:
            raise ValueError('NMJ time constants must be positive')
        if min(params['delay_s'], params['spike_gain']) < 0 or not 0 <= params['depression'] <= 1:
            raise ValueError('Invalid NMJ delay, gain or depression')
        self.delay_steps = round(params['delay_s'] / dt)
        if not math.isclose(self.delay_steps * dt, params['delay_s'], abs_tol=1e-12):
            raise ValueError('NMJ delay must be on the simulation grid')
        self.dt, self.gain, self.depression = dt, params['spike_gain'], params['depression']
        self.decay = math.exp(-dt / params['tau_exc_s'])
        self.recovery = math.exp(-dt / params['tau_recovery_s'])
        self.reset()

    def reset(self):
        self.tick = self.received = self.delivered = 0
        self.efficacy, self.excitation = 1.0, 0.0
        self.pending = deque()

    def advance(self, spike_at_end=False, *, release_block=False):
        if spike_at_end not in (False, True, 0, 1) or type(release_block) is not bool:
            raise ValueError('One binary spike and a boolean release block are required')
        while self.pending and self.pending[0] == self.tick:
            self.pending.popleft()
            if not release_block:
                self.excitation += self.gain * self.efficacy
                self.efficacy *= 1 - self.depression
                self.delivered += 1
        mid = self.excitation * math.sqrt(self.decay)
        excitation_control = mid / (1 + mid)
        self.excitation *= self.decay
        self.efficacy = 1 - (1 - self.efficacy) * self.recovery
        self.tick += 1
        if spike_at_end:
            self.received += 1
            self.pending.append(self.tick + self.delay_steps)
        return excitation_control
