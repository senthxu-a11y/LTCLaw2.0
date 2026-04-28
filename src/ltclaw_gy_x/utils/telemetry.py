# -*- coding: utf-8 -*-
"""Telemetry is disabled for LTCLAW-GY.X local deployments."""
from __future__ import annotations

from pathlib import Path


def collect_and_upload_telemetry(working_dir: Path) -> bool:
    """Keep a no-op compatibility API while telemetry stays disabled."""
    _ = working_dir
    return False
