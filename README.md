# Kodi RK3588 Mainline

[![Kernel](https://img.shields.io/badge/kernel-mainline-success)](#)
[![SoC](https://img.shields.io/badge/soc-RK3588-blue)](#)
[![Kodi](https://img.shields.io/badge/kodi-22.0-orange)](https://github.com/xbmc/xbmc)
[![Armbian](https://img.shields.io/badge/base-Armbian-green)](#)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

Kodi 22.0 with hardware video decoding for RK3588 boards, running on a **mainline Linux kernel**.

## Why this exists

Getting Kodi to work with hardware video decoding on RK3588 boards isn't always straightforward. These chips need the **V4L2 Request API** — a standard mainline kernel interface — but most pre-built Kodi images for RK3588 rely on vendor-specific BSP stacks that are hard to customize and maintain.

This project takes a different approach: a clean build of Kodi on **upstream mainline Linux**, using standard kernel interfaces (DRM/KMS, V4L2 Request API, ALSA) with zero reliance on vendor blobs. Tested on **[Armbian](https://www.armbian.com/)** (minimal Debian and Ubuntu 24.04). Everything is packaged into a few `.deb` files so you can install it and get on with your day.

## Current Status

| Feature | Status |
|---------|--------|
| Kodi 22.0 (GBM/GLES) | ✅ Stable |
| H.264 HW decode | ✅ |
| H.265 (HEVC) HW decode | ✅ |
| AV1 HW decode | ✅ |
| VP9 HW decode | ✅ |
| MPEG4 / Xvid (SW) | ✅ |
| HDMI Audio (PCM) | ✅ |
| Audio Passthrough (AC3/DTS/EAC3/TrueHD/DTS-HD) | ✅ |
| CEC | ✅ |
| 4K playback | ✅ |
| Daily use | ✅ Stable |
| HDR | ⚠️ In progress |

## Architecture

```
Linux Mainline Kernel (DRM/KMS)
        ↓
      Mesa (Panfrost/GBM)
        ↓
     FFmpeg (V4L2 Request API)
        ↓
      Kodi (GBM/GLES)
        ↓
      HDMI Output
```

All video decoding goes through the **V4L2 Request API** with zero-copy DRM PRIME buffers. Audio uses **ALSA** directly (no PulseAudio/PipeWire). The display stack uses **DRM/KMS + GBM + GLES** — no X11, no Wayland.

## Supported devices

| Board | Status |
|-------|--------|
| Orange Pi 5 | ✅ Tested |
| Rock 5B | ❓ Expected to work (untested) |
| Orange Pi 5 Plus | ❓ Expected to work (untested) |

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

## Install

1. Download the `.deb` packages from [Releases](https://github.com/Danibos/mainline-kodi-rk3588/releases)

2. Install all packages:
```bash
sudo dpkg -i linux-*.deb
sudo dpkg -i kodi-rk3588_*.deb
sudo dpkg -i kodi-rk3588-config_*.deb
sudo apt-get install -f -y
sudo reboot
```

3. After reboot, Kodi starts automatically. Go to **Settings → Player → Videos → Processing**:
   - *Allow hardware acceleration with DRM PRIME* → **ON**
   - *Prime Render Method* → **Direct To Plane**
   - **Settings → System → Audio** → *Allow passthrough* → **ON**

## CEC not working?

Run the fix script included in the release:
```bash
sudo ./fix-cec.sh --remove-rpath
sudo systemctl restart gdm3
```

Verify:
```bash
grep "Register.*cec device registered" ~/.kodi/temp/kodi.log
```

## Known issues

- **Estuary skin**: OSD seekbar lacks transparency when using Direct-to-Plane. Use another skin (Arctic Fuse 2, etc.) or switch to EGL rendering.
- **Some MPEG4 files** with packed B-frames may show artifacts.
- **HDR**: Not working yet. HDR content plays in SDR.

## License

The scripts and documentation in this repository are licensed under [MIT](LICENSE).

The binary packages distributed in [Releases](https://github.com/Danibos/mainline-kodi-rk3588/releases) contain third-party components under their own licenses:

| Component | License |
|-----------|---------|
| Linux kernel | [GPL-2.0](https://www.kernel.org/doc/html/latest/process/license-rules.html) |
| Kodi | [GPL-2.0](https://github.com/xbmc/xbmc/blob/master/LICENSE.md) |
| FFmpeg | [LGPL-2.1+ / GPL-2.0+](https://ffmpeg.org/legal.html) |

Source code for these components, including all patches and build instructions, is available at the upstream links listed in [SOURCES.md](SOURCES.md).

## Acknowledgments

This project wouldn't exist without the work of many people who share their knowledge openly:

- The **[Collabora](https://www.collabora.com/)** team for bringing RK3588 support to the mainline Linux kernel.
- The **[LibreELEC](https://libreelec.tv/) community**, **[chewitt](https://github.com/chewitt)**, and **[Kwiboo](https://github.com/Kwiboo)** for the patches, kernel configurations, and years of Rockchip expertise shared in public.
- **[Armbian](https://www.armbian.com/)** for providing a solid, minimal base to build and test on.

Thank you.
