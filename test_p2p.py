import time

from cable import Cable
from communication import add_parity_bits, bits_to_string, demodulate, modulate, string_to_bits, strip_parity_bits
from network import CollisionError, MultiHostNetwork

# # Transmit simple strings
# # Sender
# message = "Hello"
# bits = string_to_bits(message)
# signal = modulate(bits)
# # Transmission
# cable = Cable()
# received_signal = cable.transmit(signal)
# # Receiver
# received_bits = demodulate(received_signal)
# received_message = bits_to_string(received_bits)
# print(f"Sent: {message}")
# print(f"Received: {received_message}")

# # Transmit longer messages
# # Sender
# message = "Hello, this is guolab speaking. Data communication is achieved through our efforts!"
# bits = string_to_bits(message)
# signal = modulate(bits)
# # Transmission
# cable = Cable()
# received_signal = cable.transmit(signal)
# # Receiver
# received_bits = demodulate(received_signal)
# received_message = bits_to_string(received_bits)
# print(f"Sent: {message}")
# print(f"Received: {received_message}")

# Transmit longer messages with basic error detection mechanism
# 演示点对点通信，并在接收端校验奇偶校验位以检测错误
message = "Hello, this is guolab speaking. Data communication is achieved through our efforts!"
# 发送端：数据 -> 比特流 -> 添加校验位 -> 调制
data_bits = string_to_bits(message)
payload_with_parity = add_parity_bits(data_bits)
signal = modulate(payload_with_parity)
# 传输
cable = Cable()
time.sleep(cable.get_propagation_delay())
received_signal = cable.transmit(signal)
# 绘制传输前后（模拟信道输入/输出）的波形
cable.plot_signals(window_title="P2P channel waveform")
# 接收端：解调 -> 校验奇偶位 -> 还原字符串
received_bits = demodulate(received_signal)
# 如需模拟错误检测，可取消下一行注释以翻转一个比特
# received_bits[0] ^= 1
try:
    verified_bits = strip_parity_bits(received_bits)
    received_message = bits_to_string(verified_bits)
    print(f"Sent: {message}")
    print(f"Received: {received_message}")
except ValueError as exc:
    # 校验失败时，说明检测到传输错误
    print("Parity check failed, transmission error detected:", exc)
