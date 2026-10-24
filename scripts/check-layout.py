#!/usr/bin/env python3
"""Check required entry points, ELF runpaths, and payload symlinks."""
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
for name in ("bin/beremiz", "bin/beremiz-cli", "bin/beremiz-python", "matiec/iec2c",
             "matiec/lib/ieclib.txt", "toolchain/bin/gcc", "beremiz/Beremiz.py"):
    if not (root / name).is_file():
        raise SystemExit("Missing payload entry: " + name)
for path in root.rglob("*"):
    if path.is_symlink():
        target = path.readlink()
        if target.is_absolute() or not path.resolve().is_relative_to(root):
            raise SystemExit(f"External symlink: {path}: {target}")
    if not path.is_file():
        continue
    with path.open("rb") as stream:
        elf = stream.read(4) == b"\x7fELF"
    if elf:
        dynamic = subprocess.run(["readelf", "-d", str(path)], capture_output=True, text=True).stdout
        for line in dynamic.splitlines():
            if ("RPATH" in line or "RUNPATH" in line) and str(root.parent) in line:
                raise SystemExit("Build path in ELF: " + str(path))
print("Payload layout verified")
