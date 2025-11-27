from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
import math


def string_to_bits(text: str) -> List[int]:
    data = text.encode("utf-8")
    bits: List[int] = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def bits_to_string(bits: Iterable[int]) -> str:
    bit_list = list(bits)
    if len(bit_list) % 8 != 0:
        raise ValueError("Bit stream length must be a multiple of 8")
    bytes_out = bytearray()
    for i in range(0, len(bit_list), 8):
        value = 0
        for bit in bit_list[i : i + 8]:
            value = (value << 1) | bit
        bytes_out.append(value)
    return bytes_out.decode("utf-8", errors="replace")


def add_parity_bits(bits: Iterable[int]) -> List[int]:
    bit_list = list(bits)
    if len(bit_list) % 8 != 0:
        raise ValueError("Parity calculation expects data in full bytes")
    result: List[int] = []
    for i in range(0, len(bit_list), 8):
        chunk = bit_list[i : i + 8]
        parity = sum(chunk) % 2
        result.extend(chunk + [parity])
    return result


def strip_parity_bits(bits: Iterable[int]) -> List[int]:
    bit_list = list(bits)
    if len(bit_list) % 9 != 0:
        raise ValueError("Parity validation expects 9-bit blocks")
    data_bits: List[int] = []
    for i in range(0, len(bit_list), 9):
        chunk = bit_list[i : i + 9]
        payload = chunk[:8]
        parity_bit = chunk[8]
        if sum(payload) % 2 != parity_bit:
            raise ValueError("Parity check failed")
        data_bits.extend(payload)
    return data_bits


SAMPLES_PER_BIT = 20
AMPLITUDE_HIGH = 1.0
AMPLITUDE_LOW = 0.1
THRESHOLD = 0.3


def modulate(bits: Iterable[int], samples_per_bit: int = SAMPLES_PER_BIT) -> List[float]:
    bit_list = list(bits)
    signal_length = len(bit_list) * samples_per_bit
    signal = [0.0 for _ in range(signal_length)]
    for i, bit in enumerate(bit_list):
        amplitude = AMPLITUDE_HIGH if bit else AMPLITUDE_LOW
        start = i * samples_per_bit
        for j in range(samples_per_bit):
            phase = 2 * math.pi * j / samples_per_bit
            signal[start + j] = amplitude * math.sin(phase)
    return signal


def demodulate(signal: List[float], samples_per_bit: int = SAMPLES_PER_BIT) -> List[int]:
    bit_count = len(signal) // samples_per_bit
    bits = []
    for i in range(bit_count):
        start = i * samples_per_bit
        segment = signal[start:start + samples_per_bit]

        # 计算幅度绝对值的平均
        avg_amplitude = sum(abs(x) for x in segment) / samples_per_bit

        bit = 1 if avg_amplitude > THRESHOLD else 0
        bits.append(bit)

    return bits


# 帧的编码和解码以及帧的构造（8位src+8位dst+16位length+9*消息字节数）
@dataclass
class EncodedFrame:
    src: int
    dst: int
    payload_bits: List[int]

    # 把帧转化为位列表
    def to_bits(self) -> List[int]:
        src_bits = _int_to_bits(self.src)
        dst_bits = _int_to_bits(self.dst)
        length_bits = _int_to_bits(len(self.payload_bits) // 8, width=16)
        return dst_bits + src_bits + length_bits + self.payload_bits

    # 解析帧从位列表
    @staticmethod
    def from_bits(bits: Iterable[int]) -> "EncodedFrame":
        bit_list = list(bits)
        if len(bit_list) < 8 * 2 + 16:
            raise ValueError("Frame too short")
        dst = _bits_to_int(bit_list[0:8])
        src = _bits_to_int(bit_list[8:16])
        length = _bits_to_int(bit_list[16:32])
        payload_bits = bit_list[32 : 32 + length * 9]
        return EncodedFrame(src=src, dst=dst, payload_bits=payload_bits)


# 整数化为整数列表
def _int_to_bits(value: int, width: int = 8) -> List[int]:
    if value < 0 or value >= 2**width:
        raise ValueError("Integer out of range for bit conversion")
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def _bits_to_int(bits: Iterable[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value
