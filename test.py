from cable import Cable
from communication import add_parity_bits, bits_to_string, demodulate, modulate, string_to_bits, strip_parity_bits
from network import CollisionError, MultiHostNetwork

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

# Sender
message = "Hello, this is guolab speaking. Data communication is achieved through our efforts!"
bits = string_to_bits(message)
signal = modulate(bits)
# Transmission
cable = Cable()
received_signal = cable.transmit(signal)
# Receiver
received_bits = demodulate(received_signal)
received_message = bits_to_string(received_bits)
print(f"Sent: {message}")
print(f"Received: {received_message}")