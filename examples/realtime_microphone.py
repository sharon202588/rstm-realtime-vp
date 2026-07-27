"""
示例脚本：使用麦克风音频实时驱动豆包 WebSocket。

这个脚本会：
1. 建立豆包实时语音 WebSocket 连接。
2. 启动会话（包含 TTS 配置）。
3. 通过本地麦克风采集 PCM 数据并实时推送给豆包。
4. 在后台打印服务器返回的事件（ASR、TTS、状态等）。

使用前请确保：
- 安装依赖：`pip install sounddevice`
- 环境变量或 `.env` 中配置了 DOUBAO_REALTIME_APP_ID 和 DOUBAO_REALTIME_ACCESS_KEY。
- 有可用的麦克风设备。
"""

import asyncio
import sys
from typing import Optional

import sounddevice as sd

from doubao.websocket_client import DoubaoWebSocketClient

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_DURATION_SECONDS = 0.2
BLOCK_SIZE = int(SAMPLE_RATE * BLOCK_DURATION_SECONDS)


async def print_server_event(message: dict):
    """简要打印来自豆包的事件类型 / 简要信息。"""
    msg_type = message.get("type")
    if not msg_type:
        return

    prefix = f"[Doubao WS] {msg_type}"
    if msg_type == "ASRInfo":
        print(f"{prefix} -> ASR started")
    elif msg_type == "ASRResponse":
        print(f"{prefix} -> ASR results: {message.get('results', [])}")
    elif msg_type == "TTSResponse":
        data = message.get("data")
        if data:
            print(f"{prefix} -> TTS audio bytes: {len(data)}")
    elif msg_type == "TTSEnded":
        print(f"{prefix} -> TTS ended")
    else:
        print(f"{prefix} -> payload keys: {list(message.keys())}")


async def capture_and_stream(mic_queue: asyncio.Queue, stop_evt: asyncio.Event):
    """启动麦克风采集并把 PCM 块推送到异步队列。"""
    loop = asyncio.get_running_loop()

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"[mic status] {status}")
        loop.call_soon_threadsafe(mic_queue.put_nowait, indata.tobytes())

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=CHANNELS,
        callback=audio_callback,
    )

    with stream:
        print(f"开始采集麦克风音频（{SAMPLE_RATE}Hz, {CHANNELS}ch, int16）...")
        print("按 Enter 停止录音")
        await stop_evt.wait()


async def audio_sender(
    client: DoubaoWebSocketClient,
    mic_queue: asyncio.Queue,
    stop_evt: asyncio.Event,
):
    """从队列读取 PCM 并通过 Doubao WebSocket 推送。"""
    while True:
        chunk: Optional[bytes] = await mic_queue.get()
        if chunk is None:
            break

        await client.send_audio(chunk)

        if stop_evt.is_set():
            break


async def monitor_user_input(stop_evt: asyncio.Event, mic_queue: asyncio.Queue):
    """等待用户按 Enter，标记停止并通知音频发送器退出。"""
    await asyncio.to_thread(sys.stdin.readline)
    stop_evt.set()
    await mic_queue.put(None)


async def main():
    """入口：初始化 WebSocket，启动音频流并保持监听。"""
    client = DoubaoWebSocketClient()
    await client.connect()
    await client.start_session(
        system_prompt="你是一位需要与医生沟通的虚拟患者。",
        bot_name="模拟患者",
        speaking_style="neutral",
        tts_config={
            "speaker": "zh_male_yunzhou_jupiter_bigtts",
            "audio_config": {"channel": 1, "format": "pcm", "sample_rate": 24000},
        },
        input_mod="audio",
        model="O",
    )

    stop_evt = asyncio.Event()
    mic_queue: asyncio.Queue[Optional[bytes]] = asyncio.Queue()

    listener_task = asyncio.create_task(client.listen(callback=print_server_event))
    sender_task = asyncio.create_task(audio_sender(client, mic_queue, stop_evt))
    user_monitor = asyncio.create_task(monitor_user_input(stop_evt, mic_queue))

    try:
        await capture_and_stream(mic_queue, stop_evt)
    finally:
        await user_monitor
        await sender_task
        await client.finish_session()
        await client.finish_connection()
        await client.disconnect()
        listener_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n已收到中断信号，退出。")
