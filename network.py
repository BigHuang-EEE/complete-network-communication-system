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
