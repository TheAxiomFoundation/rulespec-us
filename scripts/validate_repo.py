from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_RAC_ROOT = ROOT.parent / "rac"


def run_step(name: str, command: list[str], cwd: Path | None = None) -> None:
    print(f"==> {name}")
    result = subprocess.run(command, cwd=cwd or ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def rac_module_invocation(module: str) -> tuple[list[str], Path | None]:
    if importlib.util.find_spec("rac") is not None:
        return [sys.executable, "-m", module], ROOT
    if shutil.which("uv") and LOCAL_RAC_ROOT.exists():
        return ["uv", "run", "python", "-m", module], LOCAL_RAC_ROOT
    if shutil.which("uv"):
        return ["uv", "run", "python", "-m", module], ROOT
    return [sys.executable, "-m", module], ROOT


def main() -> int:
    validate_cmd, validate_cwd = rac_module_invocation("rac.validate")
    test_cmd, test_cwd = rac_module_invocation("rac.test_runner")

    run_step(
        "Check for promoted RAC stubs",
        [sys.executable, str(ROOT / "scripts" / "check_no_promoted_stubs.py")],
    )
    run_step(
        "Validate .rac schema and imports",
        [*validate_cmd, "all", str(ROOT)],
        cwd=validate_cwd,
    )
    run_step(
        "Run inline RAC tests",
        [*test_cmd, str(ROOT), "-v"],
        cwd=test_cwd,
    )
    print("All rac-us-al validation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
