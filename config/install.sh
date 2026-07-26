#!/bin/bash
# kodi-rk3588-config installer
# Installs ALSA configuration for HDMI audio passthrough on RK3588
# Run as root

set -e

echo "=== kodi-rk3588-config installer ==="
echo ""

# 1. simple-card.conf with AES hooks
echo "[1/4] Installing simple-card.conf (AES hooks)..."
cat > /usr/share/alsa/cards/simple-card.conf << 'SIMPLEEOF'
<confdir:pcm/hdmi.conf>

simple-card.pcm.hdmi.!0 {
	@args [ CARD AES0 AES1 AES2 AES3 ]
	@args.CARD { type string }
	@args.AES0 { type integer }
	@args.AES1 { type integer }
	@args.AES2 { type integer }
	@args.AES3 { type integer }
	type hooks
	slave.pcm {
		type hw
		card $CARD
		device 0
	}
	hooks.0 {
		type ctl_elems
		hook_args [
			{
				name "IEC958 Playback Default"
				interface PCM
				lock true
				preserve true
				optional true
				value [ $AES0 $AES1 $AES2 $AES3 ]
			}
		]
	}
	hint {
		description "HDMI Passthrough"
	}
}
SIMPLEEOF

# 2. asound.conf
echo "[2/4] Installing asound.conf..."
cat > /etc/asound.conf << 'ASOUNDEOF'
# ALSA config for RK3588 HDMI audio
# Passthrough AES hooks via simple-card.conf

pcm.!default {
    type plug
    slave.pcm "hdmi:CARD=hdmi0,DEV=0"
    hint.description "HDMI Audio"
}

ctl.!default {
    type hw
    card hdmi0
}
ASOUNDEOF

# 3. Hide unnecessary ALSA plugins
echo "[3/4] Hiding unnecessary ALSA plugins..."
cat > /etc/alsa/conf.d/99-hide-plugins.conf << 'HIDEEOF'
# Hide unnecessary ALSA plugin PCMs from enumeration
pcm.!lavrate { }
pcm.!samplerate { }
pcm.!speexrate { }
pcm.!upmix { }
pcm.!vdownmix { }
pcm.!jack { }
pcm.!oss { }
pcm.!speex { }
pcm.!usbstream { }
pcm.!dmix { }
pcm.!sysdefault { }
pcm.!null { }
HIDEEOF

# 4. Blacklist analog codec
echo "[4/4] Blacklisting analog audio (ES8388)..."
cat > /etc/modprobe.d/blacklist-es8388.conf << 'BLACKEOF'
blacklist snd_soc_es8328
blacklist snd_soc_es8328_i2c
BLACKEOF

# Reset ALSA state
echo ""
echo "Resetting ALSA state..."
alsactl init 2>/dev/null || true

echo ""
echo "=== Done! Reboot to apply all changes ==="
echo "After reboot, Kodi will show only 2 audio devices:"
echo "  - HDMI Audio (PCM)"
echo "  - hdmi0 (Passthrough)"
