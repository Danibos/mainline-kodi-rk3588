# Kodi RK3588 Mainline

Kodi para Orange Pi 5 con decodificación V4L2 Request y kernel mainline.

## Actualización 2026.10.13 — preparada para revisión

- Soporte Wayland y sesión GBM.
- YouTube hasta 1080p, con parche incluido.
- InputStream Adaptive 22.3.22.
- CEC integrado, sin arreglo manual posterior.
- Cinco visualizadores GLES.
- Kernel 7.2.9, FFmpeg 9.0.2 y Kodi 22.0 RC1.

Esta entrega requiere **Orange Pi 5 arm64 con Armbian/Ubuntu 26.04**. No es una actualización binaria para Ubuntu 24.04. Kodi sigue siendo una versión candidata.

## Instalar

Descarga la entrega completa de la release, extrae su carpeta y ejecuta `sudo ./install.sh`. Reinicia al terminar y elige Kodi GBM o Kodi Wayland en el inicio de sesión. Se conserva el perfil y el kernel anterior. No se fuerza ningún dispositivo de audio ni mapa de mando.

[Instalación, paquetes y comprobaciones](releases/2026-10-13/README.md) · [Notas breves](releases/2026-10-13/RELEASE-NOTES.md).

El parche de YouTube ya forma parte del paquete; no hay que editar el complemento manualmente. AV1/4K de YouTube sigue pendiente. Las preferencias y credenciales del usuario no forman parte de la entrega.

## Construcción

`config/update-20261010.json` fija fuentes y commits. Para reconstruir, usa `scripts/build-update-20261010.py` para kernel, FFmpeg y Kodi; el perfil predeterminado de Kodi es `generic`. Los binarios se empaquetan con `scripts/package-release-20261013.py` y se verifican con `scripts/validate-release-20261013.py`. Ejecuta antes `scripts/prepare-youtube-release-20261013.py` para obtener YouTube y los módulos oficiales fijados por checksum. El empaquetado requiere el prefijo de construcción preparado y Adaptive del manifiesto; no modifica la instalación activa ni publica archivos.

La release se ha comprobado en staging y en una sesión Wayland aislada. Todavía no se ha probado una instalación limpia y arranque físico de estos paquetes. GBM/HDMI/CEC se probaron anteriormente en el equipo de desarrollo. Solo Orange Pi 5 y esta base están validados para preparar estos binarios; otras placas requieren pruebas.

Las herramientas antiguas de `build/`, `config/install.sh` y la release v1.0 describen versiones anteriores; no son el instalador de esta entrega. Cada componente conserva su licencia y sus créditos originales.
