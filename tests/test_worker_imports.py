"""Guard lightweight worker modules against optional web dependency imports."""

import os
from pathlib import Path
import subprocess
import sys


def test_voice_controls_import_without_web_dependencies(tmp_path):
    source = Path(__file__).resolve().parents[1] / "apps" / "papito_core" / "src"
    # A fresh interpreter matters: the normal suite has already imported FastAPI.
    code = """
import importlib.abc
import sys

class NoWebDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'fastapi', 'uvicorn'}:
            raise ModuleNotFoundError('Optional web dependency: ' + fullname)

sys.meta_path.insert(0, NoWebDependencies())
from papito_core.voice_quality import (
    assess_x_voice, choose_voice_shape, format_x_voice_direction, render_x_fallback,
)
shape, allow_question = choose_voice_shape([])
assert format_x_voice_direction(shape, allow_question)
assert assess_x_voice(render_x_fallback({'subject': 'clean wealth'})).passed
assert 'papito_core.intelligence' not in sys.modules
assert 'fastapi' not in sys.modules
"""
    env = {**os.environ, "PYTHONPATH": str(source), "PYTHON_DOTENV_DISABLED": "1"}
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
