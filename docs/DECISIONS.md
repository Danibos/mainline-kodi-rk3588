# Decisions

## Confirmed
- Mainline kernel only. No vendor RKMPP stack
- FFmpeg: upstream 8.1.2 + 4 patches (v4l2-request, v4l2-drmprime, vf-deinterlace, libreelec)
- Kodi: upstream xbmc + drmprime-filter patches
- Kernel: inindev linux-rockchip 7.1.1 + 7 audio passthrough patches
- GPU: Mesa Panfrost (system if ≥26.x)
- Display: DRM/KMS → GBM → GLES (no X11, no Wayland)
- Audio: ALSA → dw-hdmi-qp I2S → HDMI passthrough
- Video: V4L2 Request API → DRM PRIME → Kodi DRMPRIME renderer
- Target: Orange Pi 5 (RK3588S), Armbian/Debian
- Kodi boots to GDM autologin session (no desktop)

## Pending
- Kodi autologin via GDM working but not tested after restart
- NVME-only boot achieved but armbian-install MTD method was not used (manual config)
- CEC configuration
- HDR patches decision
