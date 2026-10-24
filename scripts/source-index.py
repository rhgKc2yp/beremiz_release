#!/usr/bin/env python3
"""Write a readable index of application, Python and SDK source provenance."""
import json
from pathlib import Path
import sys

bundle = Path(sys.argv[1])
lock = json.loads((bundle / 'SOURCES.lock.json').read_text())
print('Beremiz community source build')
print('Upstream release:', lock['release_url'])
print('Distribution recipe commit:', lock['recipe_commit'])
print('\nApplication and PLC library sources (application-sources.tar.gz):')
for name, source in lock['sources'].items():
    print(f"{name}: {source['url']}\n  SHA-256: {source['sha256']}")
print('\nPython dependencies: exact versions and VCS commits in requirements.txt.')
print('Installed Python packages: PYTHON-PACKAGES.json inside the payload.')
print('\nDistribution wxPython and shared library sources (Ubuntu 26.04):')
for package in json.loads((bundle / 'UBUNTU-PACKAGES.json').read_text()):
    print(f"{package['package']} {package['version']}: {package['url']}")
    print(f"  Source package: {package['source']}; SHA-256: {package['sha256']}")
print('\nRuntime and compiler SDK commits:')
for ref, commit in json.loads((bundle / 'RUNTIME-COMMITS.json').read_text()).items():
    print(f'{ref}: {commit}')
print('\nCompiler/support component source records from SDK-MANIFEST.json:')
manifest = json.loads((bundle / 'SDK-MANIFEST.json').read_text())
seen = set()
for module in manifest['modules']:
    if not any(word in module['name'] for word in ('gcc-base', 'binutils', 'glibc', 'linux-headers', '/gmp.', '/mpfr.', '/mpc.', '/zstd.')):
        continue
    if module['name'] in seen:
        continue
    seen.add(module['name'])
    print(module['name'])
    for source in module['sources']:
        print('  ' + json.dumps(source, sort_keys=True))
print('\nThe payload retains component licence notices. Application sources are')
print('unmodified; the build scripts and SDK manifest document their build inputs.')
