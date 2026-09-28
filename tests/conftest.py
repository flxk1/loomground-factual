# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Dev-only import shim for the sibling-repository layout.

When this package is pip-installed (CI, a release, an end user) this file does
nothing. It exists so a fresh local checkout can run ``pytest`` without an
install step: the package's own ``src`` is prepended to ``sys.path`` only if the
import would otherwise fail. loomground-factual is a leaf — it has no Loomground
siblings at runtime. The versum sibling is shimmed for TESTS ONLY, so the plane's
nD-system document can be validated by ``versum.nd`` when the checkout is present
(tests use ``pytest.importorskip`` and skip cleanly otherwise); package code never
imports it.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]  # repo root; this file lives in tests/

if importlib.util.find_spec("loomground_factual") is None:
    _self_src = _HERE / "src"
    if _self_src.is_dir() and str(_self_src) not in sys.path:
        sys.path.insert(0, str(_self_src))

if importlib.util.find_spec("versum") is None:
    _versum_src = _HERE.parent / "loomground-versum" / "src"
    if _versum_src.is_dir() and str(_versum_src) not in sys.path:
        sys.path.append(str(_versum_src))
