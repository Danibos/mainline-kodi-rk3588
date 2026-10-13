#!/usr/bin/env python3
"""Install the reviewed release bundle on its supported Armbian base."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def check_host():
    release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    if release.get('ID', '').strip('"') != 'ubuntu' or release.get('VERSION_ID', '').strip('"') != '26.04':
        raise RuntimeError('Esta release requiere Armbian basado en Ubuntu 26.04.')
    arch = subprocess.check_output(['dpkg', '--print-architecture'], text=True).strip()
    if arch != 'arm64' or not Path('/etc/armbian-release').exists():
        raise RuntimeError('Se requiere Armbian arm64.')
    model = Path('/proc/device-tree/model').read_bytes().rstrip(b'\0').decode()
    if model != 'Xunlong Orange Pi 5':
        raise RuntimeError(f'Placa sin validar para esta release: {model}')
    if not Path('/boot/armbianEnv.txt').is_file():
        raise RuntimeError('No se reconoce el arranque de Armbian.')
    spec = importlib.util.spec_from_file_location('kernel_boot', ROOT / 'tools/kernel-boot.py')
    boot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(boot)
    boot.validate_root()
    for name in boot.LINKS:
        if not (boot.BOOT / name).is_symlink():
            raise RuntimeError(f'Es necesario revisar el arranque: /boot/{name} no es un enlace.')
    return boot


def check_bundle():
    manifest = json.loads((ROOT / 'release.json').read_text())
    for item in manifest['packages']:
        file = ROOT / item['file']
        with file.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != item['sha256']:
            raise RuntimeError(f'Archivo incompleto o alterado: {file.name}')
        actual = subprocess.check_output(['dpkg-deb', '-f', str(file), 'Package', 'Version', 'Architecture'], text=True)
        if item['package'] not in actual or item['version'] not in actual:
            raise RuntimeError(f'Paquete inesperado: {file.name}')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Comprobar sin instalar')
    parser.add_argument('--with-headers', action='store_true', help='Instalar cabeceras del kernel')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise RuntimeError('Ejecuta sudo ./install.sh; usa --check para comprobar sin instalar.')
    manifest = check_bundle()
    boot = check_host()
    image = next(p for p in manifest['packages'] if p['role'] == 'kernel')
    version = manifest['kernel_version']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.+_-]*', version):
        raise RuntimeError('Versión de kernel inválida.')
    print('Orange Pi 5, Ubuntu 26.04, paquetes y esquema de arranque comprobados.', flush=True)
    if args.check:
        print('Comprobación terminada. No se ha instalado ni cambiado nada.')
        return
    # Retain the old kernel and use the same rollback-aware activation helper.
    runtime = [ROOT / p['file'] for p in manifest['packages'] if p['role'] == 'runtime']
    run('apt-get', '--no-remove', 'install', '-y', 'initramfs-tools', 'u-boot-tools', *runtime)
    command = [sys.executable, ROOT / 'tools/kernel-boot.py', version,
               '--image-deb', ROOT / image['file'], '--activate']
    if args.with_headers:
        headers = next(p for p in manifest['packages'] if p['role'] == 'headers')
        command += ['--headers-deb', ROOT / headers['file']]
    run(*command)
    print('Instalación terminada. Reinicia cuando quieras y elige Kodi GBM o Kodi Wayland en el inicio de sesión.')
    print('Se conserva el kernel anterior y el respaldo de arranque en /var/backups/kodi-kernel/.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f'No se ha completado la instalación: {error}', file=sys.stderr)
        sys.exit(1)
