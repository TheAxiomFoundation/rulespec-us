from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOTS = (ROOT / "statute", ROOT / "regulation", ROOT / "guidance")


def main() -> int:
    stub_files: list[Path] = []
    for content_root in CONTENT_ROOTS:
        if not content_root.exists():
            continue
        for rac_file in sorted(content_root.rglob("*.rac")):
            if "status: stub" in rac_file.read_text():
                stub_files.append(rac_file.relative_to(ROOT))

    if not stub_files:
        print("No promoted RAC stubs found.")
        return 0

    print("Promoted RAC stubs are not allowed in rac-us-al:")
    for stub_file in stub_files:
        print(f"- {stub_file.as_posix()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
