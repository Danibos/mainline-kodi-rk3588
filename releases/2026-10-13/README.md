# Kodi RK3588 · actualización 2026.10.13

**Preparada para revisión; todavía no publicada.** Para Orange Pi 5 arm64 con Armbian basado en Ubuntu 26.04 con raíz ext4 y arranque compatible con Image/uInitrd/DTB. Kodi 22.0 RC1 sigue siendo una versión candidata.

## Novedades

- Añadido soporte Wayland, manteniendo la sesión GBM.
- Arreglo de reproducción de YouTube hasta 1080p, incluido en el paquete.
- InputStream Adaptive incluido para DASH/HLS.
- CEC integrado: ya no hace falta aplicar el arreglo manual de libCEC.
- Cinco visualizadores: Shadertoy, Goom, FishBMC, Spectrum y Waveform.
- Kernel 7.2.9 y mejoras de estabilidad de reproducción y mini reproductor.

## Instalación

Descarga y extrae el paquete completo. Desde su carpeta ejecuta:

```sh
sudo ./install.sh
```

Cuando termine, reinicia y selecciona **Kodi RK3588 on GBM** o **Kodi RK3588 on Wayland** en el inicio de sesión. Si Kodi pregunta si quieres activar los complementos nuevos, acepta. Puedes comprobar antes la compatibilidad y los archivos con `sudo ./install.sh --check`.

Se conservan el perfil de Kodi y el kernel anterior. No se modifican SPI/U-Boot, dispositivos de audio ni mapas del mando. No se reinicia automáticamente. Las cabeceras son opcionales: `sudo ./install.sh --with-headers`.

Para restaurar los enlaces del arranque anterior desde un sistema arrancado: `sudo ./restore-boot.sh`, y reinicia. El respaldo está en `/var/backups/kodi-kernel/`; si el equipo no puede arrancar, necesitarás acceder mediante tu medio de recuperación.

## Paquetes

| Paquete | Contenido |
| --- | --- |
| linux-image-7.2.9-1-kodi-rk3588 | Kernel, módulos y DTB de Orange Pi 5 |
| linux-headers-7.2.9-1-kodi-rk3588 | Cabeceras opcionales para desarrollo/módulos |
| ffmpeg-rk3588 9.0.2 | FFmpeg con V4L2 Request, en prefijo aislado |
| kodi-rk3588 22.0rc1 | Kodi GBM/Wayland, libCEC y sesiones de inicio |
| kodi-rk3588-inputstream-adaptive 22.3.22 | Reproducción DASH/HLS compatible con este Kodi |
| kodi-rk3588-youtube 7.4.4 | Complemento parcheado y sus módulos Python necesarios |
| kodi-rk3588-visualizations | Los cinco visualizadores GLES |

## Alcance de las comprobaciones

Comprobados el empaquetado, las dependencias mediante apt, los enlaces de bibliotecas, el backend CEC, el límite de YouTube y el instalador en modo comprobación. Kodi empaquetado se ha iniciado bajo Weston headless y ha reproducido dos veces un vídeo DASH con Adaptive, con captura de imagen revisada. No se ha realizado una instalación limpia ni un nuevo arranque físico con estos paquetes; GBM/HDMI/CEC se validaron anteriormente en el equipo de desarrollo.

YouTube se limita a 1080p también si el perfil tenía una calidad superior, sin editar sus preferencias guardadas. **AV1/4K de YouTube no está resuelto**. No se incluyen claves API, cuentas ni cookies. Una actualización posterior del complemento puede sustituir esta versión modificada.

No son binarios para Ubuntu 24.04 ni para LibreELEC. Las otras placas RK3588 y otros esquemas de arranque requieren validación. El instalador comprueba estos requisitos antes de instalar.

La procedencia, los commits y las licencias están documentados en los paquetes; los scripts y parches de construcción se preparan junto a esta release. `release.json` identifica los paquetes y `SHA256SUMS` permite comprobar los archivos de la entrega.
