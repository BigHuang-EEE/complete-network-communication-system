"""
Cable (信道) 仿真类
这是课程提供的用于模拟物理传输介质的基础设施。
"""
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple


class Cable:
    """
    Cable/Channel 仿真类
    功能：
    1.传输模拟信号
    2.添加信道噪声
    3.模拟信号衰减
    4.调试模式：可视化信号波形，不建议使用，我们有提出新的画图方法
    """
    
    def __init__(self, 
                 length: float = 100.0,
                 attenuation: float = 0.1,
                 noise_level: float = 0.05,
                 debug_mode: bool = False,
                 history_size: int = 10):
        """
        初始化 Cable
        
        参数说明:
            length: 电缆长度 (meters)
            attenuation: 衰减系数 (dB/m)
            noise_level: 噪声水平 (用于添加 Gaussian white noise)
            debug_mode: 调试模式，启用后会显示信号波形，关闭就好了
            history_size: 保存多少次最近的传输，用于绘制历史上的跳跃 (hops)
        """
        self.length = length
        self.attenuation = attenuation
        self.noise_level = noise_level
        self.debug_mode = debug_mode
        self._history_size = history_size
        self._plot_counter = 0
        
        # 存储最近的传输信号 (for debugging)
        self.last_input_signal: Optional[np.ndarray] = None
        self.last_output_signal: Optional[np.ndarray] = None
        self.waveform_history: List[Tuple[np.ndarray, np.ndarray]] = []
        
    def transmit(self, signal: np.ndarray) -> np.ndarray:
        """
        通过电缆传输信号
        
        参数说明:
            signal: 输入的模拟信号 (numpy 数组)
            
        返回值:
            经过信道后的信号（包含衰减和噪声）
        """
        # 存储输入信号 for debugging
        self.last_input_signal = signal.copy()
        
        # 1. 应用 attenuation
        # 使用指数衰减模型: A(d) = A0 * exp(-α * d)
        attenuation_factor = np.exp(-self.attenuation * self.length / 100)
        attenuated_signal = np.array(signal) * attenuation_factor
        
        # 2. 添加 Gaussian white noise
        if self.noise_level > 0:
            noise = np.random.normal(0, self.noise_level, len(signal))
            noisy_signal = attenuated_signal + noise
        else:
            noisy_signal = attenuated_signal
        
        # 存储输出信号 for debugging
        self.last_output_signal = noisy_signal.copy()
        self._record_history()
        
        # 画波形图 if debug mode is enabled
        if self.debug_mode:
            self.plot_signals(window_title="Cable Debug Waveform")
        
        return noisy_signal
    
    def get_propagation_delay(self, signal_speed: float = 2e8) -> float:
        """
        计算传播时延
        
        参数说明:
            signal_speed: Signal propagation speed (m/s)
                         Default is 2/3 of light speed (typical for fiber optics)
            
        返回值:
            Propagation delay (seconds)
        """
        return self.length / signal_speed
    
    def _record_history(self) -> None:
        """存储 a copy of 最近的传输 for later plotting."""
        if self.last_input_signal is None or self.last_output_signal is None:
            return
        self.waveform_history.append((self.last_input_signal, self.last_output_signal))
        if len(self.waveform_history) > self._history_size:
            self.waveform_history.pop(0)

    def plot_signals(self, max_samples: int = 1000, history_index: Optional[int] = None,
                     window_title: Optional[str] = None):
        """
        画波形图 (debug feature)
        
        参数说明:
            max_samples: 最大显示样本数
            history_index: 历史索引以绘制特定的传输记录，可选的
            window_title: 窗口标题，可选的
        """
        if history_index is not None:
            if not self.waveform_history:
                print("No signal data available")
                return
            try:
                input_signal, output_signal = self.waveform_history[history_index]
            except IndexError:
                print(f"No signal data available at history index {history_index}")
                return
        else:
            if self.last_input_signal is None or self.last_output_signal is None:
                print("No signal data available")
                return
            input_signal = self.last_input_signal
            output_signal = self.last_output_signal
        
        # 限制显示样本数
        input_signal = input_signal[:max_samples]
        output_signal = output_signal[:max_samples]
        
        # 画图
        self._plot_counter += 1
        title = window_title or f"Cable Waveform {self._plot_counter}"
        plt.figure(figsize=(12, 6), num=title)
        plt.clf()
        
        # Subplot 1: Input signal
        plt.subplot(2, 1, 1)
        plt.plot(input_signal, 'b-', linewidth=0.5)
        plt.title('Input Signal')
        plt.xlabel('Sample')
        plt.ylabel('Amplitude')
        plt.grid(True, alpha=0.3)
        
        # Subplot 2: Output signal
        plt.subplot(2, 1, 2)
        plt.plot(output_signal, 'r-', linewidth=0.5)
        plt.title(f'Output Signal - Attenuation={self.attenuation}, Noise={self.noise_level}')
        plt.xlabel('Sample')
        plt.ylabel('Amplitude')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def get_signal_stats(self) -> dict:
        """
        获取信号统计数据 (debug feature)
        
        返回值:
            Dictionary containing signal statistics
        """
        if self.last_input_signal is None or self.last_output_signal is None:
            return {}
        
        stats = {
            'input_mean': np.mean(self.last_input_signal),
            'input_std': np.std(self.last_input_signal),
            'input_max': np.max(self.last_input_signal),
            'input_min': np.min(self.last_input_signal),
            'output_mean': np.mean(self.last_output_signal),
            'output_std': np.std(self.last_output_signal),
            'output_max': np.max(self.last_output_signal),
            'output_min': np.min(self.last_output_signal),
            'snr_db': self._calculate_snr()
        }
        
        return stats
    
    def _calculate_snr(self) -> float:
        """
        计算 Signal-to-Noise Ratio (SNR)
        
        返回值:
            SNR in dB
        """
        if self.last_input_signal is None or self.last_output_signal is None:
            return 0.0
        
        # Noise = Output - Input * attenuation_factor
        attenuation_factor = np.exp(-self.attenuation * self.length / 100)
        expected_output = self.last_input_signal * attenuation_factor
        noise = self.last_output_signal - expected_output
        
        signal_power = np.mean(expected_output ** 2)
        noise_power = np.mean(noise ** 2)
        
        if noise_power == 0:
            return float('inf')
        
        snr = 10 * np.log10(signal_power / noise_power)
        return snr
    
    def __str__(self) -> str:
        return (f"Cable(length={self.length}m, "
                f"attenuation={self.attenuation}dB/m, "
                f"noise_level={self.noise_level}, "
                f"debug={self.debug_mode})")


