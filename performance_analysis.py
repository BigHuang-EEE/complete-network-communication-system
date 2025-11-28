from __future__ import annotations

import statistics
import time
from typing import Dict

from cable import Cable
from network import MultiHostNetwork, build_frame


def measure_latency(network: MultiHostNetwork, src: int, dst: int, message: str, trials: int = 20) -> Dict[str, float]:
    durations = []
    for _ in range(trials):
        start = time.perf_counter()
        network.send_message(src, dst, message)
        durations.append(time.perf_counter() - start)
    return {
        "avg_s": statistics.mean(durations),
        "min_s": min(durations),
        "max_s": max(durations),
    }


def measure_throughput(network: MultiHostNetwork, src: int, dst: int, message: str, iterations: int = 100) -> Dict[str, float]:
    frame_bits = len(build_frame(src, dst, message).to_bits())
    payload_bits = len(message.encode("utf-8")) * 8

    start = time.perf_counter()
    for _ in range(iterations):
        network.send_message(src, dst, message)
    elapsed = time.perf_counter() - start

    return {
        "elapsed_s": elapsed,
        "payload_bps": payload_bits * iterations / elapsed,
        "wire_bps": frame_bits * 2 * iterations / elapsed,  # two hops: host->router and router->host
    }


def main() -> None:
    # 使用更长的链路让传播时延变得可观测
    cable = Cable(length=500_000, attenuation=0.02, noise_level=0.01)
    network = MultiHostNetwork(cable=cable)

    host_a = network.register_host(1)
    host_b = network.register_host(2)

    print(f"Per-hop propagation delay: {cable.get_propagation_delay():.6f} s (length={cable.length} m)")

    latency_message = "ping"
    throughput_message = "Performance test payload " * 40
    throughput_iterations = 200

    # 先跑一轮预热，避免首次调用带来的偏差
    network.send_message(host_a.address, host_b.address, "warmup")

    latency_stats = measure_latency(network, host_a.address, host_b.address, latency_message, trials=50)
    throughput_stats = measure_throughput(
        network, host_a.address, host_b.address, throughput_message, iterations=throughput_iterations
    )

    print("\nLatency stats (one-way, wall clock):")
    print(f"  avg: {latency_stats['avg_s'] * 1000:.3f} ms")
    print(f"  min: {latency_stats['min_s'] * 1000:.3f} ms")
    print(f"  max: {latency_stats['max_s'] * 1000:.3f} ms")

    print("\nThroughput (sequential sends):")
    print(f"  payload throughput: {throughput_stats['payload_bps'] / 1e6:.3f} Mb/s")
    print(f"  on-wire throughput: {throughput_stats['wire_bps'] / 1e6:.3f} Mb/s")
    total_payload_bytes = len(throughput_message.encode("utf-8")) * throughput_iterations
    print(f"  total time for {total_payload_bytes / 1024:.1f} KB payload: {throughput_stats['elapsed_s']:.3f} s")


if __name__ == "__main__":
    main()
