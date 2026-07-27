"""Shared realtime voice session core for CLI and local browser testing."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from core.audio_storage import PcmWaveWriter
from core.grading import GradingJob, format_grader_prompt, normalize_grade_result
from rstm.state_manager import RSTMStateManager
from rstm.style_mapper import StyleMapper


EventSink = Callable[[dict[str, Any]], Any | Awaitable[Any]]


@dataclass(frozen=True)
class VoiceSessionConfig:
    """Configuration fixed for one participant voice session."""

    participant_id: str
    session_id: str
    adaptive_enabled: bool = True
    language: str = "zh"
    scenario: str = "breaking_bad_news"
    case_context: str = ""
    initial_state: float = -0.25
    fixed_style_state: float = -0.25
    retain_audio: bool = True
    state_file: Optional[str] = None
    patient_profile_path: Optional[str] = None
    audio_root: str = "logs"


class RealtimeVoiceSession:
    """Coordinate Doubao voice events, CPAS grading, RSTM, and UI events."""

    STYLE_UPDATE_ACK_TIMEOUT_SECONDS = 0.75
    SPEECH_END_SILENCE_MS = 1500

    def __init__(
        self,
        config: VoiceSessionConfig,
        ws_client: Any,
        rest_client: Any,
        logger: Any = None,
        event_sink: Optional[EventSink] = None,
    ):
        self.config = config
        self.ws_client = ws_client
        self.rest_client = rest_client
        self.logger = logger
        self.event_sink = event_sink

        self.state_manager = RSTMStateManager(
            initial_cci=0.0,
            initial_state=config.initial_state,
            state_file=config.state_file,
        )
        self.fixed_style_state = float(config.fixed_style_state)
        self.dialogue_history: list[dict[str, Any]] = []
        self.dialog_id: Optional[str] = None

        self._doctor_counter = 0
        self._patient_counter = 0
        self._pending_asr_text: Optional[str] = None
        self._patient_parts: list[str] = []
        self._active_reply_id: Optional[str] = None
        self._committed_reply_ids: set[str] = set()
        self._applied_grade_turn_ids: set[str] = set()

        self._grade_queue: asyncio.Queue[Optional[GradingJob]] = asyncio.Queue()
        self._grade_worker_task: Optional[asyncio.Task] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._started = False
        self._stopping = False
        self._refresh_needed = False
        self._refresh_task: Optional[asyncio.Task] = None
        self._config_updated_event = asyncio.Event()
        self._config_update_in_flight = False
        self._config_update_error: Optional[str] = None
        self._remote_audio_enabled = False
        self._audio_send_lock = asyncio.Lock()
        self._asr_active = False
        self._response_active = False
        self._clinician_audio: Optional[PcmWaveWriter] = None
        self._patient_audio: Optional[PcmWaveWriter] = None

        project_root = Path(__file__).parent.parent
        profile_path = (
            Path(config.patient_profile_path)
            if config.patient_profile_path
            else project_root / "specs" / "patient_profile.md"
        )
        self.patient_profile = profile_path.read_text(encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def current_state(self) -> float:
        if self.config.adaptive_enabled:
            return round(self.state_manager.get_current_state(), 12)
        return self.fixed_style_state

    @property
    def current_style(self) -> dict[str, Any]:
        return StyleMapper.map_state_to_style(self.current_state)

    @property
    def pending_grade_count(self) -> int:
        return self._grade_queue.qsize()

    async def _emit(self, event: dict[str, Any]) -> None:
        if not self.event_sink:
            return
        outcome = self.event_sink(event)
        if inspect.isawaitable(outcome):
            await outcome

    def _system_prompt(self) -> str:
        language_instruction = (
            "请全程使用中文与学习者交流。"
            if self.config.language == "zh"
            else "Use English throughout the interaction."
        )
        case_context = (
            f"\n\nSession-specific case context:\n{self.config.case_context}"
            if self.config.case_context.strip()
            else ""
        )
        return f"{self.patient_profile}\n\n{language_instruction}{case_context}"

    def _speaking_style(self) -> str:
        return StyleMapper.get_style_prompt(self.current_state)

    @staticmethod
    def _bot_name() -> str:
        return "RSTM-SP Patient"

    @staticmethod
    def _tts_config() -> dict[str, Any]:
        return {
            "speaker": "zh_male_yunzhou_jupiter_bigtts",
            "audio_config": {
                "channel": 1,
                "format": "pcm_s16le",
                "sample_rate": 24000,
            },
        }
    async def start(self) -> None:
        if self._started:
            return
        self._stopping = False
        self._remote_audio_enabled = False
        if self.config.retain_audio:
            audio_dir = Path(self.config.audio_root) / self.config.session_id / "audio"
            self._clinician_audio = PcmWaveWriter(
                audio_dir / "clinician_session.wav", sample_rate=16000
            )
            self._patient_audio = PcmWaveWriter(
                audio_dir / "patient_session.wav", sample_rate=24000
            )
        self._grade_worker_task = asyncio.create_task(self._grade_worker())
        await self._emit({"type": "connection", "component": "doubao", "status": "connecting"})
        await self.ws_client.connect()
        await self._emit({"type": "connection", "component": "doubao", "status": "connected"})
        await self.ws_client.start_session(
            bot_name=self._bot_name(),
            system_role=self._system_prompt(),
            speaking_style=self._speaking_style(),
            tts_config=self._tts_config(),
            input_mod="audio",
            model="O",
            end_smooth_window_ms=self.SPEECH_END_SILENCE_MS,
            enable_custom_vad=True,
            dialog_id=self.dialog_id,
        )
        self._started = True
        self._listener_task = asyncio.create_task(
            self.ws_client.listen(callback=self.handle_doubao_event)
        )
        await self._emit(
            {
                "type": "session",
                "status": "started",
                "participant_id": self.config.participant_id,
                "session_id": self.config.session_id,
                "adaptive_enabled": self.config.adaptive_enabled,
                "state": self.current_state,
                "style": self.current_style,
            }
        )

    async def send_audio(self, chunk: bytes) -> None:
        if not self._started:
            raise RuntimeError("Voice session is not started.")
        if self._clinician_audio:
            self._clinician_audio.write(chunk)
        async with self._audio_send_lock:
            if not self._remote_audio_enabled:
                return
            await self.ws_client.send_audio(chunk)

    async def handle_doubao_event(self, message: dict[str, Any]) -> None:
        event_type = message.get("type")

        if event_type == "SessionStarted":
            self.dialog_id = message.get("dialog_id") or self.dialog_id
            async with self._audio_send_lock:
                self._remote_audio_enabled = self._started and not self._stopping
            await self._emit(
                {
                    "type": "connection",
                    "component": "realtime_session",
                    "status": "connected",
                    "dialog_id": self.dialog_id,
                }
            )
            return

        if event_type == "ConfigUpdated":
            if self._config_update_in_flight:
                self._config_updated_event.set()
            return

        if event_type == "SessionFinished":
            return
        if event_type == "ASRInfo":
            self._asr_active = True
            await self._emit({"type": "connection", "component": "asr", "status": "listening"})
            return

        if event_type == "ASRResponse":
            final_parts = []
            for result in message.get("results", []):
                if result.get("is_interim", True):
                    continue
                text = str(result.get("text", "")).strip()
                if text:
                    final_parts.append(text)
            if final_parts:
                self._pending_asr_text = " ".join(final_parts)
                await self._emit(
                    {
                        "type": "asr",
                        "status": "final",
                        "text": self._pending_asr_text,
                    }
                )
            return

        if event_type == "ASREnded":
            self._asr_active = False
            if (self._pending_asr_text or "").strip():
                self._response_active = True
            await self._commit_doctor_turn()
            return

        if event_type == "ChatResponse":
            self._response_active = True
            content = str(message.get("content", "")).strip()
            reply_id = str(message.get("reply_id") or self._active_reply_id or "reply")
            if reply_id != self._active_reply_id:
                self._patient_parts.clear()
                self._active_reply_id = reply_id
            if content:
                self._patient_parts.append(content)
                await self._emit(
                    {
                        "type": "patient_text",
                        "status": "partial",
                        "reply_id": reply_id,
                        "content": content,
                    }
                )
            return

        if event_type in ("ChatEnded", "TTSEnded"):
            await self._commit_patient_turn(message.get("reply_id"))
            if event_type == "TTSEnded":
                self._response_active = False
                await self._emit({"type": "connection", "component": "tts", "status": "idle"})
                if self._refresh_needed and self._started:
                    self._schedule_remote_refresh()
            return

        if event_type == "TTSSentenceStart":
            await self._emit({"type": "connection", "component": "tts", "status": "speaking"})
            return

        if event_type == "TTSResponse":
            audio = message.get("data") or message.get("payload")
            if isinstance(audio, (bytes, bytearray)):
                if self._patient_audio:
                    self._patient_audio.write(bytes(audio))
                await self._emit(
                    {
                        "type": "patient_audio",
                        "sample_rate": 24000,
                        "data": bytes(audio),
                    }
                )
            return

        if event_type == "ERROR":
            error_message = str(message.get("payload") or message.get("error_code"))
            if self._config_update_in_flight:
                self._config_update_error = error_message
                self._config_updated_event.set()
            await self._emit(
                {
                    "type": "error",
                    "component": "doubao",
                    "message": error_message,
                }
            )

    async def _commit_doctor_turn(self) -> None:
        doctor_text = (self._pending_asr_text or "").strip()
        self._pending_asr_text = None
        self._doctor_counter += 1
        doctor_turn_id = f"D-{self._doctor_counter:04d}"

        if not doctor_text:
            await self._emit(
                {
                    "type": "grade",
                    "doctor_turn_id": doctor_turn_id,
                    "display_score": 0,
                    "control_score": None,
                    "grading_status": "unscorable",
                    "applied_to_rstm": False,
                    "brief_rationale": "Final ASR text was unavailable.",
                }
            )
            return

        preceding_history = tuple(dict(item) for item in self.dialogue_history)
        turn = {
            "turn_id": doctor_turn_id,
            "role": "Doctor",
            "content": doctor_text,
        }
        self.dialogue_history.append(turn)
        await self._emit({"type": "transcript", "turn": turn})

        job = GradingJob(
            doctor_turn_id=doctor_turn_id,
            target_utterance=doctor_text,
            preceding_history=preceding_history,
            submitted_at=self._now(),
        )
        await self._grade_queue.put(job)
        await self._emit(
            {
                "type": "grade",
                "doctor_turn_id": doctor_turn_id,
                "display_score": 0,
                "control_score": None,
                "grading_status": "pending",
                "applied_to_rstm": False,
            }
        )

    async def _commit_patient_turn(self, reply_id: Any = None) -> None:
        resolved_reply_id = str(reply_id or self._active_reply_id or "reply")
        if resolved_reply_id in self._committed_reply_ids:
            return
        patient_text = " ".join(self._patient_parts).strip()
        if not patient_text:
            return

        self._patient_counter += 1
        turn = {
            "turn_id": f"P-{self._patient_counter:04d}",
            "role": "Patient",
            "content": patient_text,
        }
        self.dialogue_history.append(turn)
        self._committed_reply_ids.add(resolved_reply_id)
        self._patient_parts.clear()
        await self._emit({"type": "transcript", "turn": turn})

    async def _grade_worker(self) -> None:
        while True:
            job = await self._grade_queue.get()
            try:
                if job is None:
                    return
                prompt = format_grader_prompt(job)
                started_at = self._now()
                try:
                    raw_result = await asyncio.to_thread(self.rest_client.grade_prompt, prompt)
                    result = normalize_grade_result(raw_result, job.doctor_turn_id)
                except Exception as exc:
                    result = normalize_grade_result(
                        {"grading_status": "error", "reasoning": str(exc)},
                        job.doctor_turn_id,
                    )
                result["started_at"] = started_at
                result["completed_at"] = self._now()
                await self._apply_grade(result)
            finally:
                self._grade_queue.task_done()

    async def _apply_grade(self, result: dict[str, Any]) -> None:
        doctor_turn_id = str(result.get("doctor_turn_id", ""))
        control_score = result.get("control_score")
        if (
            result.get("grading_status") == "scored"
            and isinstance(control_score, (int, float))
            and self.config.adaptive_enabled
            and doctor_turn_id not in self._applied_grade_turn_ids
        ):
            previous_level = self.current_style["level"]
            update = self.state_manager.update_state(control_score)
            updated_style = self.current_style
            style_changed = updated_style["level"] != previous_level
            self._applied_grade_turn_ids.add(doctor_turn_id)
            result["applied_to_rstm"] = True
            result["style_changed"] = style_changed
            self._refresh_needed = self._refresh_needed or style_changed
            await self._emit(
                {
                    "type": "rstm",
                    **update,
                    "style": updated_style,
                    "style_changed": style_changed,
                    "doctor_turn_id": doctor_turn_id,
                }
            )
            if (
                self._refresh_needed
                and self._started
                and not self._asr_active
                and not self._response_active
            ):
                self._schedule_remote_refresh()
        await self._emit({"type": "grade", **result})

    def _schedule_remote_refresh(self) -> None:
        if not self._started or self._stopping:
            return
        if self._refresh_task and not self._refresh_task.done():
            return
        self._refresh_task = asyncio.create_task(self._refresh_remote_session())

    async def _refresh_remote_session(self) -> None:
        current_task = asyncio.current_task()
        target_level = self.current_style["level"]
        self._refresh_needed = False
        async with self._audio_send_lock:
            self._remote_audio_enabled = False

        await self._emit(
            {
                "type": "connection",
                "component": "realtime_session",
                "status": "updating",
            }
        )

        hot_update_succeeded = False
        try:
            if not self.dialog_id:
                raise RuntimeError("The active session did not return a dialog_id.")

            self._config_update_error = None
            self._config_updated_event.clear()
            self._config_update_in_flight = True
            await self.ws_client.update_config(
                bot_name=self._bot_name(),
                system_role=self._system_prompt(),
                speaking_style=self._speaking_style(),
                dialog_id=self.dialog_id,
                tts_config=self._tts_config(),
            )
            await asyncio.wait_for(
                self._config_updated_event.wait(),
                timeout=self.STYLE_UPDATE_ACK_TIMEOUT_SECONDS,
            )
            if self._config_update_error:
                raise RuntimeError(self._config_update_error)
            hot_update_succeeded = True
        except asyncio.CancelledError:
            raise
        except Exception as hot_update_error:
            if not self._stopping and self._started:
                try:
                    await self._rebuild_remote_session()
                except Exception as reconnect_error:
                    await self._emit(
                        {
                            "type": "error",
                            "component": "doubao",
                            "message": (
                                "Patient style update and fallback reconnect both failed: "
                                f"{hot_update_error}; {reconnect_error}"
                            ),
                        }
                    )
        finally:
            self._config_update_in_flight = False
            self._config_update_error = None
            self._config_updated_event.clear()

            if hot_update_succeeded and not self._stopping and self._started:
                async with self._audio_send_lock:
                    self._remote_audio_enabled = True
                await self._emit(
                    {
                        "type": "connection",
                        "component": "realtime_session",
                        "status": "connected",
                        "dialog_id": self.dialog_id,
                        "update_mode": "hot",
                    }
                )
                if self.current_style["level"] != target_level:
                    self._refresh_needed = True

            if self._refresh_task is current_task:
                self._refresh_task = None

        if (
            self._refresh_needed
            and self._started
            and not self._stopping
            and not self._asr_active
            and not self._response_active
        ):
            self._schedule_remote_refresh()

    async def _rebuild_remote_session(self) -> None:
        await self._emit(
            {
                "type": "connection",
                "component": "realtime_session",
                "status": "fallback_reconnecting",
            }
        )

        listener = self._listener_task
        self._listener_task = None
        if listener and listener is not asyncio.current_task():
            listener.cancel()
            await asyncio.gather(listener, return_exceptions=True)

        for operation in (
            self.ws_client.finish_session,
            self.ws_client.finish_connection,
        ):
            try:
                await operation()
            except Exception:
                pass
        await self.ws_client.disconnect()

        if self._stopping or not self._started:
            return

        await self.ws_client.connect()
        if self._stopping or not self._started:
            await self.ws_client.disconnect()
            return

        applied_level = self.current_style["level"]
        await self._start_refreshed_remote_session()
        self._refresh_needed = self.current_style["level"] != applied_level
        self._listener_task = asyncio.create_task(
            self.ws_client.listen(callback=self.handle_doubao_event)
        )

    async def _start_refreshed_remote_session(self) -> None:
        await self.ws_client.start_session(
            bot_name=self._bot_name(),
            system_role=self._system_prompt(),
            speaking_style=self._speaking_style(),
            tts_config=self._tts_config(),
            input_mod="audio",
            model="O",
            end_smooth_window_ms=self.SPEECH_END_SILENCE_MS,
            enable_custom_vad=True,
            dialog_id=self.dialog_id,
        )

    async def wait_until_refresh_idle(self) -> None:
        while self._refresh_task:
            task = self._refresh_task
            await asyncio.shield(task)

    async def wait_until_grades_idle(self) -> None:
        await self._grade_queue.join()

    async def stop(self) -> None:
        if self._stopping:
            return
        self._stopping = True
        async with self._audio_send_lock:
            self._remote_audio_enabled = False
        if self._refresh_task:
            self._refresh_task.cancel()
            await asyncio.gather(self._refresh_task, return_exceptions=True)
            self._refresh_task = None
        if self._grade_worker_task:
            self._grade_worker_task.cancel()
            await asyncio.gather(self._grade_worker_task, return_exceptions=True)
            self._grade_worker_task = None
        while not self._grade_queue.empty():
            try:
                self._grade_queue.get_nowait()
                self._grade_queue.task_done()
            except asyncio.QueueEmpty:
                break
        if self._listener_task:
            self._listener_task.cancel()
            await asyncio.gather(self._listener_task, return_exceptions=True)
            self._listener_task = None
        try:
            if self._started:
                await self.ws_client.finish_session()
            await self.ws_client.finish_connection()
        except Exception:
            pass
        finally:
            await self.ws_client.disconnect()
        self._started = False
        audio_files = []
        for writer in (self._clinician_audio, self._patient_audio):
            if writer:
                audio_files.append(writer.close(complete=True))
        self._clinician_audio = None
        self._patient_audio = None
        if audio_files:
            await self._emit({"type": "audio", "retained": True, "files": audio_files})
        await self._emit({"type": "session", "status": "stopped"})

    async def reset(self) -> None:
        await self.stop()
        self.state_manager.reset(initial_cci=0.0, initial_state=self.config.initial_state)
        self.dialogue_history.clear()
        self.dialog_id = None
        self._doctor_counter = 0
        self._patient_counter = 0
        self._pending_asr_text = None
        self._patient_parts.clear()
        self._active_reply_id = None
        self._committed_reply_ids.clear()
        self._applied_grade_turn_ids.clear()
        self._stopping = False
        await self._emit(
            {
                "type": "session",
                "status": "reset",
                "state": self.current_state,
                "style": self.current_style,
            }
        )

