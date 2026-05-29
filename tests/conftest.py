"""Shared loaders for the benchmark measurement scripts.

The scripts live in ``scripts/`` and aren't an importable package, so we load
them by path. ``sys.modules`` registration is required before ``exec_module``
or ``@dataclass`` introspection fails (it looks the module up by name).
"""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def score_run2():
    return _load("score_run2")


@pytest.fixture(scope="session")
def aggregate():
    return _load("aggregate_results")
