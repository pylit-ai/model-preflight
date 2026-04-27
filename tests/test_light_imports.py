from __future__ import annotations

import importlib
import sys


def test_top_level_import_does_not_import_litellm():
    sys.modules.pop("model_preflight", None)
    sys.modules.pop("litellm", None)

    importlib.import_module("model_preflight")

    assert "litellm" not in sys.modules
