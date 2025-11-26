from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, List, Optional

from cable import Cable
from communication import EncodedFrame, add_parity_bits, bits_to_string, demodulate, modulate, string_to_bits, strip_parity_bits


class CollisionError(RuntimeError):
    """Raised when two hosts attempt to transmit simultaneously."""


@dataclass
class ReceivedMessage:
    src: int
    dst: int
    payload: str


class Host:
    def __init__(self, address: int, network: "MultiHostNetwork") -> None:
        self.address = address
        self.network = network
        self.last_received: Optional[ReceivedMessage] = None

    def send(self, destination: int, message: str) -> None:
        self.network.send_message(self.address, destination, message)

    def receive(self, frame: EncodedFrame) -> Optional[ReceivedMessage]:
        if frame.dst not in (self.address, 255):
            return None
        data_bits = strip_parity_bits(frame.payload_bits)
        payload = bits_to_string(data_bits)
        return ReceivedMessage(src=frame.src, dst=frame.dst, payload=payload)


class MultiHostNetwork:
    def __init__(self, cable: Optional[Cable] = None) -> None:
        self.cable = cable or Cable()
        self.hosts: Dict[int, Host] = {}
        self._channel_lock = threading.Lock()

    def register_host(self, address: int) -> Host:
        if address in self.hosts:
            raise ValueError(f"Host {address} already registered")
        host = Host(address, self)
        self.hosts[address] = host
        return host

    def send_message(self, src: int, dst: int, message: str) -> None:
        frame = self._build_frame(src, dst, message)
        bits = frame.to_bits()
        analog_signal = modulate(bits)
        with self._channel_lock:
            transmitted = self.cable.transmit(analog_signal)
        recovered_bits = demodulate(transmitted)
        received_frame = EncodedFrame.from_bits(recovered_bits)
        for host in self.hosts.values():
            result = host.receive(received_frame)
            if result and result.dst == host.address:
                host.last_received = result

    def send_simultaneously(self, frames: List[EncodedFrame]) -> None:
        """Attempt to transmit multiple frames at once to trigger collision handling."""
        signals = [modulate(frame.to_bits()) for frame in frames]
        if len(signals) < 2:
            raise ValueError("Need at least two frames to collide")
        combined = [sum(values) for values in zip(*signals)]
        with self._channel_lock:
            transmitted = self.cable.transmit(combined)
        # Collision corrupts data, so demodulation raises an error or produces garbage.
        recovered_bits = demodulate(transmitted)
        try:
            EncodedFrame.from_bits(recovered_bits)
        except Exception as exc:  # noqa: BLE001
            raise CollisionError("Collision detected; transmission corrupted") from exc
        raise CollisionError("Collision detected; transmission corrupted")

    def _build_frame(self, src: int, dst: int, message: str) -> EncodedFrame:
        if src not in self.hosts:
            raise ValueError(f"Unknown source host {src}")
        if dst not in self.hosts and dst != 255:
            raise ValueError(f"Unknown destination host {dst}")
        data_bits = string_to_bits(message)
        parity_bits = add_parity_bits(data_bits)
        payload_length_bytes = len(parity_bits) // 9
        if payload_length_bytes >= 2**16:
            raise ValueError("Payload too large")
        return EncodedFrame(src=src, dst=dst, payload_bits=parity_bits)
