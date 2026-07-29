# Kodi RK3588 Mainline — v1.0

Kodi 22.0 with hardware video decoding for RK3588 (Orange Pi 5, etc.).

## Video formats

| Format | Resolution | Decoder |
|--------|-----------|---------|
| H.264 | 4K | V4L2 HW (rkvdec) |
| H.265 (HEVC) | 4K | V4L2 HW (rkvdec) |
| AV1 | 4K | V4L2 HW (hantro-vpu) |
| VP9 | 4K | V4L2 HW (rkvdec) |
| MPEG4 / Xvid | SD | Software (FFmpeg) |

> **Note:** HDR is not working yet. 4K HDR content plays in SDR. Under investigation.

**Audio**: multichannel passthrough (AC3, DTS, EAC3, TrueHD, DTS-HD).
**CEC**: HDMI control (tested with Sony HT-RT3 soundbar + TCL TV).

## Files

| File | Description |
|------|-------------|
| `linux-image-7.1.1-3-arm64_*.deb` | Kernel with HDMI audio + CEC |
| `linux-headers-7.1.1-3-arm64_*.deb` | Kernel headers |
| `linux-libc-dev_7.1.1-3_*.deb` | Development libraries |
| `ffmpeg-rk3588_*.deb` | FFmpeg with V4L2 support |
| `kodi-rk3588_22.0-beta1_*.deb` | Kodi |
| `kodi-rk3588-config_*.deb` | Audio + CEC config |
| `fix-cec.sh` | Fix script if CEC is broken |

## Install

```bash
sudo dpkg -i linux-*.deb
sudo dpkg -i ffmpeg-rk3588_*.deb
sudo dpkg -i kodi-rk3588_22.0-beta1_*.deb
sudo dpkg -i kodi-rk3588-config_*.deb
sudo apt-get install -f -y
sudo reboot
```

After reboot, go to **Settings → Player → Videos → Processing**:
- *Allow hardware acceleration with DRM PRIME* → **ON**
- *Prime Render Method* → **Direct To Plane**
- **Settings → System → Audio** → *Allow passthrough* → **ON**

## CEC not working?

```bash
sudo ./fix-cec.sh --remove-rpath
sudo systemctl restart gdm3
```

## Known issues

- **Estuary skin**: OSD seekbar lacks transparency when using Direct-to-Plane — use another skin or switch to EGL rendering.
- **HDR**: Not working yet. HDR content plays in SDR.
- **MPEG4**: Some packed B-frame files may show artifacts.
