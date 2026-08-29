"""Start the local RSTM-SP voice test interface."""

from __future__ import annotations

import argparse
import asyncio

from dotenv import load_dotenv

from core.runtime_paths import APPLICATION_ROOT

from ui.server import LocalVoiceUIServer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RSTM-SP local voice test UI")
    parser.add_argument("--http-port", type=int, default=7860)
    parser.add_argument("--ws-port", type=int, default=8765)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    load_dotenv(APPLICATION_ROOT / ".env", override=True)
    server = LocalVoiceUIServer(http_port=args.http_port, ws_port=args.ws_port)
    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
