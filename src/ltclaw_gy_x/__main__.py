# -*- coding: utf-8 -*-
"""Allow running LTCLAW-GY.X via ``python -m ltclaw_gy_x``."""
from .cli.main import cli

if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
