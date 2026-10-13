#!/usr/bin/env python3
"""Rebuild the pinned RK3588 update without replacing the running installation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'config/update-20261010.json').read_text())
WORK = ROOT / 'build/update-20261010'
PREFIX = MANIFEST['prefix']
MARKER = '.prepared-update-20261010'


def run(*args, cwd=None):
    subprocess.run([str(a) for a in args], cwd=cwd, check=True)


def download(url, destination, expected):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        temporary = destination.with_suffix(destination.suffix + '.partial')
        with urllib.request.urlopen(url, timeout=90) as response, temporary.open('wb') as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        temporary.replace(destination)
    with destination.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != expected:
        raise RuntimeError(f'Checksum incorrecto: {destination}')


def apply(source, patches):
    for patch in patches:
        run('patch', '--batch', '--forward', '-p1', '-i', patch.resolve(), cwd=source)


def prepare_tar(source, archive, url, checksum, patches):
    download(url, archive, checksum)
    if (source / MARKER).exists():
        return
    if source.exists():
        raise RuntimeError(f'Árbol sin marca de preparación; conservar y revisar: {source}')
    run('tar', '--no-same-owner', '-xf', archive, '-C', source.parent)
    apply(source, patches)
    (source / MARKER).write_text('prepared\n')


def kernel(prepare_only):
    for unit in ('kodi-kernel-build-20261010.service', 'kodi-kernel-resume-20261010.service'):
        state = subprocess.check_output(['systemctl', '--user', 'show', unit,
                                         '-p', 'ActiveState', '--value'], text=True).strip()
        if state in ('active', 'activating'):
            raise RuntimeError('El kernel ya se está compilando; no modificar su configuración.')
    base = ROOT / 'build/kernel-20261010'
    base.mkdir(parents=True, exist_ok=True)
    version = MANIFEST['kernel']['version']
    source = base / f'linux-{version}'
    patches = sorted((ROOT / f'patches/kernel-{version}').rglob('*.patch'))
    prepare_tar(source, base / f'linux-{version}.tar.xz',
                f'https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-{version}.tar.xz',
                MANIFEST['kernel']['sha256'], patches)
    run('make', 'ARCH=arm64', 'inindev_defconfig', cwd=source)
    run(source / 'scripts/config', '--file', source / '.config',
        '--enable', 'DRM_DW_HDMI_QP_CEC', '--enable', 'BLK_DEV_NVME',
        '--enable', 'NVME_CORE', '--enable', 'PCIE_ROCKCHIP_DW', '--enable', 'EXT4_FS',
        '--disable', 'DEBUG_INFO', '--enable', 'DEBUG_INFO_NONE',
        '--disable', 'DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT', '--disable', 'DEBUG_INFO_BTF')
    run('make', 'ARCH=arm64', 'olddefconfig', cwd=source)
    config = (source / '.config').read_text().splitlines()
    for option in ('DRM_DW_HDMI_QP_CEC', 'BLK_DEV_NVME', 'NVME_CORE',
                   'PCIE_ROCKCHIP_DW', 'EXT4_FS'):
        if f'CONFIG_{option}=y' not in config:
            raise RuntimeError(f'Configuración requerida ausente: {option}')
    if not prepare_only:
        run('make', '-j2', 'ARCH=arm64', 'LOCALVERSION=-1-kodi-rk3588',
            'KBUILD_BUILD_VERSION=1', 'bindeb-pkg', cwd=source)


def ffmpeg(prepare_only):
    for unit in ('kodi-ffmpeg-build-20261010.service', 'kodi-ffmpeg-resume-20261010.service'):
        state = subprocess.check_output(['systemctl', '--user', 'show', unit,
                                         '-p', 'ActiveState', '--value'], text=True).strip()
        if state in ('active', 'activating'):
            raise RuntimeError('FFmpeg ya se está compilando; no reconfigurar el árbol activo.')
    WORK.mkdir(parents=True, exist_ok=True)
    version = MANIFEST['ffmpeg']['version']
    source = WORK / f'ffmpeg-{version}'
    patches = []
    for group in ('postproc', 'libreelec', 'v4l2-request', 'detlev', 'vf-deinterlace-v4l2m2m'):
        patches.extend(sorted((ROOT / f'patches/ffmpeg-{version}' / group).glob('*.patch')))
    prepare_tar(source, WORK / f'ffmpeg-{version}.tar.xz',
                f'https://ffmpeg.org/releases/ffmpeg-{version}.tar.xz',
                MANIFEST['ffmpeg']['sha256'], patches)
    run('./configure', f'--prefix={PREFIX}', f'--libdir={PREFIX}/lib',
        '--enable-shared', '--disable-static', '--enable-gpl', '--disable-doc',
        '--disable-debug', '--enable-libdrm', '--enable-libudev', '--enable-v4l2-request',
        '--enable-libdav1d', '--enable-libass', '--enable-libopus', '--enable-libvorbis',
        '--enable-libmp3lame', '--enable-libsoxr', '--enable-libxml2', '--enable-gnutls',
        f'--extra-ldflags=-Wl,-rpath,{PREFIX}/lib', cwd=source)
    if not prepare_only:
        run('make', '-j2', cwd=source)
        # This prefix is isolated; system FFmpeg and running Kodi are preserved.
        run('sudo', '-n', 'make', 'install', cwd=source)


def kodi(prepare_only, profile="generic"):
    source = ROOT / ('build/kodi-release-generic' if profile == "generic" else 'build/kodi-20261010')
    if not source.exists():
        run('git', 'clone', '--depth=1', '--branch', MANIFEST['kodi']['tag'],
            'https://github.com/xbmc/xbmc.git', source)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if commit != MANIFEST['kodi']['commit']:
        raise RuntimeError('El commit de Kodi no coincide con el manifiesto')
    if not (source / MARKER).exists():
        patches = [ROOT / 'patches/kodi/0001-sqlite-busy-timeout.patch',
                   ROOT / 'patches/kodi/0003-alsa-retry-hw-params.patch']
        patches += sorted((ROOT / 'patches/kodi-22.0rc1/drmprime-filter').glob('*.patch'))
        patches += [p for p in sorted((ROOT / 'patches/kodi-22.0rc1/local').glob('*.patch'))
                    if not p.name.startswith('0007-')]
        apply(source, patches)
        (source / MARKER).write_text('prepared\n')
    build = WORK / ('kodi-release-generic-build' if profile == 'generic' else 'kodi-build')
    run('cmake', '-S', source, '-B', build, '-G', 'Ninja',
        f'-DCMAKE_INSTALL_PREFIX={PREFIX}', '-DCMAKE_BUILD_TYPE=Release',
        '-DCORE_PLATFORM_NAME=gbm wayland', '-DAPP_RENDER_SYSTEM=gles',
        '-DENABLE_INTERNAL_FFMPEG=OFF', f'-DFFMPEG_PATH={PREFIX}',
        '-DENABLE_INTERNAL_EXIV2=ON',
        '-DENABLE_INTERNAL_SWIG=ON',
        f'-DCMAKE_BUILD_RPATH={PREFIX}/lib', f'-DCMAKE_INSTALL_RPATH={PREFIX}/lib',
        '-DENABLE_ALSA=ON', '-DENABLE_PULSEAUDIO=OFF', '-DENABLE_PIPEWIRE=OFF',
        '-DENABLE_CEC=ON', '-DENABLE_INTERNAL_CEC=ON', '-DENABLE_MYSQL=OFF', '-DENABLE_MARIADB=OFF',
        '-DENABLE_SMBCLIENT=ON', '-DENABLE_NFS=ON')
    if not prepare_only:
        run('cmake', '--build', build, '--parallel', '2')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('component', choices=('kernel', 'ffmpeg', 'kodi'))
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--profile', choices=('generic', 'local'), default='generic',
                        help='Generic is the default release build profile.')
    options = parser.parse_args()
    if options.component == 'kodi':
        kodi(options.prepare_only, options.profile)
    else:
        globals()[options.component](options.prepare_only)
