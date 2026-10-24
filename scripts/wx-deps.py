#!/usr/bin/env python3
"""Stage the distribution wxPython dependency used by upstream's Linux setup."""
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

PACKAGES = {
    'universe': {'python3-wxgtk4.0', 'python3-wxgtk-webview4.0',
                 'libwxbase3.2-1t64', 'libwxgtk3.2-1t64',
                 'libwxgtk-gl3.2-1t64', 'libwxgtk-webview3.2-1t64'},
    'main': {'libjpeg-turbo8'},
}


def download(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def fetch(arch):
    distro_arch, base = {
        'x86_64': ('amd64', 'https://archive.ubuntu.com/ubuntu'),
        'aarch64': ('arm64', 'https://ports.ubuntu.com/ubuntu-ports'),
    }[arch]
    release = download(base + '/dists/resolute/Release').decode()
    checksums = {}
    section = ''
    for line in release.splitlines():
        if line and not line.startswith(' '):
            section = line.rstrip(':')
        elif section == 'SHA256':
            digest, size, filename = line.split()
            checksums[filename] = (digest, int(size))
    records = []
    cache = Path('build/ubuntu-wx') / arch
    cache.mkdir(parents=True, exist_ok=True)
    for component, wanted in PACKAGES.items():
        index_path = f'{component}/binary-{distro_arch}/Packages.xz'
        data = download(f'{base}/dists/resolute/{index_path}')
        digest, size = checksums[index_path]
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit('Ubuntu package index checksum mismatch')
        found = {}
        for paragraph in lzma.decompress(data).decode().split('\n\n'):
            fields = dict(line.split(': ', 1) for line in paragraph.splitlines()
                          if line and not line.startswith(' ') and ': ' in line)
            if fields.get('Package') in wanted:
                found[fields['Package']] = fields
        if set(found) != wanted:
            raise SystemExit(f'Missing Ubuntu packages: {wanted - set(found)}')
        for name, fields in sorted(found.items()):
            filename = Path(fields['Filename']).name
            url = base + '/' + fields['Filename']
            package = cache / filename
            if not package.exists():
                package.write_bytes(download(url))
            if package.stat().st_size != int(fields['Size']) or hashlib.sha256(package.read_bytes()).hexdigest() != fields['SHA256']:
                raise SystemExit('Ubuntu package checksum mismatch: ' + name)
            if name.startswith('python3-wxgtk') and not fields['Version'].startswith('4.2.4+'):
                raise SystemExit('Unexpected wxPython version: ' + fields['Version'])
            records.append({'package': name, 'version': fields['Version'],
                            'architecture': distro_arch, 'url': url,
                            'sha256': fields['SHA256'], 'size': int(fields['Size']),
                            'source': fields.get('Source', name), 'file': filename})
    (cache / 'packages.lock.json').write_text(json.dumps(records, indent=2) + '\n')
    print(f'Pinned Ubuntu 26.04 wxPython dependency for {arch}')


def install(bundle):
    arch = subprocess.check_output(['uname', '-m'], text=True).strip()
    cache = Path('build/ubuntu-wx') / arch
    records = json.loads((cache / 'packages.lock.json').read_text())
    stage = Path('build/ubuntu-wx-stage')
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    for record in records:
        package = cache / record['file']
        if hashlib.sha256(package.read_bytes()).hexdigest() != record['sha256']:
            raise SystemExit('Changed wxPython dependency archive')
        container = stage / 'deb'
        container.mkdir()
        subprocess.run(['bsdtar', '--no-same-owner', '-xf', str(package), '-C', str(container)], check=True)
        data, = container.glob('data.tar.*')
        subprocess.run(['bsdtar', '--no-same-owner', '-xf', str(data), '-C', str(stage)], check=True)
        shutil.rmtree(container)
    bundle = Path(bundle)
    python = stage / 'usr/lib/python3/dist-packages'
    shutil.copytree(python, bundle / 'python', dirs_exist_ok=True, symlinks=True)
    for source in (stage / 'usr/lib').rglob('*.so*'):
        if 'python3' in source.parts:
            continue
        target = bundle / 'lib' / source.name
        if source.is_symlink():
            target.symlink_to(source.readlink())
        else:
            shutil.copy2(source, target)
    notices = bundle / 'licenses/ubuntu'
    shutil.copytree(stage / 'usr/share/doc', notices, dirs_exist_ok=True, symlinks=True)
    shutil.copy2(cache / 'packages.lock.json', bundle / 'UBUNTU-PACKAGES.json')
    print('Staged unmodified distribution wxPython and its shared libraries')


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('fetch', 'install'):
        raise SystemExit('usage: wx-deps.py fetch ARCH | install BUNDLE')
    (fetch if sys.argv[1] == 'fetch' else install)(sys.argv[2])
