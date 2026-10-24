#!/usr/bin/env bash
# Run on the Platform, offline, so SDK tools cannot mask missing dependencies.
set -euo pipefail
bundle=$(realpath "$1")
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
export XDG_CONFIG_HOME="$work/config" XDG_DATA_HOME="$work/data" XDG_CACHE_HOME="$work/cache"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_CACHE_HOME"
"$bundle/bin/beremiz-python" - "$bundle" <<'PY'
from pathlib import Path
import os, subprocess, sys
missing = []
for path in Path(sys.argv[1]).rglob('*'):
    if not path.is_file():
        continue
    with path.open('rb') as stream:
        if stream.read(4) != b'\x7fELF':
            continue
    env = os.environ.copy()
    # Auditwheel's private libraries inherit their importing extension's RPATH.
    # Check them with that sibling directory, as they are loaded by Python.
    if path.parent.name.endswith('.libs'):
        env['LD_LIBRARY_PATH'] = str(path.parent) + ':' + env.get('LD_LIBRARY_PATH', '')
    result = subprocess.run(['ldd', str(path)], capture_output=True, text=True, env=env)
    if 'not found' in result.stdout:
        missing.append(str(path) + '\n' + result.stdout)
if missing:
    raise SystemExit('\n'.join(missing))
print('ELF dependencies resolve on the Platform')
PY
"$bundle/bin/beremiz-python" -c 'import wx, lxml, matplotlib, erpc, OpenSSL, nevow, asyncua; print("Python imports OK", wx.version())'
"$bundle/bin/beremiz-python" - <<'PY'
from io import BytesIO
from PIL import Image
import numpy as np
assert np.dot([1, 2], [3, 4]) == 11
for codec in ('PNG', 'JPEG', 'WEBP', 'TIFF'):
    stream = BytesIO()
    Image.new('RGB', (8, 8), 'red').save(stream, format=codec)
    stream.seek(0)
    Image.open(stream).load()
print('Image codecs and numerical libraries work')
PY
"$bundle/bin/beremiz-cli" --help
cp -a "$bundle/beremiz/tests/projects/iec61131_lang_test" "$work/project"
"$bundle/bin/beremiz-cli" --project-home "$work/project" build
test -n "$(find "$work/project" -name '*.so' -print -quit)"
# Exercise upstream's IEC language test, with a bounded lifetime.
setsid timeout 120 "$bundle/bin/beremiz-cli" -k --project-home "$work/project" \
    build transfer run > "$work/runtime.log" 2>&1 &
client=$!
cleanup() {
    kill -- "-$client" 2>/dev/null || true
    wait "$client" 2>/dev/null || true
    rm -rf "$work"
}
trap cleanup EXIT
for ((i=0; i<110; i++)); do
    if grep -q 'ALL TESTS OK' "$work/runtime.log"; then
        cat "$work/runtime.log"
        echo 'Offline IEC compile, transfer and runtime test passed'
        exit 0
    fi
    if ! kill -0 "$client" 2>/dev/null; then break; fi
    sleep 1
done
cat "$work/runtime.log"
echo 'IEC runtime test did not report ALL TESTS OK' >&2
exit 1
