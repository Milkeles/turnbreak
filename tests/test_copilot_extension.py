import shutil
import subprocess
from pathlib import Path
import pytest

EXT_PATH = Path(__file__).resolve().parent.parent / "adapters" / "copilot_extension" / "extension.mjs"


def test_extension_file_exists():
    assert EXT_PATH.exists(), f"Missing extension file: {EXT_PATH}"


def test_node_syntax_ok_or_skip():
    node = shutil.which("node")
    if not node:
        pytest.skip("node not available; skip syntax check")
    # Use node --check if available; fall back to running node to parse via --eval
    try:
        # Newer Node versions support --check
        res = subprocess.run([node, "--check", str(EXT_PATH)], capture_output=True)
        assert res.returncode == 0, f"node syntax check failed: {res.stderr.decode()[:200]}"
    except Exception:
        # Fallback: try parsing by invoking node to load the module
        res = subprocess.run([node, "-e", f"import('{EXT_PATH.as_posix()}')"], capture_output=True)
        assert res.returncode == 0, f"node import failed: {res.stderr.decode()[:200]}"
