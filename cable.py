import math
import random
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class CableStats:
    attenuation_factor: float
    noise_level: float
    propagation_delay: float


class Cable:
    """Simple analog cable model used by all layers.

    The cable applies attenuation, adds white noise, and tracks propagation delay.
    """

    def __init__(
        self,
        length: float = 100.0,
        attenuation: float = 0.1,
        noise_level: float = 0.05,
        debug_mode: bool = False,
        signal_velocity: float = 2e8,
    ) -> None:
        self.length = length
        self.attenuation = attenuation
        self.noise_level = noise_level
        self.debug_mode = debug_mode
        self.signal_velocity = signal_velocity
        self._last_sent: Optional[List[float]] = None
        self._last_received: Optional[List[float]] = None

    def transmit(self, signal: Iterable[float]) -> List[float]:
        """Simulate signal propagation through the cable."""
        self._last_sent = [float(x) for x in signal]
        attenuation_factor = math.exp(-self.attenuation * (self.length / 100.0))
        noisy = [sample * attenuation_factor for sample in self._last_sent]
        if self.noise_level > 0:
            noise = [random.gauss(0.0, self.noise_level) for _ in noisy]
            noisy = [value + n for value, n in zip(noisy, noise)]
        self._last_received = noisy
        if self.debug_mode:
            self.plot_signals()
        return noisy

    def get_propagation_delay(self) -> float:
        """Return the one-way propagation delay in seconds."""
        return self.length / self.signal_velocity

    def plot_signals(self) -> None:
        """Plot the last sent and received signals for debugging."""
        if self._last_sent is None or self._last_received is None:
            return
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 4))
        plt.plot(self._last_sent, label="sent")
        plt.plot(self._last_received, label="received", alpha=0.8)
        plt.legend()
        plt.title("Cable signal propagation")
        plt.xlabel("Sample")
        plt.ylabel("Amplitude")
        plt.tight_layout()
        plt.show()

    def get_signal_stats(self) -> CableStats:
        """Return statistics describing the most recent transmission."""
        attenuation_factor = math.exp(-self.attenuation * (self.length / 100.0))
        return CableStats(
            attenuation_factor=attenuation_factor,
            noise_level=self.noise_level,
            propagation_delay=self.get_propagation_delay(),
        )
