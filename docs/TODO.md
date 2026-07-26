## ✅ Completado

### Build & Run
- [x] Repo: Danibos/mainline-kodi-rk3588
- [x] FFmpeg 8.1.2 + v4l2-request/drmprime patches
- [x] Kodi 22 Piers GBM/GLES + Python bindings
- [x] NVMe boot
- [x] GDM autologin → Kodi
- [x] ALSA HDMI directo (asound.conf type plug)
- [x] PulseAudio/pipewire masked
- [x] Kodi patched: detección HDMI + stream types sin ELD

### Addons
- [x] Jellyfin: instalado, carga correctamente
- [x] Keymap Editor: instalado
- [x] python3-websocket, python3-defusedxml

### Kernel
- [x] Parches HBR/IEC958 aplicados sobre inindev v7.1.1
- [x] CEC: funcionando (control de volumen via HT-RT3 confirmado)
- [x] `/dev/cec0` funcional

## Pendiente
- [ ] HDMI audio passthrough: test con contenido AC-3/DTS real
- [ ] HW decode: test con video H.264/H.265
- [ ] HDR10/HDR10+ output
- [ ] glmark2-es2 (error "canvas init" - no crítico)
- [ ] SMB auto-credenciales
