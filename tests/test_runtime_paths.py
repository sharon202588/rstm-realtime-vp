from pathlib import Path

from core.runtime_paths import resolve_runtime_paths


def test_source_runtime_uses_repository_root_for_resources_and_data(tmp_path):
    module_file = tmp_path / "project" / "core" / "runtime_paths.py"
    paths = resolve_runtime_paths(module_file=module_file, frozen=False)

    assert paths.resource_root == tmp_path / "project"
    assert paths.application_root == tmp_path / "project"


def test_frozen_runtime_separates_bundled_resources_from_writable_app_folder(tmp_path):
    executable = tmp_path / "portable" / "RealtimeVoiceVP.exe"
    bundle = tmp_path / "portable" / "_internal"
    paths = resolve_runtime_paths(
        module_file=tmp_path / "ignored.py",
        frozen=True,
        executable=executable,
        bundle_root=bundle,
    )

    assert paths.resource_root == bundle
    assert paths.application_root == executable.parent
