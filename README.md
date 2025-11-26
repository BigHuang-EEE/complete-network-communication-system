# Complete Network Communication System

This project simulates the full data path from the physical layer to the application layer using a simplified cable model. The implementation covers:

- **Level 1:** Point-to-point digital communication with modulation/demodulation and parity-based error detection.
- **Level 2:** Multi-host networking with addressing, forwarding, and collision handling on a shared medium.

## Running tests

```bash
pytest -q
```

## Key components
- `cable.py` — Analog cable model that adds attenuation and noise and can visualize signals in debug mode.
- `communication.py` — Bit/byte conversion helpers, parity encoding, and NRZ-style modulation/demodulation.
- `network.py` — Multi-host network built on the cable with host registration, addressing, and collision detection utilities.
