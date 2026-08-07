# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""loomground-factual — the assertoric substrate. Lowers facts into the fixed 5D."""
from ._version import __version__
from .grammar import clean_entity, load_json, lower

__all__ = ["lower", "clean_entity", "load_json", "__version__"]
