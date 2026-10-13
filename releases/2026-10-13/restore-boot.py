#!/usr/bin/env python3
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description='Restore the previous boot configuration.')
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
try:
    if os.geteuid() != 0:
        raise RuntimeError('Run with sudo.')
    root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location('boot', root / 'tools/kernel-boot.py')
    boot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(boot)
    boot.validate_root()
    copies = sorted(Path('/var/backups/kodi-kernel').glob('*/boot-links.json'))
    if not copies:
        raise RuntimeError('No boot backup was found.')
    mapping = json.loads(copies[-1].read_text())
    if set(mapping) != set(boot.LINKS):
        raise RuntimeError('Incomplete boot backup.')
    for name, target in mapping.items():
        if not (boot.BOOT / target).exists():
            raise RuntimeError(f'Previous kernel file is missing: {target}')
    if not args.check:
        boot.set_links(mapping)
    print(f'Backup: {copies[-1].parent}; restored={not args.check}. Restart when ready.')
except (OSError, RuntimeError, ValueError) as error:
    print(str(error), file=sys.stderr)
    sys.exit(1)
