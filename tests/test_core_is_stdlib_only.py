import ast
import sys
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent.parent / "src" / "turnbreak" / "core"
ALLOWED = set(sys.stdlib_module_names) | {"turnbreak", "__future__"}


def _imported_top_level_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def test_core_modules_only_import_stdlib_or_turnbreak():
    offenders = {
        path.name: bad
        for path in sorted(CORE_DIR.glob("*.py"))
        if (bad := _imported_top_level_modules(path) - ALLOWED)
    }
    assert offenders == {}
