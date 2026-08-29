"""Resolve bundled resources and writable application data locations."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    resource_root: Path
    application_root: Path


def resolve_runtime_paths(
    *,
    module_file: str | Path = __file__,
    frozen: bool | None = None,
    executable: str | Path | None = None,
    bundle_root: str | Path | None = None,
) -> RuntimePaths:
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if not is_frozen:
        root = Path(module_file).resolve().parent.parent
        return RuntimePaths(resource_root=root, application_root=root)

    executable_path = Path(executable or sys.executable).resolve()
    bundled = Path(bundle_root or getattr(sys, "_MEIPASS", executable_path.parent)).resolve()
    return RuntimePaths(
        resource_root=bundled,
        application_root=executable_path.parent,
    )


RUNTIME_PATHS = resolve_runtime_paths()
RESOURCE_ROOT = RUNTIME_PATHS.resource_root
APPLICATION_ROOT = RUNTIME_PATHS.application_root
