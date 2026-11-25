from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from types import ModuleType


def _load_module_from_path(config_path: Path, playbook_root: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "lca_playbook_llm_config",
        config_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not create import spec for {config_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.__lca_playbook_root__ = playbook_root  # type: ignore[attr-defined]
    return module


def load_llm_config_from(start_path: Path) -> ModuleType:
    """Load repo-root llm_config.py, falling back to llm_config.example.py."""
    resolved = start_path.resolve()
    candidates = [resolved, *resolved.parents] if resolved.is_dir() else list(resolved.parents)
    for parent in candidates:
        local_config = parent / "llm_config.py"
        example_config = parent / "llm_config.example.py"
        if local_config.is_file():
            return _load_module_from_path(local_config, parent)
        if example_config.is_file():
            return _load_module_from_path(example_config, parent)

    raise RuntimeError(
        "Could not find repo-root llm_config.py or llm_config.example.py for convergence-review. "
        "Copy llm_config.example.py to llm_config.py or install from the lca_playbook source tree."
    )


@lru_cache(maxsize=1)
def load_llm_config() -> ModuleType:
    return load_llm_config_from(Path(__file__))


llm_config = load_llm_config()
