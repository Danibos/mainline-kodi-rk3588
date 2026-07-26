#!/bin/bash
# Kodi RK3588 Mainline - Installer
# Orange Pi 5 / RK3588 devices
set -e

echo "=== Kodi RK3588 Mainline v1.0 ==="
echo ""

DEBS="linux-image-7.1.1-3-arm64_7.1.1-3_arm64.deb
linux-headers-7.1.1-3-arm64_7.1.1-3_arm64.deb
linux-libc-dev_7.1.1-3_arm64.deb
ffmpeg-rk3588_8.1.2-1_arm64.deb
kodi-rk3588_22.0-beta1_arm64.deb
kodi-rk3588-config_1.0_all.deb"

echo "Installing packages..."
for deb in $DEBS; do
    echo "  $deb"
    sudo dpkg -i "$deb" 2>/dev/null || sudo apt-get install -f -y
done

echo ""
echo "After reboot, configure Kodi:"
echo "  Settings > Player > Videos > Processing:"
echo "    - Allow hardware acceleration: ON"
echo "    - Prime Render Method: Direct To Plane"
echo ""
echo "Rebooting in 5s..."
sleep 5
sudo reboot
