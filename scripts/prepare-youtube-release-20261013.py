#!/usr/bin/env python3
"""Fetch pinned public YouTube sources and Kodi Python modules for packaging."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'build/youtube-release-20261013'
MODULES = ROOT / 'build/release-20261013/modules'
COMMIT = '922cc0d2b3f2ffbee249d42e69ceaf4d0f34f5c7'
if not SOURCE.exists():
    subprocess.run(['git','clone','--depth=1','--branch','v7.4.4',
                    'https://github.com/anxdpanic/plugin.video.youtube.git',str(SOURCE)],check=True)
actual = subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()
if actual != COMMIT:
    raise RuntimeError('Unexpected YouTube source commit')
for patch in sorted((ROOT / 'patches/youtube-7.4.4').glob('*.patch')):
    command = ['patch','--batch','-p1','-i',str(patch)]
    forward = subprocess.run(command + ['--dry-run','--forward'],cwd=SOURCE,capture_output=True)
    if forward.returncode == 0:
        subprocess.run(command + ['--forward'],cwd=SOURCE,check=True)
    else:
        subprocess.run(command + ['--dry-run','--reverse'],cwd=SOURCE,check=True)
MODULES.mkdir(parents=True,exist_ok=True)
manifest = json.loads((ROOT / 'config/release-python-modules-20261013.json').read_text())
for module in manifest:
    with urllib.request.urlopen(module['url'],timeout=30) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != module['sha256']:
        raise RuntimeError('Module checksum mismatch: ' + module['addon'])
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if any(Path(n).is_absolute() or '..' in Path(n).parts for n in archive.namelist()):
            raise RuntimeError('Invalid module archive paths')
        archive.extractall(MODULES)
(MODULES / 'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Pinned YouTube sources and five public Kodi modules prepared.')
