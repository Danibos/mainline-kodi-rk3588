#!/usr/bin/env python3
"""Validate/install a kernel and switch Armbian boot links as one checked operation."""
import argparse
import gzip
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zlib

BOOT = Path('/boot')
LINKS = ('Image', 'vmlinuz', 'uInitrd', 'initrd.img', 'dtb')
REQUIRED = ('BLK_DEV_NVME', 'NVME_CORE', 'PCIE_ROCKCHIP_DW', 'EXT4_FS')


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def validate_root():
    if output('findmnt', '-n', '-o', 'FSTYPE', '/') != 'ext4':
        raise RuntimeError('This release requires an ext4 root filesystem.')
    source = output('findmnt', '-n', '-o', 'SOURCE', '/')
    if not re.fullmatch(r'/dev/(?:nvme[0-9]+n[0-9]+p[0-9]+|mmcblk[0-9]+p[0-9]+|sd[a-z]+[0-9]+)', source):
        raise RuntimeError(f'Unsupported root partition: {source}')
    uuid = output('blkid', '-s', 'UUID', '-o', 'value', source)
    environment = (BOOT / 'armbianEnv.txt').read_text().splitlines()
    if f'rootdev=UUID={uuid}' not in environment:
        raise RuntimeError('Root UUID does not match armbianEnv.txt')
    entries = [line.split() for line in Path('/etc/fstab').read_text().splitlines()
               if line.strip() and not line.lstrip().startswith('#')]
    if any(len(fields) < 4 for fields in entries):
        raise RuntimeError('fstab contains incomplete entries')
    if not any(fields[0] == f'UUID={uuid}' and fields[1] == '/' for fields in entries):
        raise RuntimeError('Root UUID does not match fstab')


def validate_config(config):
    lines = config.read_text().splitlines()
    for symbol in REQUIRED:
        if f'CONFIG_{symbol}=y' not in lines:
            raise RuntimeError(f'Boot requires CONFIG_{symbol}=y')


def prepare_image(image):
    """Armbian's boot script expects an uncompressed ARM64 Image."""
    with image.open('rb') as stream:
        compressed = stream.read(2) == b'\x1f\x8b'
    if not compressed:
        return
    payload = gzip.decompress(image.read_bytes())
    if payload[56:60] != b'ARM\x64':
        raise RuntimeError('Decompressed image has no ARM64 header')
    temporary = image.with_name(image.name + '.uncompressed')
    temporary.write_bytes(payload)
    shutil.copymode(image, temporary)
    os.replace(temporary, image)


def validate_candidate(version):
    validate_config(BOOT / f'config-{version}')
    image = BOOT / f'vmlinuz-{version}'
    with image.open('rb') as stream:
        header = stream.read(64)
    if header[56:60] != b'ARM\x64':
        raise RuntimeError('Image has no ARM64 header')
    dtb = BOOT / f'dtb-{version}/rockchip/rk3588s-orangepi-5.dtb'
    with dtb.open('rb') as stream:
        if stream.read(4) != b'\xd0\x0d\xfe\xed':
            raise RuntimeError('Invalid Orange Pi 5 DTB')
    if not Path(f'/lib/modules/{version}').is_dir():
        raise RuntimeError('Kernel modules are missing')
    ramdisk = (BOOT / f'uInitrd-{version}').read_bytes()
    initrd = (BOOT / f'initrd.img-{version}').read_bytes()
    if ramdisk[:4] != b'\x27\x05\x19\x56' or ramdisk[64:] != initrd:
        raise RuntimeError('uInitrd does not match this kernel initramfs')
    if int.from_bytes(ramdisk[24:28], 'big') != zlib.crc32(initrd):
        raise RuntimeError('Invalid uInitrd CRC')
    inventory = output('lsinitramfs', str(BOOT / f'initrd.img-{version}'))
    versions = set(re.findall(r'(?:usr/)?lib/modules/([^/\n]+)', inventory))
    if versions != {version}:
        raise RuntimeError(f'Unexpected versions in initramfs: {versions}')


def targets(version):
    return {'Image': f'vmlinuz-{version}', 'vmlinuz': f'vmlinuz-{version}',
            'uInitrd': f'uInitrd-{version}', 'initrd.img': f'initrd.img-{version}',
            'dtb': f'dtb-{version}'}


