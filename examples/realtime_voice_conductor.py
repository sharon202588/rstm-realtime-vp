"""
实时语音指挥脚本：
麦克风 -> Doubao 实时语音 API -> CPAS Lite 评分 -> RSTM 状态更新 -> 风格注入 -> 下一轮回复
"""

import asyncio
import io
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import sounddevice as sd

from doubao.rest_client import DoubaoRESTClient, ReasoningEffort
from doubao.websocket_client import DoubaoWebSocketClient
from rstm.state_manager import RSTMStateManager
from rstm.style_mapper import StyleMapper

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SECONDS = 0.12  # slots smaller for faster VAD commits
SILENCE_THRESHOLD = 600
BLOCK_SIZE = int(SAMPLE_RATE * BLOCK_SECONDS)


class RealtimeVoiceConductor:
    """协调整个实时语音流程的控制器。"""

    def __init__(
        self,
        ark_api_key: Optional[str] = None,
        doubao_realtime_app_id: Optional[str] = None,
        doubao_realtime_access_key: Optional[str] = None,
        initial_cci: float = 0.0,
        initial_state: float = -0.25,
        state_file: Optional[str] = "dialogue_state.json",
    ):
        project_root = Path(__file__).parent.parent
        self.patient_profile_path = project_root / "specs" / "patient_profile.md"
        self.grader_prompt_path = project_root / "specs" / "grader_prompt.md"

        self.patient_profile = self.patient_profile_path.read_text(encoding="utf-8")
        self.grader_prompt = self.grader_prompt_path.read_text(encoding="utf-8")

        self.ws_client = DoubaoWebSocketClient(
            realtime_app_id=doubao_realtime_app_id,
            realtime_access_key=doubao_realtime_access_key,
        )
        self.rest_client = DoubaoRESTClient(api_key=ark_api_key)
        self.state_manager = RSTMStateManager(initial_cci=initial_cci, initial_state=initial_state, state_file=state_file)
        self.state_manager.reset(initial_cci=initial_cci, initial_state=initial_state)
        self.dialogue_history: list[Dict[str, Any]] = []

        # TTS 配置可省略，省略则使用服务端默认值
        self.tts_config: Optional[Dict[str, Any]] = {
            "speaker": "zh_male_yunzhou_jupiter_bigtts",
            "audio_config": {
                "channel": 1,
                "format": "pcm_s16le",
                "sample_rate": 24000,
            },
        }

        self.use_model_response = True
        self._last_patient_text: Optional[str] = None
        self._asr_lock = asyncio.Lock()
        self._pending_doctor_text: Optional[str] = None
        self._processing_turn = asyncio.Lock()
        self._tts_stream: Optional[sd.RawOutputStream] = None
        self._pending_tts_data = bytearray()
        self._ttst_reply_id: Optional[str] = None
        self._patient_text_parts: list[str] = []
        self._user_querying = False
        self.model_version = "O"
        self._start_time = 0.0
        self._audio_chunk_counter = 0
        self._has_sent_audio = False
        self._current_style_prompt = StyleMapper.get_style_prompt(
            self.state_manager.get_current_state()
        )
        self._tts_capture_buffer: Optional[io.BytesIO] = None
        self._tts_dump_dir = project_root / "tts_dumps"
        self._tts_dump_dir.mkdir(parents=True, exist_ok=True)
        self._pause_audio_upload = False
        self._tts_sentence_delay = 3
        self._tts_sentence_timeout = 0.3
        self._tts_sentence_buffer: list[list[bytes]] = []
        self._tts_playback_started = False
        self._current_sentence_chunks: list[bytes] = []
        self._tts_sentence_start_time = 0.0

    def _format_history_text(self) -> str:
        formatted = []
        for idx, turn in enumerate(self.dialogue_history, start=1):
            role = turn.get("role", "Unknown")
            content = turn.get("content", "")
            formatted.append(f"Turn {idx}: {role}: {content}")
        return "\n".join(formatted)

    def _record_turn(self, role: str, content: str):
        self.dialogue_history.append({
            "role": role,
            "content": content.strip(),
        })

    def _build_system_prompt(self, override_state: Optional[float] = None) -> str:
        target_state = override_state if override_state is not None else self.state_manager.get_current_state()
        style_prompt = StyleMapper.get_style_prompt(target_state)
        return f"{self.patient_profile}\n\n{style_prompt}"

    def _format_user_query(self, doctor_text: str, style_prompt: str) -> str:
        return (
            f"{style_prompt}\n"
            f"Doctor: {doctor_text}\n"
            f"Please respond strictly as the patient described above."
        )

    def _log_event(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        elapsed = (time.monotonic() - self._start_time) if self._start_time else 0.0
        print(f"[{timestamp} +{elapsed:.3f}s] {message}")

    def _should_flush_buffer(self) -> bool:
        if len(self._tts_sentence_buffer) >= self._tts_sentence_delay:
            return True
        if self._tts_sentence_start_time:
            return (time.monotonic() - self._tts_sentence_start_time) >= self._tts_sentence_timeout
        return False

    def _flush_buffer(self):
        for buffered_sentence in self._tts_sentence_buffer:
            for buffered_chunk in buffered_sentence:
                self._write_tts_chunk(buffered_chunk)
        self._tts_sentence_buffer.clear()
        self._tts_playback_started = True
        self._tts_sentence_start_time = 0.0

    def _write_tts_chunk(self, chunk: bytes):
        if not self._tts_stream:
            return
        try:
            self._tts_stream.write(chunk)
        except Exception as exc:
            print(f"[Doubao] 播放音频失败: {exc}")

    def _chunk_has_voice(self, chunk: bytes) -> bool:
        if not chunk:
            return False
        try:
            samples = memoryview(chunk).cast("h")
        except ValueError:
            return True
        max_amp = 0
        for sample in samples:
            amp = abs(sample)
            if amp > max_amp:
                max_amp = amp
                if max_amp >= SILENCE_THRESHOLD:
                    return True
        return max_amp >= SILENCE_THRESHOLD

    def _flush_patient_text(self):
        if self._patient_text_parts:
            full = " ".join(self._patient_text_parts).strip()
            print(f"[患者回应-汇总] {full}")
            self._patient_text_parts.clear()

    async def _start_session(self, state: Optional[float] = None):
        await self.ws_client.start_session(
            system_prompt=self._build_system_prompt(override_state=state),
            tts_config=self.tts_config,
            input_mod="audio",
            model=self.model_version,
            end_smooth_window_ms=400,
        )

    def _extract_final_asr(self, message: dict) -> Optional[str]:
        text_parts = []
        for result in message.get("results", []):
            if result.get("is_interim", True):
                continue
            text = result.get("text", "").strip()
            if text:
                text_parts.append(text)
        if text_parts:
            return " ".join(text_parts)
        return None

    async def _generate_patient_text(self, doctor_text: str, style_prompt: str) -> str:
        full_prompt = f"{self.patient_profile}\n\n{style_prompt}"
        messages = [
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": doctor_text},
        ]
        response = self.rest_client.chat_completion(
            messages=messages,
            reasoning_effort=ReasoningEffort.MEDIUM,
            temperature=0.4,
        )
        if "choices" in response and response["choices"]:
            return response["choices"][0].get("message", {}).get("content", "").strip()
        return "抱歉，我暂时无法生成回应。"

    async def _process_doctor_turn(self, doctor_text: str):
        async with self._processing_turn:
            if not doctor_text:
                return

            self._record_turn("Doctor", doctor_text)
            dialogue_str = self._format_history_text()

            style_prompt = self._current_style_prompt
            if self.use_model_response:
                self._log_event("音频输入模式由豆包服务端自动生成患者回复")
                asyncio.create_task(self._grade_dialogue(dialogue_str))
            else:
                patient_text = await self._generate_patient_text(doctor_text, style_prompt)
                self._record_turn("Patient", patient_text)
                await self.ws_client.send_tts_text(patient_text)

    async def _grade_dialogue(self, dialogue_str: str):
        try:
            grade_result = await asyncio.to_thread(
                self.rest_client.grade_dialogue,
                dialogue_str,
                self.grader_prompt,
                ReasoningEffort.MINIMAL,
            )

            print("\n[LLM 输入历史]\n" + dialogue_str)
            print(f"\n[评分提示词来源] {self.grader_prompt_path}")

            cpas_score = grade_result.get("final_cpas_score")
            if isinstance(cpas_score, str):
                try:
                    cpas_score = float(cpas_score)
                except ValueError:
                    cpas_score = None
            if not isinstance(cpas_score, (int, float)) or not -8 <= cpas_score <= 5:
                self._log_event("CPAS结果不可评分，RSTM状态保持不变")
                return

            state_update = self.state_manager.update_state(cpas_score)
            style_prompt = StyleMapper.get_style_prompt(state_update["state"])
            self._current_style_prompt = style_prompt

            print("\n" + "-" * 60)
            print(f"CPAS 评分: {grade_result.get('final_cpas_score')}")
            print(f"Track A (任务完成度): {grade_result.get('scoring_breakdown', {}).get('track_a_task')}")
            print(f"Track B (共情能力): {grade_result.get('scoring_breakdown', {}).get('track_b_empathy')}")
            print(f"RSTM 状态更新: CCI={state_update['cci']:.2f}, S(t)={state_update['state']:.3f}")
            mapped_style = StyleMapper.map_state_to_style(state_update["state"])
            print(f"当前风格: Level {mapped_style['level']} - {mapped_style['name']}")
            print("-" * 60 + "\n")
        except Exception as exc:
            print(f"\n⚠️ 评分异步出错: {exc}")
            import traceback

            traceback.print_exc()

    async def _handle_event(self, message: dict):
        session_id = message.get("session_id")
        if session_id and self.ws_client.session_id and session_id != self.ws_client.session_id:
            return

        msg_type = message.get("type")
        self._log_event(f"收到豆包事件 {msg_type}")
        if msg_type == "ASRResponse":
            final_text = self._extract_final_asr(message)
            if final_text:
                self._log_event(f"ASR 最终文本: {final_text}")
                async with self._asr_lock:
                    self._pending_doctor_text = final_text
        elif msg_type == "ASRInfo":
            if not self._user_querying:
                print("[状态] 已侦测到医生语音，正在等待交互完成...")
        elif msg_type == "ASREnded":
            async with self._asr_lock:
                doctor_text = self._pending_doctor_text
                self._pending_doctor_text = None
            if doctor_text:
                self._user_querying = True
                self._log_event("ASR 已结束，开始处理医生回合")
                await self._process_doctor_turn(doctor_text)
        elif msg_type == "ChatResponse":
            content = message.get("content", "").strip()
            reply_id = message.get("reply_id")
            if content:
                if reply_id != self._ttst_reply_id:
                    self._patient_text_parts.clear()
                    self._ttst_reply_id = reply_id
                self._patient_text_parts.append(content)
                self._log_event(f"患者文本片段追加：{content}")
        elif msg_type == "TTSSentenceStart":
            self._tts_capture_buffer = io.BytesIO()
            self._pause_audio_upload = True
            self._log_event("TTSSentenceStart：初始化 TTS PCM 捕获，暂停麦克风上传")
            if not self._tts_sentence_buffer:
                self._tts_sentence_start_time = time.monotonic()
            self._current_sentence_chunks = []
        elif msg_type == "TTSResponse":
            audio_chunk = message.get("payload") or message.get("data")
            if isinstance(audio_chunk, (bytes, bytearray)):
                self._pending_tts_data.extend(audio_chunk)
                if self._tts_capture_buffer is not None:
                    self._tts_capture_buffer.write(audio_chunk)
                self._current_sentence_chunks.append(audio_chunk)
                self._log_event(f"TTS 音频 chunk: {len(audio_chunk)} bytes")
                if self._tts_playback_started:
                    self._write_tts_chunk(audio_chunk)
        elif msg_type == "TTSSentenceEnd":
            self._flush_patient_text()
            self._log_event("TTSSentenceEnd：患者语音段落播报中")
            print("[状态] 患者语音段落播报中...")
            if not self._tts_playback_started:
                self._tts_sentence_buffer.append(self._current_sentence_chunks.copy())
                self._current_sentence_chunks.clear()
                if self._should_flush_buffer():
                    self._flush_buffer()
            else:
                self._current_sentence_chunks.clear()
        elif msg_type == "TTSEnded":
            self._flush_patient_text()
            self._user_querying = False
            self._log_event("TTSEnded：患者语音播放完毕")
            print("[状态] 患者语音播放完毕，等待医生输入...")
            self._pause_audio_upload = False
            self._tts_playback_started = False
            self._tts_sentence_buffer.clear()
            self._tts_sentence_start_time = 0.0
            if self._tts_capture_buffer:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                dump_file = self._tts_dump_dir / f"tts_response_{timestamp}.pcm"
                try:
                    with dump_file.open("wb") as fh:
                        fh.write(self._tts_capture_buffer.getvalue())
                    self._log_event(f"TTS PCM 存档: {dump_file}")
                except Exception as exc:
                    self._log_event(f"保存 TTS PCM 失败: {exc}")
                finally:
                    self._tts_capture_buffer.close()
                    self._tts_capture_buffer = None
        elif msg_type == "ERROR":
            print(f"[Doubao] 事件错误: {message.get('error_code')}, 详情: {message.get('payload')}")
        elif msg_type in ("RAW", "TEXT"):
            pass
        else:
            print(f"[Doubao Event] type={msg_type}, keys={list(message.keys())}")

    async def _capture_microphone(self, queue: asyncio.Queue, stop_evt: asyncio.Event):
        loop = asyncio.get_running_loop()

        def callback(indata, frames, time, status):
            if status:
                print(f"[麦克风状态] {status}")
            if self._pause_audio_upload:
                return
            chunk = bytes(indata)
            if not self._has_sent_audio or self._chunk_has_voice(chunk):
                self._has_sent_audio = True
                loop.call_soon_threadsafe(queue.put_nowait, chunk)

        try:
            with sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                dtype="int16",
                channels=CHANNELS,
                callback=callback,
            ):
                print(f"开始采集麦克风音频（{SAMPLE_RATE}Hz, {CHANNELS}ch）...")
                self._log_event("麦克风采集启动")
                await stop_evt.wait()
        except Exception as exc:
            print(f"麦克风采集失败: {exc}")
        finally:
            await queue.put(None)

    async def _audio_sender(self, queue: asyncio.Queue):
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            await self.ws_client.send_audio(chunk)
            self._audio_chunk_counter += 1
            if self._audio_chunk_counter == 1 or self._audio_chunk_counter % 50 == 0:
                self._log_event(f"医生音频 chunk #{self._audio_chunk_counter} 已上传 ({len(chunk)} bytes)")
        self._log_event("医生音频上传任务结束")

    async def run(self):
        print("=" * 60)
        print("🚀 实时语音连接成功！豆包模型已加载以下提示词：")
        print(f"  - Endpoint: {self.ws_client.endpoint}")
        print(f"  - Resource: {self.ws_client.resource_id}")
        print(f"  - Model: {self.model_version}")
        print(f"  - 患者设定: {self.patient_profile_path}")
        print("  请确保麦克风已开启，后续对话将遵循以上提示词。")
        print("=" * 60)
        self._start_time = time.monotonic()
        self._log_event("开始连接豆包实时语音")
        await self.ws_client.connect()
        self._log_event("豆包 WebSocket 连接建立")
        await self._start_session()
        self._log_event("实时会话已成功启动")

        listener = asyncio.create_task(self.ws_client.listen(callback=self._handle_event))
        stop_event = asyncio.Event()
        mic_queue: asyncio.Queue[Optional[bytes]] = asyncio.Queue()
        capture_task = asyncio.create_task(self._capture_microphone(mic_queue, stop_event))
        sender_task = asyncio.create_task(self._audio_sender(mic_queue))

        try:
            self._tts_stream = sd.RawOutputStream(
                samplerate=24000,
                channels=1,
                dtype="float32",
            )
            self._tts_stream.start()
        except Exception as exc:
            print(f"✔ 无法打开播放设备：{exc}")

        print("\n按 Enter 停止对话并关闭连接...")
        await asyncio.to_thread(sys.stdin.readline)
        stop_event.set()
        await capture_task
        await sender_task

        await self.ws_client.finish_session()
        await self.ws_client.finish_connection()
        await self.ws_client.disconnect()
        self._log_event("实时语音连接已断开")
        listener.cancel()
        if self._tts_stream:
            self._tts_stream.stop()
            self._tts_stream.close()


def main():
    conductor = RealtimeVoiceConductor()
    try:
        asyncio.run(conductor.run())
    except KeyboardInterrupt:
        print("\n用户中断，退出。")


if __name__ == "__main__":
    main()
