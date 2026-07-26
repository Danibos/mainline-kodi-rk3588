# Session Log — 2026-07-24/25

## Resumen

### Audio passthrough — Kernel en compilación
**Diagnóstico**: El kernel 7.1.1-3 no incluye parches IEC958/HBR → el driver dw-hdmi-qp siempre configura HDMI como PCM. Datos raw AC3/DTS enviados como PCM = ruido.

**Solución**: Recompilando kernel con fuente inindev/linux-rockchip v7.1.1 + 166 parches (159 Collabora + 7 audio IEC958/HBR passthrough).

**Cambios finales en el sistema**:
| Archivo | Cambio |
|---------|--------|
| `/etc/asound.conf` | `type plug` → conversión automática de formatos |
| `/etc/alsa/conf.d/` | Plugins PulseAudio desactivados |
| `~/.kodi/userdata/guisettings.xml` | ALSA:default + passthrough |
| `/usr/lib/aarch64-linux-gnu/kodi/kodi-gbm` | Recompilado con Python bindings + parches HDMI |

### Jellyfin, Keymap Editor, Python addons — SOLUCIONADO ✅
- Kodi recompilado con `-DENABLE_PYTHON=ON`
- Dependencias: python3-dev, swig, default-jdk-headless
- python3-websocket, python3-defusedxml instalados

### HW Decode
- Módulos rockchip_vdec, v4l2_h264, v4l2_vp9 cargados
- FFmpeg compilado con --enable-v4l2-request
- Pendiente probar con contenido real

### CEC
- Kernel compilado con CONFIG_DRM_DW_HDMI_QP_CEC=y
- Pendiente probar
