#!/usr/bin/env python3
"""Check packaged files and runtime dependencies without modifying the live install."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'releases/2026-10-13'
WORK = ROOT / 'build/release-20261013'
MERGED = WORK / 'validation-root'
PREFIX = MERGED / 'opt/kodi-rk3588/22.0rc1'


def run(*args, **kw):
    return subprocess.run([str(a) for a in args], check=True, **kw)


def main():
    MERGED.mkdir(parents=True, exist_ok=True)
    metadata = []
    packages = sorted(OUT.glob('*.deb'))
    assert len(packages) == 7, 'Seven packages are required'
    for file in packages:
        fields = subprocess.check_output(['dpkg-deb', '-f', str(file), 'Package', 'Version', 'Architecture'], text=True)
        values = dict(line.split(': ', 1) for line in fields.splitlines())
        name = values['Package']
        role = 'headers' if name.startswith('linux-headers') else 'kernel' if name.startswith('linux-image') else 'runtime'
        with file.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        metadata.append({'file': file.name, 'package': name, 'version': values['Version'],
                         'architecture': values['Architecture'], 'role': role, 'sha256': digest})
        run('dpkg-deb', '-x', file, MERGED)
    (OUT / 'release.json').write_text(json.dumps({'target': 'Orange Pi 5 / Armbian Ubuntu 26.04 arm64',
        'kernel_version': '7.2.9-1-kodi-rk3588', 'packages': metadata}, indent=2) + '\n')
    env = {**os.environ, 'LD_LIBRARY_PATH': str(PREFIX / 'lib')}
    elf_count = 0
    ldd_output = []
    for file in PREFIX.rglob('*'):
        if not file.is_file() or file.is_symlink():
            continue
        with file.open('rb') as f:
            is_elf = f.read(4) == b'\x7fELF'
        if not is_elf:
            continue
        elf_count += 1
        dynamic = subprocess.check_output(['readelf', '-d', str(file)], text=True)
        assert '/home/' not in dynamic and '/build/' not in dynamic, str(file)
        result = subprocess.run(['ldd', str(file)], env=env, capture_output=True, text=True)
        ldd_output.append(str(file) + '\n' + result.stdout + result.stderr)
        assert result.returncode == 0 and 'not found' not in result.stdout, str(file)
        for name in re.findall(r'Shared library: \[([^]]+)\]', dynamic):
            if name.startswith(('libavcodec.', 'libavformat.', 'libavutil.', 'libavdevice.', 'libavfilter.', 'libswresample.', 'libswscale.', 'libpostproc.', 'libcec.')):
                assert (PREFIX / 'lib' / name).exists(), f'Unpackaged private library: {name}'
    (WORK / 'ldd-validation.log').write_text('\n'.join(ldd_output))
    core = PREFIX / 'lib/kodi/kodi.bin'
    version = subprocess.check_output([str(core), '--version'], env=env, text=True)
    assert '22.0' in version, version
    help_text = subprocess.check_output([str(core), '--help'], env=env, text=True)
    assert 'gbm, wayland' in help_text, help_text
    symbols = subprocess.check_output(['nm', '-D', str(PREFIX / 'lib/libcec.so')], text=True)
    assert 'CLinuxCECAdapterCommunication' in symbols
    sources = ROOT / 'build/kodi-release-generic/xbmc/platform/linux/input/LibInputKeyboard.cpp'
    assert not re.search(r'0x400[cC]|0x107[aA]|m_pulseActive', sources.read_text())
    addons = {}
    for file in (PREFIX / 'share/kodi/addons').glob('*/addon.xml'):
        root = ET.parse(file).getroot()
        addons[root.attrib['id']] = root
    youtube = addons['plugin.video.youtube']
    assert youtube.attrib['version'] == '7.4.4.1'
    assert addons['inputstream.adaptive'].attrib['version'] == '22.3.22'
    for name in ('plugin.video.youtube', 'script.module.requests', 'script.module.certifi',
                 'script.module.chardet', 'script.module.idna', 'script.module.urllib3'):
        for dependency in addons[name].findall('requires/import'):
            if dependency.get('optional') != 'true':
                assert dependency.get('addon') in addons, f'Missing dependency: {dependency.attrib}'
    settings = PREFIX / 'share/kodi/addons/plugin.video.youtube/resources/lib/youtube_plugin/kodion/settings/abstract_settings.py'
    tree = ast.parse(settings.read_text())
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'mpd_video_qualities')
    namespace = {'SETTINGS': type('Settings', (), {'MPD_QUALITY_SELECTION': 'quality'})}
    exec(compile(ast.Module(body=[method], type_ignores=[]), '<youtube-test>', 'exec'), namespace)
    for chosen, expected in ((7, 1080), (6, 1080), (4, 1080), (3, 720)):
        fake = type('Fake', (), {'use_mpd_videos': lambda self: True,
            'get_int': lambda self, key, default, chosen=chosen: chosen,
            '_QUALITY_SELECTIONS': {7: {'nom_height': 4320}, 6: {'nom_height': 2160},
                                   4: {'nom_height': 1080}, 3: {'nom_height': 720}}})()
        assert namespace['mpd_video_qualities'](fake)[0]['nom_height'] == expected
    # Check that the complete runtime dependency set can be resolved by apt.
    runtime = [OUT / p['file'] for p in metadata if p['role'] == 'runtime']
    result = run('apt-get', '-s', '--no-remove', 'install', *runtime, capture_output=True, text=True)
    (WORK / 'apt-simulation.log').write_text(result.stdout + result.stderr)
    report = {'elf_checked': elf_count, 'missing_libraries': 0, 'kodi_version': version.strip(),
              'window_systems': ['gbm', 'wayland'], 'linux_cec_backend': True,
              'device_specific_input_patch': False, 'inputstream_adaptive': '22.3.22',
              'youtube_profile_cap_test': 'passed', 'apt_simulation': 'passed',
              'clean_hardware_install': 'not performed'}
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
