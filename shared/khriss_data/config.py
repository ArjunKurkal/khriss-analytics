"""Central paths and configuration for all Khriss Analytics projects.

One data lake, shared by every project, so a source is pulled once and
reused. Override the lake location with the KH_DATA_ROOT environment
variable; the default is ~/workspace/data.
"""
from __future__ import annotations

import os
from pathlib import Path


def data_root() -> Path:
    root = Path(os.environ.get("KH_DATA_ROOT", Path.home() / "workspace" / "data"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def project_data(project: str) -> tuple[Path, Path]:
    """Return (raw_dir, curated_dir) for a project, creating them."""
    base = data_root() / project
    raw = base / "raw"
    curated = base / "curated"
    raw.mkdir(parents=True, exist_ok=True)
    curated.mkdir(parents=True, exist_ok=True)
    return raw, curated
