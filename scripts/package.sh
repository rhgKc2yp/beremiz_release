#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag=$(python3 -c 'import json; print(json.load(open("build/inputs.lock.json"))["tag"])')
arch=$(flatpak --default-arch)
name="beremiz-${tag#v}-$arch.tar.gz"
mkdir -p dist
tar --sort=name --owner=0 --group=0 --numeric-owner -czf "dist/$name" -C build beremiz
cp build/inputs.lock.json dist/SOURCES.lock.json
cp build/runtime-commits.json dist/RUNTIME-COMMITS.json
cp build/requirements.txt dist/requirements.txt
cp build/beremiz/SDK-MANIFEST.json dist/SDK-MANIFEST.json
cp build/beremiz/UBUNTU-PACKAGES.json dist/UBUNTU-PACKAGES.json
python3 scripts/source-index.py build/beremiz > dist/SOURCES.txt
# Corresponding unmodified application and PLC library sources accompany releases.
tar --sort=name --owner=0 --group=0 --numeric-owner -czf dist/application-sources.tar.gz \
    -C build/sources beremiz.tar.gz matiec.tar.gz Modbus.tar.gz canfestival.tar.gz open62541.tar.gz
python3 - build/beremiz dist/layout.txt <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
Path(sys.argv[2]).write_text('\n'.join(str(p.relative_to(root)) for p in sorted(root.rglob('*')) if p.is_file()) + '\n')
PY
(cd dist && sha256sum *.tar.gz *.json *.txt > SHA256SUMS)
