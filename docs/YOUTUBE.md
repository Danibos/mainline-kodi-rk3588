# YouTube: errores de descarga y pantalla negra

En la instalación de prueba de Orange Pi 5 se observaron dos fallos distintos:

- HTTP 403 al descargar segmentos mediante el cliente ANDROID_VR de YouTube 7.4.4. El parche incluido excluye ese cliente. Es un workaround para esa versión, no una garantía frente a futuros cambios del servicio. Referencia upstream: https://github.com/anxdpanic/plugin.video.youtube/issues/1483.
- Pantalla negra con AV1/4K: el registro muestra ENOMEM al reservar buffers V4L2 Request con CMA de 256 MiB. Limitar la calidad máxima DASH de YouTube a **1080p** seleccionó H.264 con imagen visible en las pruebas de los tráileres La bella y la bestia y La joya del Nilo. El cambio interno fue kodion.mpd.quality.selection=4 en YouTube 7.4.4.

## Ajuste recomendado

En los ajustes del complemento YouTube, limita la calidad máxima DASH a 1080p. No requiere un mando, televisión o sistema de audio concreto. Mantén InputStream Adaptive compilado para la misma versión y ABI de Kodi.

El parche de descarga se encuentra en patches/youtube-7.4.4/0001-disable-android-vr-http-403.patch. Se aplica a las fuentes de **YouTube 7.4.4**, no al código de Kodi ni al kernel. Guarda una copia del complemento antes de aplicarlo. No se distribuyen claves API, tokens, cookies ni perfiles. Una actualización del complemento puede sustituir el archivo modificado; no aplicar este parche sin comprobar compatibilidad con otras versiones.

Para mantenedores, desde la raíz de las fuentes de YouTube 7.4.4: `patch --dry-run -p1 < /ruta/al/parche.patch` y, si pasa, `patch -p1 < /ruta/al/parche.patch`.

Las pruebas confirmaron reproducción de esos tráileres en 1080p; **AV1/4K sigue pendiente**. El límite es un ajuste recomendado y reversible, no se presenta como soporte 4K corregido. La próxima release debe integrar y comprobar este comportamiento para evitar arreglos manuales posteriores. Este cambio de documentación y parche no publica una nueva release binaria de Kodi/kernel.
