# Complete Network Communication System

模拟从物理层到应用层的简化通信流程，覆盖点对点和多主机两级需求，带奇偶校验、帧封装、共享信道串行化，以及传播时延/吞吐观察。
网络通信系统基于类 circuit switching 的哲学

## 快速开始
- 依赖：Python 3，`numpy`，`matplotlib`（用于 `Cable.plot_signals`）。可直接 `python -m pip install numpy matplotlib`。
- 进入仓库目录后可直接跑示例：
  - `python test_p2p.py`：Level 1 点对点演示（字符串→比特→调制→Cable→解调→校验→还原）。
  - `python test_multihost.py`：Level 2 多主机演示（三个主机，单播与并发发送）。
  - `python performance_analysis.py`：带传播时延的吞吐/时延分析（使用更长链路便于观测，需本地有 GUI 才能弹出波形）。

## 帧格式与校验
- 帧结构：`dst(8) | src(8) | length(16) | payload_bits`，其中 `payload_bits` 为每字节 8 数据位 + 1 奇偶校验位。
- 奇偶校验：`add_parity_bits` 添加奇校验位，`strip_parity_bits` 校验失败会抛出 `ValueError`。
- 调制参数：默认 `SAMPLES_PER_BIT=20`，`AMPLITUDE_HIGH/LOW=1.0/0.1`，`THRESHOLD=0.3`，必要时可在 `communication.py` 调整。

## Level 1：点对点通信（30 分）
- 数据→比特流：`communication.string_to_bits`
- 调制：`communication.modulate`
- 传输：`Cable.transmit`（添加衰减/噪声，可视化调试）
- 解调：`communication.demodulate`
- 数据恢复：`communication.strip_parity_bits` + `communication.bits_to_string`
- 错误检测：每字节附加奇偶位（`add_parity_bits` / `strip_parity_bits`）

## Level 2：多主机通信（30 分）
- 地址区分与路由：`network.AddressTable` 保存主机和直连路由；`Router` 使用 `resolve_targets` 选择目标（支持单播与 255 广播）。
- 封装/转发：`build_frame`/`recover_payload` 负责帧编解码；`Router.send_from_host` 负责校验地址、选择目标、重封帧并下发。
- 共享信道与并发：`PhysicalChannel` 将调制/解调与信道锁包装在一起，`transmit_bits` 内使用锁串行化，避免并发碰撞。
- 物理层仍通过 `Cable` 模拟模拟信号：比特→调制波形→Cable→解调比特。

## 调试与参数
- `Cable(length, attenuation, noise_level, debug_mode)`：可配置链路长度、衰减和噪声；`plot_signals` 支持查看最近多跳历史波形（`history_index` 控制）。
- 传播时延：`Cable.get_propagation_delay` 在 `PhysicalChannel.transmit_bits` 中用于 `time.sleep` 模拟传播时间，性能测试会让长度调大以便观测。
- 信道锁：`PhysicalChannel.lock` 串行化共享介质的发送，示例里用线程屏障模拟并发。

## 组件速览
- `cable.py`：模拟物理信道，提供衰减、噪声和波形绘制。
- `communication.py`：比特/字符串互转，奇偶校验添加/校验，调制/解调，帧结构 `EncodedFrame`。
- `network.py`：多主机网络，包含 `Host`、`Router`、`PhysicalChannel`、`AddressTable` 以及辅助封装/恢复函数。

## 测试与复现
- 运行 `python test_p2p.py`（点对点）、`python test_multihost.py`（多主机单播 + 并发串行化）。这两段脚本对应评分需求中的“成功传输简单/长消息”“区分主机并正确路由”等项。
- 运行 `python performance_analysis.py` 查看长链路下的延迟和吞吐，默认会先做一轮预热以排除冷启动误差。