# ============================================================================
# Usage Example
# ============================================================================

def example_usage():
    """Example: How to use the Cable class"""
    
    print("=" * 60)
    print("Cable Class Usage Example")
    print("=" * 60)
    
    # Create cable (with debug mode enabled)
    cable = Cable(
        length=100,           # 100 meters
        attenuation=0.1,      # Attenuation coefficient
        noise_level=0.05,     # Noise level
        debug_mode=True      # Set to True to see waveforms
    )
    
    print(f"\n{cable}")
    
    # Generate a simple sine wave signal as an example
    sample_rate = 44100  # Sampling rate
    duration = 0.01      # Duration (seconds)
    frequency = 1000     # Frequency (Hz)
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    signal = np.sin(2 * np.pi * frequency * t)
    
    print(f"\nTransmitting signal:")
    print(f"  Number of samples: {len(signal)}")
    print(f"  Frequency: {frequency} Hz")
    
    # Transmit through cable
    received_signal = cable.transmit(signal)
    
    print(f"\nReceived signal:")
    print(f"  Number of samples: {len(received_signal)}")
    print(f"  Propagation delay: {cable.get_propagation_delay():.9f} seconds")
    
    # Get statistics
    stats = cable.get_signal_stats()
    print(f"\nSignal statistics:")
    print(f"  Input signal mean: {stats['input_mean']:.6f}")
    print(f"  Output signal mean: {stats['output_mean']:.6f}")
    print(f"  SNR: {stats['snr_db']:.2f} dB")
    
    # Uncomment below to view waveforms
    # cable.plot_signals()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    example_usage()
