"""Pytest configuration: make the ``src`` package importable without install.

The repo is standard-library only and runs in an offline sandbox, so there is
no editable install step. Adding ``src`` to ``sys.path`` keeps ``import dgqp``
working in CI and locally.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

REPO_ROOT = ROOT
