import pytest

from cable import Cable
from communication import add_parity_bits, bits_to_string, demodulate, modulate, string_to_bits, strip_parity_bits
from network import CollisionError, MultiHostNetwork


def test_point_to_point_round_trip():
    message = "Hello"
    bits = string_to_bits(message)
    encoded = add_parity_bits(bits)
    signal = modulate(encoded)
    cable = Cable(noise_level=0.01)
    received_signal = cable.transmit(signal)
    recovered_bits = demodulate(received_signal)
    decoded = strip_parity_bits(recovered_bits)
    assert bits_to_string(decoded) == message


def test_point_to_point_long_message():
    message = "Data communication across layers"
    bits = string_to_bits(message)
    encoded = add_parity_bits(bits)
    signal = modulate(encoded)
    cable = Cable(length=200, attenuation=0.05, noise_level=0.02)
    received_signal = cable.transmit(signal)
    recovered_bits = demodulate(received_signal)
    decoded = strip_parity_bits(recovered_bits)
    assert bits_to_string(decoded) == message


def test_multihost_routing_and_addressing():
    network = MultiHostNetwork(Cable(noise_level=0.01))
    host_a = network.register_host(1)
    host_b = network.register_host(2)
    host_c = network.register_host(3)

    host_a.send(3, "Ping from A")

    assert host_c.last_received is not None
    assert host_c.last_received.payload == "Ping from A"
    assert host_c.last_received.src == 1
    assert host_c.last_received.dst == 3
    assert host_b.last_received is None


def test_collision_detection():
    network = MultiHostNetwork(Cable(noise_level=0.0))
    host_a = network.register_host(10)
    host_b = network.register_host(20)

    frame_a = network._build_frame(host_a.address, host_b.address, "hello")
    frame_b = network._build_frame(host_b.address, host_a.address, "world")

    with pytest.raises(CollisionError):
        network.send_simultaneously([frame_a, frame_b])