def set_links(mapping):
    for name, target in mapping.items():
        temporary = BOOT / f'.{name}.nvme-new'
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(target)
        os.replace(temporary, BOOT / name)
    os.sync()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('--image-deb', type=Path)
    parser.add_argument('--headers-deb', type=Path)
    parser.add_argument('--activate', action='store_true',
                        help='Switch all boot links after validating the candidate')
    args = parser.parse_args()
    if args.headers_deb and not args.image_deb:
        parser.error('--headers-deb requires --image-deb')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.+_-]*', args.version):
        parser.error('Invalid version')
    if os.geteuid() != 0:
        parser.error('Run with sudo to verify the root UUID')
    validate_root()
    if args.image_deb or args.activate:
        previous = {}
        for name in LINKS:
            path = BOOT / name
            if not path.is_symlink():
                raise RuntimeError(f'Expected a symbolic link: {path}')
            previous[name] = os.readlink(path)
        backup = Path('/var/backups/kodi-kernel') / datetime.now().strftime('%Y%m%d-%H%M%S')
        backup.mkdir(parents=True, mode=0o700)
        (backup / 'boot-links.json').write_text(json.dumps(previous, indent=2) + '\n')
        shutil.copy2('/etc/fstab', backup / 'fstab')
        shutil.copy2(BOOT / 'armbianEnv.txt', backup / 'armbianEnv.txt')
        try:
            if args.image_deb:
                package = args.image_deb.resolve()
                if output('dpkg-deb', '-f', str(package), 'Package') != f'linux-image-{args.version}':
                    raise RuntimeError('Package does not contain the requested kernel image')
                if output('dpkg-deb', '-f', str(package), 'Architecture') != 'arm64':
                    raise RuntimeError('Incorrect package architecture')
                # Validate root-storage drivers before any kernel postinst can alter boot.
                with tempfile.TemporaryDirectory(prefix='kodi-kernel-check-') as staging:
                    subprocess.run(['dpkg-deb', '-x', str(package), staging], check=True)
                    validate_config(Path(staging) / f'boot/config-{args.version}')
                hook = Path(__file__).resolve().parents[1] / 'config/zz-kodi-keep-selected-initrd'
                subprocess.run(['install', '-m', '755', str(hook),
                                '/etc/initramfs/post-update.d/zz-kodi-keep-selected-initrd'], check=True)
                packages = [str(package)]
                if args.headers_deb:
                    headers = args.headers_deb.resolve()
                    if output('dpkg-deb', '-f', str(headers), 'Package') != f'linux-headers-{args.version}':
                        raise RuntimeError('Headers package does not match the kernel')
                    if output('dpkg-deb', '-f', str(headers), 'Architecture') != 'arm64':
                        raise RuntimeError('Incorrect headers architecture')
                    packages.append(str(headers))
                subprocess.run(['dpkg', '-i', *packages], check=True)
                # Armbian's initramfs hook may have moved only uInitrd. Restore the
                # known-good set immediately, even when merely staging the new kernel.
                set_links(previous)
                prepare_image(BOOT / f'vmlinuz-{args.version}')
                dtb_source = Path(f'/usr/lib/linux-image-{args.version}')
                destination = BOOT / f'dtb-{args.version}'
                if not destination.exists():
                    shutil.copytree(dtb_source, destination)
                if not (BOOT / f'initrd.img-{args.version}').exists():
                    subprocess.run(['update-initramfs', '-c', '-k', args.version], check=True)
                    set_links(previous)
            validate_candidate(args.version)
            if args.activate:
                set_links(targets(args.version))
                if any(os.readlink(BOOT / name) != target
                       for name, target in targets(args.version).items()):
                    raise RuntimeError('Boot links do not match the selected kernel')
            print(f'Kernel {args.version} verified; activated={args.activate}; backup={backup}')
        except BaseException:
            set_links(previous)
            raise
    else:
        validate_candidate(args.version)
        print(f'Kernel {args.version}: root, image, DTB and initramfs verified')


if __name__ == '__main__':
    main()
