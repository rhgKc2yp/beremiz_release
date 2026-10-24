#!/usr/bin/env bash
# Host driver, also used unchanged by GitHub Actions.
set -euo pipefail
cd "$(dirname "$0")/.."
test -f build/inputs.lock.json
python3 scripts/wx-deps.py fetch "$(flatpak --default-arch)"
python3 - <<'PY'
import json
from pathlib import Path
import subprocess
refs = ['org.gnome.Sdk//51', 'org.gnome.Platform//51']
records = {ref: subprocess.check_output(['flatpak', 'info', '--show-commit', ref], text=True).strip() for ref in refs}
Path('build/runtime-commits.json').write_text(json.dumps(records, indent=2) + '\n')
PY
flatpak run --share=network --filesystem="$PWD" --command=bash org.gnome.Sdk//51 "$PWD/scripts/build.sh"
flatpak run --unshare=network --filesystem="$PWD" --command=bash org.gnome.Platform//51 \
    "$PWD/scripts/verify.sh" "$PWD/build/beremiz"
bash scripts/package.sh
mkdir -p build/archive-test
tar --no-same-owner -xzf dist/beremiz-*.tar.gz -C build/archive-test
flatpak run --unshare=network --filesystem="$PWD" --command=bash org.gnome.Platform//51 \
    "$PWD/scripts/verify.sh" "$PWD/build/archive-test/beremiz"
