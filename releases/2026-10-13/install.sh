#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
sha256sum --quiet -c SHA256SUMS
exec python3 ./install.py "$@"
