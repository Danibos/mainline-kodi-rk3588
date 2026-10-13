# Kodi RK3588 Mainline

Kodi for Orange Pi 5 with hardware video decoding and a mainline Linux kernel.

## What's new in 2026.10.13

- Wayland support alongside GBM.
- YouTube playback fix, up to 1080p.
- InputStream Adaptive included for DASH/HLS.
- Integrated HDMI-CEC support.
- Five visualizers: Shadertoy, Goom, FishBMC, Spectrum and Waveform.
- Kernel 7.2.9, FFmpeg 9.0.2 and Kodi 22 RC1, with playback stability fixes.

## Install

Requires **Orange Pi 5 with Armbian based on Ubuntu 26.04 (arm64), using an ext4 root filesystem**.

1. Download the release `.tar.gz` archive.
2. Extract it and open a terminal in the extracted folder.
3. Run:

```sh
sudo ./install.sh
```

4. Restart and select **Kodi RK3588 on GBM** or **Kodi RK3588 on Wayland** at login. Accept any prompts to enable the included add-ons.

[Download releases](https://github.com/Danibos/mainline-kodi-rk3588/releases)
