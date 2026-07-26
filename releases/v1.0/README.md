# Kodi RK3588 Mainline — v1.0

Kodi 22.0 Beta 1 with hardware video decoding for RK3588 (Orange Pi 5, Rock 5B, etc.) on mainline kernel.

## What works

| Codec | Resolution | Decode | Render |
|-------|-----------|--------|--------|
| H.264 | up to 4K | V4L2 HW (rkvdec) | Direct-to-Plane NV12 |
| H.265 | up to 4K | V4L2 HW (rkvdec) | Direct-to-Plane NV15 |
| AV1 | up to 4K | V4L2 HW (hantro) | Direct-to-Plane NV15 |
| VP9 | up to 4K | V4L2 HW (rkvdec) | Direct-to-Plane |
| MPEG4/Xvid | SD | Software FFmpeg | LinuxRendererGLES |
| Audio | — | Passthrough | AC3/DTS/EAC3/TrueHD/DTS-HD |
| CEC | — | Pulse-Eight | HT-RT3 amplifier |

## Files

| File | Size | Description |
|------|------|-------------|
| `linux-image-7.1.1-3-arm64_7.1.1-3_arm64.deb` | 27 MB | Kernel 7.1.1 with HDMI audio + CEC patches |
| `linux-headers-7.1.1-3-arm64_7.1.1-3_arm64.deb` | 8.8 MB | Kernel headers |
| `linux-libc-dev_7.1.1-3_arm64.deb` | 1.5 MB | libc dev |
| `kodi-rk3588_22.0-beta1_arm64.deb` | 271 MB | Kodi with HW decode patches |
| `kodi-rk3588-config_1.0_all.deb` | 1.5 KB | ALSA config (audio passthrough + device cleanup) |

## Install

```bash
chmod +x install.sh
sudo ./install.sh
```

Or manually:

```bash
sudo dpkg -i linux-*.deb
sudo dpkg -i kodi-rk3588_22.0-beta1_arm64.deb
sudo dpkg -i kodi-rk3588-config_1.0_all.deb
sudo apt-get install -f -y
sudo reboot
```

## Kodi settings

After reboot, in Kodi go to **Settings > Player > Videos > Processing**:

- **Allow hardware acceleration with DRM PRIME** → ON
- **Allow hardware acceleration with DRM PRIME for HW codecs** → ON  
- **Prime Render Method** → **Direct To Plane**
- **Allow passthrough** → ON (for AC3/DTS/EAC3/TrueHD/DTS-HD)

## Kodi patches applied

| # | Patch | Source |
|---|-------|--------|
| 1 | Map HW AVFrame to DRM_PRIME | Jonas Karlman (Kwiboo) / LibreELEC |
| 2 | VideoLayerBridgeDRMPRIME release buffer early | Jonas Karlman (Kwiboo) / LibreELEC |
| 3 | HW_FRAMES_CTX method support | Custom (1 line) |
| 4 | Skip V4L2 wrapper decoders (v4l2m2m) | Custom (3 lines) |
| 5 | No HW config → fallback FFmpeg | Custom (5 lines) |

## Known issues

- **Estuary skin**: OSD seekbar lacks transparency with D2P. Use Arctic Fuse 2 or other skin.
- **HDR**: Detected but not fully configured in Kodi settings.
- **Some MPEG4 files with packed B-frames**: May need `mpeg4_unpack_bframes` bitstream filter.

## Build info

- Kernel: Linux 7.1.1-3-hbr-v3-arm64 (based on Collabora rk3588 tree)
- Kodi: 22.0-BETA1 (commit b6e1771, July 2026)
- FFmpeg: 8.1.2 with V4L2 request API
- Platform: Orange Pi 5, Ubuntu 24.04 arm64
