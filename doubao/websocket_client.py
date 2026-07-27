"""
Doubao WebSocket API client (v3 realtime dialogue).

This client follows the official protocol documented in docs/豆包实时语音API.md:
- Connect with required headers (App ID / Access Key / Resource ID / fixed App Key).
- Send StartConnection + StartSession using the binary protocol.
- Send audio (TaskRequest) and text (ChatTextQuery / ChatTTSText) events.
"""

from __future__ import annotations

import os
import json
import gzip
import uuid
import asyncio
from typing import Optional, Dict, Any, Callable

import websockets
import websockets.exceptions

# Protocol constants (see examples/realtime_dialog.zip/python3.7/protocol.py)
PROTOCOL_VERSION = 0b0001

CLIENT_FULL_REQUEST = 0b0001
CLIENT_AUDIO_ONLY_REQUEST = 0b0010

SERVER_FULL_RESPONSE = 0b1001
SERVER_ACK = 0b1011
SERVER_ERROR_RESPONSE = 0b1111

NO_SEQUENCE = 0b0000
POS_SEQUENCE = 0b0001
NEG_SEQUENCE = 0b0010
NEG_SEQUENCE_1 = 0b0011

MSG_WITH_EVENT = 0b0100

NO_SERIALIZATION = 0b0000
JSON_SERIALIZATION = 0b0001

NO_COMPRESSION = 0b0000
GZIP_COMPRESSION = 0b0001

EVENT_ID_TO_NAME = {
    50: "ConnectionStarted",
    51: "ConnectionFailed",
    52: "ConnectionFinished",
    150: "SessionStarted",
    152: "SessionFinished",
    153: "SessionFailed",
    154: "UsageResponse",
    251: "ConfigUpdated",
    450: "ASRInfo",
    451: "ASRResponse",
    459: "ASREnded",
    350: "TTSSentenceStart",
    351: "TTSSentenceEnd",
    352: "TTSResponse",
    359: "TTSEnded",
    550: "ChatResponse",
    553: "ChatTextQueryAck",
    559: "ChatEnded",
}

EVENT_NAME_TO_ID = {
    "StartConnection": 1,
    "FinishConnection": 2,
    "StartSession": 100,
    "FinishSession": 102,
    "TaskRequest": 200,
    "UpdateConfig": 201,
    "SayHello": 300,
    "ChatTTSText": 500,
    "ChatTextQuery": 501,
    "ChatRAGText": 502,
}


def _generate_header(
    version: int = PROTOCOL_VERSION,
    message_type: int = CLIENT_FULL_REQUEST,
    message_type_specific_flags: int = MSG_WITH_EVENT,
    serial_method: int = JSON_SERIALIZATION,
    compression_type: int = GZIP_COMPRESSION,
    reserved_data: int = 0x00,
    extension_header: bytes = b"",
) -> bytearray:
    header = bytearray()
    header_size = int(len(extension_header) / 4) + 1
    header.append((version << 4) | header_size)
    header.append((message_type << 4) | message_type_specific_flags)
    header.append((serial_method << 4) | compression_type)
    header.append(reserved_data)
    header.extend(extension_header)
    return header


def _gzip_json(payload: Dict[str, Any]) -> bytes:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return gzip.compress(data)


