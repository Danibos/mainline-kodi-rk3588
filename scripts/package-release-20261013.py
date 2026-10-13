#!/usr/bin/env python3
"""Package the generic build into local release artifacts; never install or publish."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'build/release-20261013'
OUT = ROOT / 'releases/2026-10-13'
PREFIX = Path('opt/kodi-rk3588/22.0rc1')
VERSION = '22.0rc1-20261013.1'
FFVERSION = '9.0.2-20261013.1'
CORE_BUILD = ROOT / 'build/update-20261010/kodi-release-generic-build'
CORE_SOURCE = ROOT / 'build/kodi-release-generic'
LIVE = Path('/') / PREFIX


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def fresh(name):
    stage = WORK / name
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    return stage


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, symlinks=True,
                        ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '*.log'))
    else:
        shutil.copy2(source, target, follow_symlinks=False)


def elf_files(stage):
    for p in stage.rglob('*'):
        if p.is_file() and not p.is_symlink():
            with p.open('rb') as f:
                if f.read(4) == b'\x7fELF':
                    yield p


def normalize_elf(stage):
    for file in elf_files(stage):
        # Runtime libs share one isolated prefix; no build directory is needed.
        run('patchelf', '--set-rpath', '/opt/kodi-rk3588/22.0rc1/lib', file)
        dynamic = subprocess.check_output(['readelf', '-d', str(file)], text=True)
        if '/home/' in dynamic or '/build/' in dynamic:
            raise RuntimeError(f'Development path in {file}')


def document(stage, name, source, license_files):
    doc = stage / 'usr/share/doc' / name
    doc.mkdir(parents=True, exist_ok=True)
    (doc / 'sources.json').write_text(json.dumps(source, indent=2) + '\n')
    for file in license_files:
        copy(file, doc / file.name)


def deb(stage, name, version, description, extra_depends='', architecture='arm64'):
    normalize_elf(stage)
    elf = list(elf_files(stage))
    depends = extra_depends
    if elf:
        metadata = WORK / 'shlibdeps'
        (metadata / 'debian').mkdir(parents=True, exist_ok=True)
        (metadata / 'debian/control').write_text(
            f'Source: {name}\nSection: video\nPriority: optional\nMaintainer: Dani <dani@localhost>\n\n'
            f'Package: {name}\nArchitecture: arm64\nDescription: {description}\n')
        directories = [stage / PREFIX / 'lib', WORK / 'ffmpeg' / PREFIX / 'lib',
                       WORK / 'kodi' / PREFIX / 'lib']
        command = ['dpkg-shlibdeps', '--ignore-missing-info', '-O']
        command += ['-l' + str(p) for p in directories if p.exists()]
        command += ['-e' + str(p) for p in elf]
        result = subprocess.run(command, cwd=metadata, check=True, text=True, capture_output=True)
        (WORK / f'{name}-shlibdeps.log').write_text(result.stdout + result.stderr)
        calculated = result.stdout.strip().removeprefix('shlibs:Depends=')
        depends = ', '.join(filter(None, [depends, calculated]))
    control = stage / 'DEBIAN'
    control.mkdir(exist_ok=True)
    (control / 'control').write_text(
        f'Package: {name}\nVersion: {version}\nArchitecture: {architecture}\n'
        'Maintainer: Dani <dani@localhost>\nSection: video\nPriority: optional\n'
        + (f'Depends: {depends}\n' if depends else '')
        + f'Description: {description}\n RK3588 release for Orange Pi 5 and Ubuntu 26.04 arm64.\n')
    target = OUT / f'{name}_{version}_{architecture}.deb'
    run('dpkg-deb', '--root-owner-group', '-Zxz', '-z6', '--threads-max=2', '--build', stage, target)
    return target


def ffmpeg():
    stage = fresh('ffmpeg')
    for file in (LIVE / 'lib').glob('lib*.so*'):
        if file.name.startswith(('libav', 'libsw', 'libpostproc')):
            copy(file, stage / PREFIX / 'lib' / file.name)
    for name in ('ffmpeg', 'ffprobe'):
        copy(LIVE / 'bin' / name, stage / PREFIX / 'bin' / name)
    source = ROOT / 'build/update-20261010/ffmpeg-9.0.2'
    manifest = json.loads((ROOT / 'config/update-20261010.json').read_text())
    document(stage, 'ffmpeg-rk3588', manifest['ffmpeg'],
             [source / 'COPYING.GPLv2', source / 'LICENSE.md'])
    return deb(stage, 'ffmpeg-rk3588', FFVERSION, 'FFmpeg 9.0.2 with V4L2 Request decoding')


def kodi():
    stage = fresh('kodi')
    run('cmake', '--install', CORE_BUILD, env={**os.environ, 'DESTDIR': str(stage)})
    # CMake's internal libCEC build is not part of the Kodi install manifest.
    copy(CORE_BUILD / 'build/lib/libcec.so', stage / PREFIX / 'lib/libcec.so')
    for name in ('kodi-rk3588-gbm.desktop', 'kodi-rk3588-wayland.desktop'):
        copy(ROOT / 'config' / name, stage / 'usr/share/wayland-sessions' / name)
    copy(ROOT / 'config/kodi-rk3588-gbm.desktop', stage / 'usr/share/xsessions/kodi-rk3588-gbm.desktop')
    copy(ROOT / 'config/kodi-rk3588-wayland', stage / 'usr/bin/kodi-rk3588-wayland')
    desktop = stage / 'usr/share/wayland-sessions/kodi-rk3588-wayland.desktop'
    desktop.write_text(desktop.read_text().replace('/usr/local/bin/', '/usr/bin/'))
    os.chmod(stage / 'usr/bin/kodi-rk3588-wayland', 0o755)
    rules = stage / 'usr/lib/udev/rules.d/70-kodi-rk3588-cec.rules'
    rules.parent.mkdir(parents=True, exist_ok=True)
    rules.write_text('SUBSYSTEM=="cec", TAG+="uaccess", GROUP="video", MODE="0660"\n')
    sources = json.loads((ROOT / 'config/update-20261010.json').read_text())
    sources['profile'] = 'generic'
    sources['patches'] = [p.name for p in sorted((ROOT / 'patches/kodi-22.0rc1/local').glob('*.patch'))
                         if not p.name.startswith('0007-')]
    document(stage, 'kodi-rk3588', sources, [CORE_SOURCE / 'LICENSE.md'])
    for dependency, filename in (('cec', 'LICENSE.md'), ('libdvdnav', 'COPYING'),
                                  ('libdvdread', 'COPYING'), ('libdvdcss', 'COPYING'),
                                  ('exiv2', 'COPYING')):
        license_file = CORE_BUILD / f'build/build-{dependency}/src/build-{dependency}' / filename
        if not license_file.exists():
            raise RuntimeError(f'Missing third-party license: {license_file}')
        copy(license_file, stage / 'usr/share/doc/kodi-rk3588/third-party' / dependency / filename)
    return deb(stage, 'kodi-rk3588', VERSION, 'Kodi 22 RC1 with GBM, Wayland and Linux CEC',
               f'ffmpeg-rk3588 (= {FFVERSION}), weston, xkb-data, python3, udev')


def adaptive():
    stage = fresh('adaptive')
    for section in ('lib', 'share'):
        source = LIVE / section / 'kodi/addons/inputstream.adaptive'
        copy(source, stage / PREFIX / section / 'kodi/addons/inputstream.adaptive')
    source = ROOT / 'build/update-20261010/inputstream.adaptive'
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    expected = json.loads((ROOT / 'config/update-20261010.json').read_text())['inputstream_adaptive']['commit']
    if commit != expected:
        raise RuntimeError('Adaptive source does not match the pinned manifest')
    document(stage, 'kodi-rk3588-inputstream-adaptive', {'commit': commit, 'version': '22.3.22'},
             [source / 'LICENSE.md'])
    return deb(stage, 'kodi-rk3588-inputstream-adaptive', '22.3.22-20261013.1',
               'InputStream Adaptive for Kodi 22 DASH and HLS', f'kodi-rk3588 (= {VERSION})')


def youtube():
    stage = fresh('youtube')
    source = ROOT / 'build/youtube-release-20261013'
    target = stage / PREFIX / 'share/kodi/addons/plugin.video.youtube'
    copy(source, target)
    client = target / 'resources/lib/youtube_plugin/youtube/client/player_client.py'
    if '# Disabled locally: ANDROID_VR' not in client.read_text():
        raise RuntimeError('Missing HTTP403 workaround')
    settings = target / 'resources/lib/youtube_plugin/kodion/settings/abstract_settings.py'
    if 'min(4, self.get_int(SETTINGS.MPD_QUALITY_SELECTION, 4))' not in settings.read_text():
        raise RuntimeError('Missing DASH resolution cap')
    p = target / 'addon.xml'
    p.write_text(p.read_text().replace('version="7.4.4"', 'version="7.4.4.1"', 1))
    dependencies = []
    for addon in ('requests', 'certifi', 'chardet', 'idna', 'urllib3'):
        directory = WORK / 'modules' / f'script.module.{addon}'
        copy(directory, stage / PREFIX / 'share/kodi/addons' / directory.name)
        dependencies.append(ET.parse(directory / 'addon.xml').getroot().attrib)
    document(stage, 'kodi-rk3588-youtube',
             {'upstream': 'https://github.com/anxdpanic/plugin.video.youtube',
              'commit': '922cc0d2b3f2ffbee249d42e69ceaf4d0f34f5c7',
              'version': '7.4.4.1', 'max_dash_height': 1080, 'modules': dependencies,
              'module_sources': json.loads((WORK / 'modules/sources.json').read_text())},
             [source / 'LICENSES/GPL-2.0-only'])
    return deb(stage, 'kodi-rk3588-youtube', '7.4.4-20261013.1',
               'YouTube with download workaround and 1080p DASH support',
               'kodi-rk3588-inputstream-adaptive (= 22.3.22-20261013.1)', architecture='all')


def visualizers():
    stage = fresh('visualizers')
    original = ROOT / 'releases/2026-10-12/visualizations/kodi-rk3588-visualizations_22.0rc1-20261012.3_arm64.deb'
    run('dpkg-deb', '-x', original, stage)
    return deb(stage, 'kodi-rk3588-visualizations', VERSION,
               'Shadertoy, Goom, FishBMC, Spectrum and Waveform GLES visualizers', f'kodi-rk3588 (= {VERSION})')


def kernel():
    files = []
    for kind in ('image', 'headers'):
        name = f'linux-{kind}-7.2.9-1-kodi-rk3588_7.2.9-2_arm64.deb'
        copy(ROOT / 'build/kernel-20261010' / name, OUT / name)
        files.append(OUT / name)
    return files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', nargs='+', choices=('ffmpeg', 'kodi', 'adaptive', 'youtube', 'visualizers', 'kernel'),
                        default=['ffmpeg', 'kodi', 'adaptive', 'youtube', 'visualizers', 'kernel'])
    options = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for component in options.components:
        globals()[component]()
    files = sorted(OUT.glob('*.deb'))
    sums = [hashlib.file_digest(p.open('rb'), 'sha256').hexdigest() + '  ' + p.name for p in files]
    (OUT / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')
    print('Local artifacts:', len(files))
