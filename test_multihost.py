import threading
from typing import Optional, Tuple

from network import MultiHostNetwork


def plot_latest_waveform(cable, label: str, history_index: Optional[int] = None) -> None:
    # 绘制某一次特定的跳跃；当提供了 history_index 时，我们就从历史记录中读取该次跳跃的数据。
    if history_index is not None and not cable.waveform_history:
        print("No waveform available to plot yet.")
        return
    if history_index is None and (cable.last_input_signal is None or cable.last_output_signal is None):
        print("No waveform available to plot yet.")
        return
    # print(f"\nPlotting channel waveforms: {label}")
    # 注释掉是因为这个打印本意是未来说明情况，却让终端太眼花缭乱
    cable.plot_signals(history_index=history_index, window_title=label)


def setup_hosts(network: MultiHostNetwork) -> Tuple:
    # 注册三个主机作为演示
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


# 同时发送的演示
def demo_concurrent_success(host_a, host_b, host_c) -> None:
    # 模拟两个主机在共享电缆上（几乎）同时发送数据。
    # 信道锁会将访问串行化，从而确保两条消息都能正确到达。
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
    channel_cable = network.router.cable
    host_a, host_b, host_c = setup_hosts(network)
    demo_unicast(host_a, host_b, host_c)
    plot_latest_waveform(channel_cable, "unicast last hop (Router -> Host)", history_index=-1)
    plot_latest_waveform(channel_cable, "unicast previous hop (Host -> Router)", history_index=-2)
    demo_concurrent_success(host_a, host_b, host_c)
    plot_latest_waveform(channel_cable, "after concurrent transmissions")


if __name__ == "__main__":
    main()
