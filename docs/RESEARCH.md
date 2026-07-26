# Research & Debug Findings

## 1. Audio Passthrough en RK3588 con dw-hdmi-qp

### El Problema (diagnóstico completo)
Kodi 22 no activa passthrough en HDMI del RK3588 por **4 causas simultáneas**:

1. **PipeWire/PulseAudio captura ALSA** — los servicios de audio de usuario y GDM toman `hw:hdmi0` dejando a Kodi sin acceso directo
2. **Plugins ALSA (pulse) en `/etc/alsa/conf.d/`** — hacen que `default` apunte a PulseAudio aunque `asound.conf` lo redefina
3. **No hay ELD en dw-hdmi-qp** — el driver del kernel no expone el control "ELD" (EDID Like Data) que Kodi usa para detectar formatos de passthrough (AC3, DTS, etc.)
4. **Kodi no reconoce `sysdefault:CARD=hdmi0` como HDMI** — `AEDeviceTypeFromName` solo busca nombres que *empiecen* con "hdmi"

### Solución aplicada

#### Nivel ALSA
```bash
# /etc/asound.conf
pcm.!default { type hw; card hdmi0; device 0; }
ctl.!default { type hw; card hdmi0; }
```
```bash
# Desactivar plugins PulseAudio
rm /etc/alsa/conf.d/99-pulse.conf
rm /etc/alsa/conf.d/50-pulseaudio.conf
```

#### Nivel systemd
```bash
systemctl --user mask pulseaudio pulseaudio.socket
systemctl --user mask pipewire-pulse.service pipewire-pulse.socket wireplumber.service
```

#### Nivel script de arranque (`kodi-alsa.sh`)
```bash
export KODI_AE_SINK=ALSA
pulseaudio --kill
pkill -u gdm pipewire pulseaudio
exec /usr/bin/kodi
```

#### Nivel Kodi (parches en AESinkALSA.cpp)
1. **AEDeviceTypeFromName**: busca `"hdmi"` en cualquier parte del nombre, no solo al inicio
2. **EnumerateDevice**: fuerza `AE_DEVTYPE_HDMI` si `snd_card_get_name` contiene "hdmi" aunque el device se llame "default"
3. **Stream types por defecto**: si `GetELD()` falla (no hay datos), añade AC3/DTS/EAC3/TrueHD/DTS-HD de todas formas

## 2. Python Bindings de Kodi (Jellyfin, addons)

### El Problema
El `build.sh` original compilaba Kodi **sin `-DENABLE_PYTHON=ON`**. Sin Python bindings (`xbmc.so`, `xbmcgui.so`), los addons de servicio (Jellyfin, versioncheck) no podían importar los módulos de Kodi y fallaban con "failed to start" genérico.

### Solución
1. Instalar dependencias: `python3-dev`, `swig`, `default-jdk-headless`
2. Añadir a cmake: `-DENABLE_PYTHON=ON -DPython3_EXECUTABLE=/usr/bin/python3 -DSWIG_EXECUTABLE=/usr/bin/swig`
3. Recompilar Kodi completo (los bindings SWIG generan archivos `.cpp` usando Java/Groovy)

### Archivos SWIG generados
- `AddonModuleXbmc.i.cpp` → módulo `xbmc`
- `AddonModuleXbmcgui.i.cpp` → módulo `xbmcgui`
- `AddonModuleXbmcaddon.i.cpp` → módulo `xbmcaddon`
- `AddonModuleXbmcplugin.i.cpp` → módulo `xbmcplugin`
- `AddonModuleXbmcvfs.i.cpp` → módulo `xbmcvfs`
- `AddonModuleXbmcwsgi.i.cpp` → módulo `xbmcwsgi`
- `AddonModuleXbmcdrm.i.cpp` → módulo `xbmcdrm`

## 3. HW Decode (V4L2 Request API)

Módulos cargados: `rockchip_vdec`, `v4l2_h264`, `v4l2_vp9`, `v4l2_jpeg`

FFmpeg compilado con `--enable-v4l2-request`. Kodi usará `v4l2-request` automáticamente para decodificación H.264/H.265.

## 4. CEC en dw-hdmi-qp

Módulo `cec` cargado y `dw_hdmi` presente, pero **no hay /dev/cec**. El driver `dw-hdmi-qp` no expone dispositivo CEC en el espacio de usuario. Kodi necesita `/dev/cec0` para usar CEC via libcec.

Posible solución: patch del kernel de Collabora `rockchip-0172-WIP-KNAERZCHE-drm-bridge-synopsys-fix-CEC-not-workin.patch`

## 5. CIFS en kernel

Kernel no compilado con `CONFIG_CIFS=y`. Kodi usa `libsmbclient` internamente (no requiere módulo cifs del kernel). Solo afecta montajes desde CLI.

## 6. EDID warnings

"Colorimetry Data Block: Reserved bits MD0-MD3 must be 0" y "Peak luminance index 0 is reserved" — warnings benignos del parser EDID de libdisplay-info. La TV reporta HDR10+ pero con bits de luminancia reservados. No afectan funcionalidad.

## 7. Compilación del kernel

### Fuente
- Repo: `https://github.com/inindev/linux-rockchip` (tag v7.1.1)
- Patches Collabora: 159 parches en `patches/01_collabora/` (RK3588 HDMI, GPU, VOP2, etc.)
- Patches audio: 7 parches en `patches/03_audio/` (IEC958 subframe, HBR detection, dw-hdmi-qp audio sequencing)
- Config extra: `CONFIG_DRM_DW_HDMI_QP_CEC=y` para CEC

### Build
```bash
cd ~/linux-rockchip
export STY=dummy  # bypass screen check
make -j$(nproc)   # 8 cores en OPI5
# Output: ../linux-image-7.1.1-*.deb
```

### Verificación HBR/IEC958
```bash
# Después de instalar kernel nuevo:
strings /lib/modules/*-arm64/kernel/sound/soc/rockchip/snd-soc-rockchip-i2s-tdm.ko.xz | xzcat | grep -i hbr
strings /lib/modules/*-arm64/kernel/drivers/gpu/drm/bridge/synopsys/dw-hdmi-qp.ko.xz | xzcat | grep -i hbr
# Deben aparecer símbolos HBR
```
