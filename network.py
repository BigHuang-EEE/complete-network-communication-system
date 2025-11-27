from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, List, Optional

from cable import Cable
from communication import (
    EncodedFrame,
    add_parity_bits,
    bits_to_string,
    demodulate,
    modulate,
    string_to_bits,
    strip_parity_bits,
)


class CollisionError(RuntimeError):
    """Raised when two hosts attempt to transmit simultaneously."""


# 接收到的消息 ReceivedMessage 对象
@dataclass
class ReceivedMessage:
    src: int
    dst: int
    payload: str


# 构建帧：把字符串转换成带校验位的比特流
def build_frame(src: int, dst: int, message: str) -> EncodedFrame:
    data_bits = string_to_bits(message)
    # 添加校验位
    parity_bits = add_parity_bits(data_bits)
    # 计算字节长度以防止过大的消息传输
    payload_length_bytes = len(parity_bits) // 9
    if payload_length_bytes >= 2**16:
        raise ValueError("Payload too large")
    return EncodedFrame(src=src, dst=dst, payload_bits=parity_bits)


# 先把校验位剥掉并做校验，然后还原字符串
def recover_payload(payload_bits: List[int]) -> str:
    return bits_to_string(strip_parity_bits(payload_bits))


class PhysicalChannel:
    # 对共享电缆的一层轻量抽象。
    # 它把调制，传输帧，解调以及信道锁(channel lock)封装起来。

    def __init__(self, cable: Optional[Cable] = None, lock: Optional[threading.Lock] = None) -> None:
        self.cable = cable or Cable()
        # 信道锁，确保同一时间只有一个传输在进行
        self.lock = lock or threading.Lock()

    def transmit_frame(self, frame: EncodedFrame) -> EncodedFrame:
        recovered_bits = self.transmit_bits(frame.to_bits())
        return EncodedFrame.from_bits(recovered_bits)

    def transmit_bits(self, bits: List[int]) -> List[int]:
        analog_signal = modulate(bits)
        with self.lock:
            transmitted = self.cable.transmit(analog_signal)
        return demodulate(transmitted)


# 主机的发送和接收功能
class Host:
    def __init__(self, address: int, router: "Router") -> None:
        self.address = address
        self.router = router
        self.last_received: Optional[ReceivedMessage] = None

    # 主机发送消息到另一个主机，通过路由器转发
    def send(self, destination: int, message: str) -> None:
        self.router.send_from_host(self.address, destination, message)

    # 主机接收帧：
    # 检查是否发给自己
    # 剥离校验位并还原字符串
    # 构造一个 ReceivedMessage 对象返回
    def receive(self, frame: EncodedFrame) -> Optional[ReceivedMessage]:
        if frame.dst not in (self.address, 255):
            return None
        data_bits = strip_parity_bits(frame.payload_bits)
        payload = bits_to_string(data_bits)
        return ReceivedMessage(src=frame.src, dst=frame.dst, payload=payload)


# 专门维护主机地址和路由表
class AddressTable:
    def __init__(self) -> None:
        self.hosts: Dict[int, Host] = {}
        # 简单的直连路由表：目标地址就是下一跳地址
        self.routing_table: Dict[int, int] = {}

    def register(self, host: Host) -> None:
        if host.address in self.hosts:
            raise ValueError(f"Host {host.address} already registered")
        self.hosts[host.address] = host
        self.routing_table[host.address] = host.address

    def require_known(self, address: int) -> None:
        if address not in self.hosts:
            raise ValueError(f"Unknown host {address}")

    # 根据目标地址解析出目标主机（列表）
    # （查路由表，但这里面可能存在路由表项缺失和未注册主机的问题，
    # 所以用if语句排除）
    def resolve_targets(self, dst: int) -> List[Host]:
        if dst == 255:
            return list(self.hosts.values())
        if dst not in self.routing_table:
            raise ValueError(f"Unknown destination host {dst}")
        next_hop = self.routing_table[dst]
        if next_hop not in self.hosts:
            raise ValueError(f"Routing table points to missing host {next_hop}")
        return [self.hosts[next_hop]]


# 路由器
class Router:
    def __init__(self, cable: Optional[Cable] = None) -> None:
        self.channel = PhysicalChannel(cable=cable)
        self.addresses = AddressTable()
        # 为了兼容旧的调用者，使用了两个属性指向同一个对象
        # （原来PhysicalChannel也写在router里了，但这样显然
        # 不太符合直觉和实际情况）
        self.cable = self.channel.cable
        self._channel_lock = self.channel.lock

    # 注册主机到路由器
    def register_host(self, address: int) -> Host:
        host = Host(address, self)
        self.addresses.register(host)
        return host

    # 从主机发送消息，通过路由器转发
    def send_from_host(self, src: int, dst: int, message: str) -> None:
        self.addresses.require_known(src)
        if dst != 255:
            self.addresses.require_known(dst)

        # 主机到路由器: 构建帧并通过物理信道传输
        uplink_frame = build_frame(src, dst, message)
        ingress_frame = self.channel.transmit_frame(uplink_frame)

        # 路由器处理接收到的帧：还原字符串并查找目标主机
        recovered_payload = recover_payload(ingress_frame.payload_bits)
        # 目标主机（列表）
        targets = self.addresses.resolve_targets(ingress_frame.dst)

        # 路由器到目标主机
        for host in targets:
            # 广播或者单播
            outgoing_dst = 255 if dst == 255 else host.address
            # 构建新的帧
            outbound_frame = build_frame(ingress_frame.src, outgoing_dst, recovered_payload)
            # 新的帧通过物理信道传输到目标主机
            delivered_frame = self.channel.transmit_frame(outbound_frame)
            # 主机尝试接收帧
            result = host.receive(delivered_frame)
            if result:
                # 主机成功接收帧，更新最后接收的消息
                host.last_received = result


class MultiHostNetwork:
    # 多主机网络
    # 但没有实际网络逻辑
    # 所有工作交给 Router 等类完成
    # MultiHostNetwork 只负责维持旧接口
    # 确保旧测试不需要修改
    # 做一个这样的类，也方便测试，有一个多主机网络的感觉，便于setup
    # 当然，后续你要是觉得麻烦，你也可以改了测试代码直接用 Router 就行

    def __init__(self, cable: Optional[Cable] = None) -> None:
        self.router = Router(cable=cable)

    def register_host(self, address: int) -> Host:
        return self.router.register_host(address)

    def send_message(self, src: int, dst: int, message: str) -> None:
        self.router.send_from_host(src, dst, message)