def _decode_session_id(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except Exception:
        return str(raw)


def _parse_response(res: bytes | str) -> Dict[str, Any]:
    if isinstance(res, str):
        return {"message_type": "TEXT", "payload": res}

    protocol_version = res[0] >> 4
    header_size = res[0] & 0x0F
    message_type = res[1] >> 4
    message_type_specific_flags = res[1] & 0x0F
    serialization_method = res[2] >> 4
    message_compression = res[2] & 0x0F
    payload = res[header_size * 4:]

    result: Dict[str, Any] = {
        "protocol_version": protocol_version,
        "message_type": message_type,
        "message_type_specific_flags": message_type_specific_flags,
    }

    payload_msg: bytes | str | Dict[str, Any] | None = None
    payload_size = 0
    start = 0

    if message_type in (SERVER_FULL_RESPONSE, SERVER_ACK):
        if message_type_specific_flags & NEG_SEQUENCE:
            result["seq"] = int.from_bytes(payload[:4], "big", signed=False)
            start += 4
        if message_type_specific_flags & MSG_WITH_EVENT:
            result["event_id"] = int.from_bytes(payload[start:start + 4], "big", signed=False)
            start += 4

        payload = payload[start:]
        session_id_size = int.from_bytes(payload[:4], "big", signed=True)
        session_id_raw = payload[4:session_id_size + 4]
        result["session_id"] = _decode_session_id(session_id_raw)
        payload = payload[4 + session_id_size:]
        payload_size = int.from_bytes(payload[:4], "big", signed=False)
        payload_msg = payload[4:]

    elif message_type == SERVER_ERROR_RESPONSE:
        result["error_code"] = int.from_bytes(payload[:4], "big", signed=False)
        payload_size = int.from_bytes(payload[4:8], "big", signed=False)
        payload_msg = payload[8:]

    if payload_msg is None:
        return result

    if message_compression == GZIP_COMPRESSION:
        payload_msg = gzip.decompress(payload_msg)
    # TTSResponse(352) 为二进制音频，直接返回 bytes

    if serialization_method == JSON_SERIALIZATION:
        payload_msg = json.loads(payload_msg.decode("utf-8"))
    elif serialization_method != NO_SERIALIZATION:
        payload_msg = payload_msg.decode("utf-8")

    result["payload"] = payload_msg
    result["payload_size"] = payload_size
    return result


class DoubaoWebSocketClient:
    """Doubao realtime dialogue WebSocket client."""

    DEFAULT_ENDPOINT = "wss://openspeech.bytedance.com/api/v3/realtime/dialogue"
    DEFAULT_RESOURCE_ID = "volc.speech.dialog"
    FIXED_APP_KEY = "PlgvMymc7f3tQnJ6"

    def __init__(
        self,
        realtime_app_id: Optional[str] = None,
        realtime_access_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        self.app_id = realtime_app_id or os.getenv("DOUBAO_REALTIME_APP_ID")
        self.access_key = realtime_access_key or os.getenv("DOUBAO_REALTIME_ACCESS_KEY")
        if not self.app_id or not self.access_key:
            raise ValueError(
                "Realtime credentials are required. Set both "
                "DOUBAO_REALTIME_APP_ID and DOUBAO_REALTIME_ACCESS_KEY."
            )

        self.endpoint = endpoint or os.getenv("DOUBAO_API_ENDPOINT") or self.DEFAULT_ENDPOINT
        self.resource_id = resource_id or self.DEFAULT_RESOURCE_ID
        self.connect_id = str(uuid.uuid4())

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.message_handlers: Dict[str, Callable] = {}
        self.session_id: Optional[str] = None
        self._connection_started = False
        self._send_lock = asyncio.Lock()

    def _headers(self) -> Dict[str, str]:
        common = {
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Connect-Id": self.connect_id,
        }
        return {
            "X-Api-App-ID": self.app_id,
            "X-Api-Access-Key": self.access_key,
            "X-Api-App-Key": self.FIXED_APP_KEY,
            **common,
        }

    async def connect(self):
        self.connect_id = str(uuid.uuid4())
        try:
            self.websocket = await websockets.connect(
                self.endpoint,
                extra_headers=self._headers(),
                ping_interval=None,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Doubao WebSocket API: {str(e)}") from e

    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self._connection_started = False
        self.session_id = None

    async def _send_full_request(
        self,
        event_id: int,
        payload: Dict[str, Any],
        session_id: Optional[str] = None,
        compression_type: int = GZIP_COMPRESSION,
    ):
        if not self.websocket:
            raise ConnectionError("WebSocket is not connected. Call connect() first.")

        header = _generate_header(compression_type=compression_type)
        request = bytearray(header)
        request.extend(int(event_id).to_bytes(4, "big"))

        if session_id is not None:
            session_bytes = session_id.encode("utf-8")
            request.extend(len(session_bytes).to_bytes(4, "big"))
            request.extend(session_bytes)

        serialized_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        payload_bytes = (
            gzip.compress(serialized_payload)
            if compression_type == GZIP_COMPRESSION
            else serialized_payload
        )
        request.extend(len(payload_bytes).to_bytes(4, "big"))
        request.extend(payload_bytes)

        async with self._send_lock:
            await self.websocket.send(request)

    async def _send_audio_request(self, audio_data: bytes, session_id: str):
        if not self.websocket:
            raise ConnectionError("WebSocket is not connected. Call connect() first.")

        header = _generate_header(
            message_type=CLIENT_AUDIO_ONLY_REQUEST,
            serial_method=NO_SERIALIZATION,
        )
        request = bytearray(header)
        request.extend(int(EVENT_NAME_TO_ID["TaskRequest"]).to_bytes(4, "big"))
        session_bytes = session_id.encode("utf-8")
        request.extend(len(session_bytes).to_bytes(4, "big"))
        request.extend(session_bytes)
        payload_bytes = gzip.compress(audio_data)
        request.extend(len(payload_bytes).to_bytes(4, "big"))
        request.extend(payload_bytes)
        async with self._send_lock:
            await self.websocket.send(request)

    async def start_connection(self):
        if self._connection_started:
            return
        await self._send_full_request(EVENT_NAME_TO_ID["StartConnection"], {})
        self._connection_started = True

    async def start_session(
        self,
        system_prompt: Optional[str] = None,
        bot_name: Optional[str] = None,
        system_role: Optional[str] = None,
        speaking_style: Optional[str] = None,
        tts_config: Optional[Dict[str, Any]] = None,
        input_mod: str = "audio",
        model: str = "O",
        recv_timeout: Optional[int] = None,
        end_smooth_window_ms: Optional[int] = None,
        enable_custom_vad: Optional[bool] = None,
        dialog_id: Optional[str] = None,
        **kwargs,
    ):
        if not self.websocket:
            raise ConnectionError("WebSocket is not connected. Call connect() first.")

        await self.start_connection()

        self.session_id = str(uuid.uuid4())

        dialog_extra: Dict[str, Any] = {
            "input_mod": input_mod,
            "model": model,
        }
        if recv_timeout is not None:
            dialog_extra["recv_timeout"] = recv_timeout

        asr_extra: Dict[str, Any] = {}
        if end_smooth_window_ms is not None:
            asr_extra["end_smooth_window_ms"] = end_smooth_window_ms
        if enable_custom_vad is not None:
            asr_extra["enable_custom_vad"] = enable_custom_vad

        dialog_payload: Dict[str, Any] = {
            "extra": dialog_extra,
        }
        if bot_name:
            dialog_payload["bot_name"] = bot_name

        # Use system_prompt as system_role if system_role is not provided
        merged_system_role = system_role or system_prompt
        if merged_system_role:
            dialog_payload["system_role"] = merged_system_role
        if speaking_style:
            dialog_payload["speaking_style"] = speaking_style
        if dialog_id is not None:
            dialog_payload["dialog_id"] = dialog_id

        payload: Dict[str, Any] = {
            "asr": {"extra": asr_extra},
            "dialog": dialog_payload,
        }

        if tts_config:
            payload["tts"] = tts_config

        payload.update(kwargs)

        await self._send_full_request(EVENT_NAME_TO_ID["StartSession"], payload, self.session_id)

    async def update_config(
        self,
        *,
        bot_name: str,
        system_role: str,
        speaking_style: str,
        dialog_id: str,
        tts_config: Dict[str, Any],
    ) -> None:
        """Replace the active session configuration without ending the session."""
        if not self.session_id:
            raise RuntimeError("Session not initialized. Call start_session() first.")
        if not dialog_id:
            raise ValueError("dialog_id is required for an in-session configuration update.")

        payload = {
            "dialog": {
                "bot_name": bot_name,
                "system_role": system_role,
                "speaking_style": speaking_style,
                "dialog_id": dialog_id,
            },
            "tts": tts_config,
        }
        await self._send_full_request(
            EVENT_NAME_TO_ID["UpdateConfig"],
            payload,
            self.session_id,
            compression_type=NO_COMPRESSION,
        )

    async def send_audio(self, audio_data: bytes):
        if not self.session_id:
            raise RuntimeError("Session not initialized. Call start_session() first.")
        await self._send_audio_request(audio_data, self.session_id)

    async def send_text_query(self, text: str):
        if not self.session_id:
            raise RuntimeError("Session not initialized. Call start_session() first.")
        await self._send_full_request(
            EVENT_NAME_TO_ID["ChatTextQuery"],
            {"content": text},
            self.session_id,
        )

    async def send_tts_text(self, text: str):
        if not self.session_id:
            raise RuntimeError("Session not initialized. Call start_session() first.")
        if not text:
            return
        # 按文档示例分两包发送，确保兼容长文本/中断场景
        await self._send_full_request(
            EVENT_NAME_TO_ID["ChatTTSText"],
            {"start": True, "content": text, "end": False},
            self.session_id,
        )
        await self._send_full_request(
            EVENT_NAME_TO_ID["ChatTTSText"],
            {"start": False, "content": "", "end": True},
            self.session_id,
        )

    async def finish_session(self):
        if not self.session_id:
            return
        await self._send_full_request(EVENT_NAME_TO_ID["FinishSession"], {}, self.session_id)

    async def finish_connection(self):
        await self._send_full_request(EVENT_NAME_TO_ID["FinishConnection"], {})

    def register_handler(self, event_type: str, handler: Callable):
        self.message_handlers[event_type] = handler

    async def receive_message(self) -> Dict[str, Any]:
        if not self.websocket:
            raise ConnectionError("WebSocket is not connected. Call connect() first.")
        message = await self.websocket.recv()
        parsed = _parse_response(message)
        event_id = parsed.get("event_id")
        event_name = EVENT_ID_TO_NAME.get(event_id)

        if event_name:
            payload = parsed.get("payload", {})
            result: Dict[str, Any] = {
                "type": event_name,
                "event_id": event_id,
                "session_id": parsed.get("session_id"),
            }
            if isinstance(payload, dict):
                result.update(payload)
            else:
                result["data"] = payload
            return result

        if parsed.get("message_type") == "TEXT":
            return {"type": "TEXT", "content": parsed.get("payload")}

        if parsed.get("message_type") == SERVER_ERROR_RESPONSE:
            return {"type": "ERROR", "error_code": parsed.get("error_code"), "payload": parsed.get("payload")}

        return {"type": "RAW", "parsed": parsed}

    async def listen(self, callback: Optional[Callable] = None):
        try:
            while True:
                message = await self.receive_message()
                msg_type = message.get("type")
                if msg_type in self.message_handlers:
                    await self.message_handlers[msg_type](message)
                if callback:
                    await callback(message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            raise RuntimeError(f"Error while listening to WebSocket messages: {str(e)}") from e
