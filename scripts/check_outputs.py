"""Fail CI when the local pipeline did not produce a trustworthy run manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_outputs.py PATH_TO_MANIFEST")
    manifest_path = Path(sys.argv[1])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest["quality_gate_passed"]:
        raise SystemExit("data quality gate did not pass")
    if manifest["valid_rows"] <= 0:
        raise SystemExit("pipeline produced no valid rows")
    missing = [name for name in manifest["outputs"] if not (manifest_path.parent / name).is_file()]
    if missing:
        raise SystemExit(f"missing pipeline outputs: {', '.join(missing)}")
    print(f"validated {manifest['valid_rows']} rows at {manifest['quality_pass_rate']:.2%} quality")


if __name__ == "__main__":
    main()
