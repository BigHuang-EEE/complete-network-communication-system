import threading
from typing import Tuple

from network import MultiHostNetwork


def setup_hosts(network: MultiHostNetwork) -> Tuple:
    """Register three hosts for the demo."""
    host_a = network.register_host(1)
    host_b = network.register_host(2)
    host_c = network.register_host(3)
    return host_a, host_b, host_c


def demo_unicast(host_a, host_b, host_c) -> None:
    print("=== Unicast messages ===")
    host_a.send(2, "Hello B, this is A.")
    if host_b.last_received:
        print(f"B received from {host_b.last_received.src}: {host_b.last_received.payload}")

    host_b.send(3, "Hi C, B here.")
    if host_c.last_received:
        print(f"C received from {host_c.last_received.src}: {host_c.last_received.payload}")


def demo_concurrent_success(host_a, host_b, host_c) -> None:
    """
    Simulate two hosts transmitting at (almost) the same time over the shared cable.
    The channel lock in MultiHostNetwork serializes access so both messages arrive correctly.
    """
    print("\n=== Concurrent transmissions (expected success) ===")
    barrier = threading.Barrier(2)

    def send_from_a():
        barrier.wait()
        host_a.send(3, "Parallel from A to C.")

    def send_from_b():
        barrier.wait()
        host_b.send(1, "Parallel from B to A.")

    thread_a = threading.Thread(target=send_from_a)
    thread_b = threading.Thread(target=send_from_b)
    thread_a.start()
    thread_b.start()
    thread_a.join()
    thread_b.join()

    if host_c.last_received:
        print(f"C received from {host_c.last_received.src}: {host_c.last_received.payload}")
    if host_a.last_received:
        print(f"A received from {host_a.last_received.src}: {host_a.last_received.payload}")


def main() -> None:
    network = MultiHostNetwork()
    host_a, host_b, host_c = setup_hosts(network)
    demo_unicast(host_a, host_b, host_c)
    demo_concurrent_success(host_a, host_b, host_c)


if __name__ == "__main__":
    main()
