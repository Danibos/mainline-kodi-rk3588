#!/bin/bash
# fix-cec.sh — Arregla el problema de libcec en Kodi RK3588
#
# Problema: si Kodi se compiló con ENABLE_INTERNAL_CEC=ON y el build system
# generó su propia libcec.so, ésta carece de CLinuxCECAdapterCommunication
# y no puede abrir /dev/cec0. Además el binario puede tener RUNPATH apuntando
# al directorio de build.
#
# Este script:
#   1. Detecta si el binario tiene RUNPATH a un dir de build
#   2. Si la libcec en ese path es la rota, la reemplaza con symlink a la del sistema
#   3. Opcionalmente, borra el RUNPATH del binario con patchelf
#
# Uso: sudo ./fix-cec.sh [--remove-rpath]

set -euo pipefail

KODI_BIN="/usr/lib/aarch64-linux-gnu/kodi/kodi-gbm"
SYSTEM_LIBCEC="/usr/lib/aarch64-linux-gnu/libcec.so.7"
REMOVE_RPATH=false

if [[ "${1:-}" == "--remove-rpath" ]]; then
    REMOVE_RPATH=true
fi

# ── 1. Detectar RUNPATH ──────────────────────────────────────────────
RUNPATH=$(readelf -d "$KODI_BIN" 2>/dev/null | grep -oP 'Library runpath:\s*\[\K[^]]+' || true)

if [[ -z "$RUNPATH" ]]; then
    echo "ℹ️  No RUNPATH encontrado en $KODI_BIN — el binario ya usa las librerías del sistema."
    echo "✅ No se necesita hacer nada. CEC debería funcionar con libcec del sistema."
    exit 0
fi

echo "⚠️  RUNPATH detectado: $RUNPATH"

# ── 2. Verificar cada path del RUNPATH ───────────────────────────────
FIXED=false
IFS=':' read -ra PATHS <<< "$RUNPATH"
for rpath in "${PATHS[@]}"; do
    LIBCEC="$rpath/libcec.so"
    if [[ -f "$LIBCEC" ]]; then
        # Ver si es la libcec rota (sin CLinuxCECAdapterCommunication)
        if ! nm -D "$LIBCEC" 2>/dev/null | grep -q "CLinuxCECAdapterCommunication"; then
            echo "🔧 libcec.so rota detectada en: $LIBCEC"
            echo "   → reemplazando con symlink a $SYSTEM_LIBCEC"

            cp "$LIBCEC" "${LIBCEC}.bak" 2>/dev/null || true
            ln -sf "$SYSTEM_LIBCEC" "$LIBCEC"
            FIXED=true
            echo "   ✅ Symlink creado: $LIBCEC → $SYSTEM_LIBCEC"
        else
            echo "ℹ️  $LIBCEC ya tiene soporte Linux CEC, no se modifica."
        fi
    fi
done

# ── 3. Opcional: borrar RUNPATH del binario ──────────────────────────
if $REMOVE_RPATH; then
    if command -v patchelf &>/dev/null; then
        echo "🔧 Eliminando RUNPATH del binario..."
        # Hay que parar Kodi para poder escribir el binario
        if pgrep kodi-gbm &>/dev/null; then
            echo "   Parando Kodi..."
            systemctl stop gdm3 2>/dev/null || true
            sleep 2
        fi
        patchelf --remove-rpath "$KODI_BIN"
        echo "   ✅ RUNPATH eliminado."
        systemctl start gdm3 2>/dev/null || true
    else
        echo "⚠️  patchelf no instalado. Instálalo con: sudo apt-get install patchelf"
        echo "   Luego ejecuta: sudo patchelf --remove-rpath $KODI_BIN"
    fi
fi

# ── 4. Verificar ─────────────────────────────────────────────────────
if $FIXED; then
    echo ""
    echo "✅ Fix aplicado. Reinicia Kodi para verificar:"
    echo "   sudo systemctl restart gdm3"
    echo ""
    echo "   Para verificar:"
    echo "   grep 'Register.*cec device registered' ~/.kodi/temp/kodi.log"
fi
