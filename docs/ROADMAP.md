# Roadmap

## Goal
Modern multimedia stack for RK3588 on Debian/Armbian with mainline kernel.

## Status

### ✅ Milestone 1: Kernel & Audio basics
- Mainline kernel 7.1.1 + 166 patches, booting from NVMe
- IEC958/ELD controls exposed
- HDMI passthrough formats detected
- CEC working (`/dev/cec0`, volume control confirmed)

### ⏳ Milestone 2: Passthrough & HW Decode
- Audio passthrough playback test (IEC958/HBR patches applied, enumeration works)
- V4L2 Request API HW decode (H.264/H.265) — modules loaded, pending playback test
- CEC functional test ✅

### ⏳ Milestone 3: Full Multimedia
- HDR10/HDR10+ output
- Stable Kodi + FFmpeg + kernel integration

### ⏳ Milestone 4: Stable Release
- Polished, reproducible build
- All features tested and working
