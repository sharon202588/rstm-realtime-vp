"""WAV storage for raw PCM16 streams."""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any


class PcmWaveWriter:
    """Write a PCM stream to a valid WAV file and expose audit metadata."""

    def __init__(
        self,
        path: str | Path,
        sample_rate: int,
        channels: int = 1,
        sample_width: int = 2,
    ):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.sample_rate = int(sample_rate)
        self.channels = int(channels)
        self.sample_width = int(sample_width)
        self.byte_count = 0
        self._complete = False
        self._closed = False
        self._wave = wave.open(str(self.path), "wb")
        self._wave.setnchannels(self.channels)
        self._wave.setsampwidth(self.sample_width)
        self._wave.setframerate(self.sample_rate)

    def write(self, data: bytes) -> None:
        if self._closed:
            raise RuntimeError("Cannot write to a closed WAV file.")
        if not data:
            return
        self._wave.writeframesraw(data)
        self.byte_count += len(data)

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "path": str(self.path.resolve()),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width": self.sample_width,
            "bytes": self.byte_count,
            "complete": self._complete,
        }

    def close(self, complete: bool = True) -> dict[str, Any]:
        if not self._closed:
            self._complete = bool(complete)
            self._wave.close()
            self._closed = True
        return self.metadata
