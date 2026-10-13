#!/usr/bin/env python3
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description='Restaurar los enlaces del arranque anterior; conserva los paquetes.')
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
try:
    if os.geteuid() != 0:
        raise RuntimeError('Ejecuta con sudo.')
    root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location('boot', root / 'tools/kernel-boot.py')
    boot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(boot)
    boot.validate_root()
    copies = sorted(Path('/var/backups/kodi-kernel').glob('*/boot-links.json'))
    if not copies:
        raise RuntimeError('No se encuentra un respaldo del arranque.')
    mapping = json.loads(copies[-1].read_text())
    if set(mapping) != set(boot.LINKS):
        raise RuntimeError('Respaldo incompleto.')
    for name, target in mapping.items():
        if not (boot.BOOT / target).exists():
            raise RuntimeError(f'Ya no existe el archivo del kernel anterior: {target}')
    if not args.check:
        boot.set_links(mapping)
    print(f'Respaldo: {copies[-1].parent}; restaurado={not args.check}. Reinicia cuando quieras.')
except (OSError, RuntimeError, ValueError) as error:
    print(str(error), file=sys.stderr)
    sys.exit(1)
