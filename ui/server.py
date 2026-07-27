"""Local HTTP and WebSocket bridge for the voice-only research UI."""

from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import websockets
from dotenv import load_dotenv

from core.realtime_voice_session import RealtimeVoiceSession, VoiceSessionConfig
from doubao.rest_client import DoubaoRESTClient
from doubao.websocket_client import DoubaoWebSocketClient
from ui.protocol import ProtocolError, parse_command


PROJECT_ROOT = Path(__file__).parent.parent
STATIC_ROOT = Path(__file__).parent / "static"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] != "/api/patient-profile":
            super().do_GET()
            return

        try:
            profile = (PROJECT_ROOT / "specs" / "patient_profile.md").read_text(
                encoding="utf-8"
            )
        except OSError:
            self.send_error(500, "Patient profile is unavailable")
            return

        payload = json.dumps({"profile": profile}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


class ResearchEventLog:
    def __init__(self, config: VoiceSessionConfig):
        self.path = (
            Path(config.audio_root)
            / config.session_id
            / "research_events.jsonl"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: dict[str, Any]) -> None:
        record = {
            "logged_at": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")


class LocalVoiceUIServer:
    def __init__(
        self,
        http_host: str = "127.0.0.1",
        http_port: int = 7860,
        ws_host: str = "127.0.0.1",
        ws_port: int = 8765,
    ):
        self.http_host = http_host
        self.http_port = int(http_port)
        self.ws_host = ws_host
        self.ws_port = int(ws_port)
        self._http_server: ThreadingHTTPServer | None = None
        self._http_thread: threading.Thread | None = None

    def start_http(self) -> None:
        handler = partial(QuietStaticHandler, directory=str(STATIC_ROOT))
        self._http_server = ThreadingHTTPServer(
            (self.http_host, self.http_port),
            handler,
        )
        self._http_thread = threading.Thread(
            target=self._http_server.serve_forever,
            name="rstm-ui-http",
            daemon=True,
        )
        self._http_thread.start()

    def stop_http(self) -> None:
        if self._http_server:
            self._http_server.shutdown()
            self._http_server.server_close()
            self._http_server = None

    async def _handler(self, browser, path: str | None = None) -> None:
        del path
        config: VoiceSessionConfig | None = None
        session: RealtimeVoiceSession | None = None
        event_log: ResearchEventLog | None = None
        send_lock = asyncio.Lock()

        async def send_json(event: dict[str, Any]) -> None:
            serializable = dict(event)
            serializable.pop("data", None)
            if event_log and event.get("type") != "patient_audio":
                event_log.write(serializable)
            async with send_lock:
                await browser.send(json.dumps(serializable, ensure_ascii=False))

        async def emit(event: dict[str, Any]) -> None:
            if event.get("type") == "patient_audio":
                audio = event.get("data")
                if isinstance(audio, bytes):
                    async with send_lock:
                        await browser.send(audio)
                return
            await send_json(event)

        await send_json(
            {
                "type": "connection",
                "component": "local_bridge",
                "status": "connected",
            }
        )

        try:
            async for incoming in browser:
                if isinstance(incoming, bytes):
                    if not session or not session.is_started:
                        await send_json(
                            {
                                "type": "error",
                                "component": "microphone",
                                "message": "语音会话尚未开始，音频未发送。",
                            }
                        )
                        continue
                    await session.send_audio(incoming)
                    continue

                try:
                    command = parse_command(json.loads(incoming))
                    if command.name == "ping":
                        await send_json({"type": "pong"})
                    elif command.name == "configure":
                        if session:
                            await session.stop()
                            session = None
                        config = command.config
                        event_log = ResearchEventLog(config)
                        await send_json(
                            {
                                "type": "session",
                                "status": "configured",
                                "participant_id": config.participant_id,
                                "session_id": config.session_id,
                                "adaptive_enabled": config.adaptive_enabled,
                                "language": config.language,
                                "state": -0.25,
                                "style": {
                                    "level": 3,
                                    "name": "Concerned / Downcast",
                                    "description": "担忧/低落",
                                },
                                "retain_audio": config.retain_audio,
                            }
                        )
                    elif command.name == "start":
                        load_dotenv(PROJECT_ROOT / ".env", override=True)
                        if not config:
                            raise ProtocolError("请先完成受试者与测试场次设置。")
                        if session and session.is_started:
                            raise ProtocolError("语音测试已经开始。")
                        session = RealtimeVoiceSession(
                            config=config,
                            ws_client=DoubaoWebSocketClient(),
                            rest_client=DoubaoRESTClient(),
                            event_sink=emit,
                        )
                        try:
                            await session.start()
                        except Exception:
                            await session.stop()
                            session = None
                            raise
                    elif command.name == "stop":
                        if session:
                            await session.stop()
                    elif command.name == "reset":
                        if session:
                            await session.reset()
                            session = None
                        await send_json(
                            {
                                "type": "session",
                                "status": "reset",
                                "state": -0.25,
                                "style": {
                                    "level": 3,
                                    "name": "Concerned / Downcast",
                                    "description": "担忧/低落",
                                },
                            }
                        )
                except (json.JSONDecodeError, ProtocolError, ValueError) as exc:
                    await send_json(
                        {
                            "type": "error",
                            "component": "command",
                            "message": str(exc),
                        }
                    )
                except Exception as exc:
                    await send_json(
                        {
                            "type": "error",
                            "component": "runtime",
                            "message": str(exc),
                        }
                    )
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if session:
                await session.stop()

    async def serve(self) -> None:
        self.start_http()
        print(f"RSTM-SP UI: http://{self.http_host}:{self.http_port}")
        print(f"Voice bridge: ws://{self.ws_host}:{self.ws_port}")
        try:
            async with websockets.serve(
                self._handler,
                self.ws_host,
                self.ws_port,
                max_size=2**20,
                ping_interval=20,
                ping_timeout=20,
            ):
                await asyncio.Future()
        finally:
            self.stop_http()
