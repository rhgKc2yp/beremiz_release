#!/usr/bin/env bash
# Run inside org.gnome.Sdk//51. Application sources remain unmodified.
set -euo pipefail
cd "$(dirname "$0")/.."
root=$PWD
bundle="$root/build/beremiz"
rm -rf "$bundle"
mkdir -p "$bundle"/{bin,lib,libexec,python} build/wheels dist
mkdir -p "$root/build/tmp"
# Keep native build scratch on workspace disk.
export TMPDIR="$root/build/tmp"
test -f build/inputs.lock.json
sources="$root/build/sources"

# wxPython is staged from Ubuntu, as in upstream's documented Linux setup.
python3 - "$sources/beremiz/requirements_pinned.txt" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
lines = [line for line in text.splitlines() if not line.lower().startswith('wxpython==')]
Path('build/requirements.txt').write_text('\n'.join(lines) + '\n# wxPython 4.2.4: see UBUNTU-PACKAGES.json\n')
PY
python3 -m pip wheel --no-clean --no-deps --find-links build/wheels --wheel-dir build/wheels -r build/requirements.txt
python3 -m pip install --no-index --no-deps --no-compile --target "$bundle/python" build/wheels/*.whl
python3 scripts/wx-deps.py install "$bundle"

cd "$sources/matiec"
autoreconf -fi
./configure
make -j"${BUILD_JOBS:-2}"
cd "$sources/Modbus"
make -j"${BUILD_JOBS:-2}"
cd "$sources/canfestival"
cmake -S . -B build -DCF_TARGET=unix '-DCF_CAN_DRIVER=virtual;socket' \
    -DCF_TIMERS_DRIVER=unix -DCMAKE_POSITION_INDEPENDENT_CODE=ON
cmake --build build -j"${BUILD_JOBS:-2}"
cd "$sources/open62541"
cmake -S . -B build -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DUA_FORCE_WERROR=OFF
cmake --build build -j"${BUILD_JOBS:-2}"
cd "$root"
for name in beremiz matiec Modbus canfestival open62541; do
    cp -a "$sources/$name" "$bundle/$name"
done
install -m755 scripts/environment "$bundle/libexec/environment"
for command in beremiz beremiz-cli beremiz-runtime beremiz-python; do
    install -m755 scripts/launcher "$bundle/bin/$command"
done
python3 scripts/toolchain.py "$bundle"
cp build/inputs.lock.json "$bundle/SOURCES.lock.json"
python3 -m pip list --path "$bundle/python" --format=json > "$bundle/PYTHON-PACKAGES.json"
cp build/runtime-commits.json "$bundle/RUNTIME-COMMITS.json"
cp "$sources/beremiz"/COPYING* "$bundle/"
find "$bundle" -type d -name .git -prune -exec rm -rf '{}' +
python3 scripts/check-layout.py "$bundle"
