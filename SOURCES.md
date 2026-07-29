# Sources

## Linux kernel

- **Upstream**: [inindev/linux-rockchip](https://github.com/inindev/linux-rockchip) tag `v7.1.1`
- **Patches**: 167 patches (Collabora mainline backports, HBR audio, CEC)
- **Config**: Armbian-based with IEC958, HDMI_CODEC, HDMI_I2S_AUDIO, and CEC enabled
- **Build**: cross-compiled with `aarch64-linux-gnu-`

## Kodi

- **Upstream**: [xbmc/xbmc](https://github.com/xbmc/xbmc) `22.0-BETA1`
- **Patches**: Kwiboo DRMPRIME patches + custom V4L2 fixes
- **Build**: native on RK3588, GBM/GLES target

## FFmpeg

- **Upstream**: [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) `8.1.2`
- **Config**: `--enable-v4l2-request --enable-libdrm`
- **Build**: native on RK3588

## License notes

The patches and build scripts used to produce the binary packages in [Releases](https://github.com/Danibos/mainline-kodi-rk3588/releases) are available upon request. The upstream sources are linked above — the release binaries are built directly from those trees with the modifications described here.
