---
hide:
  - navigation
---

<p align="center">
  <img src="brand/wordmark.png" alt="md-bridge" width="600">
</p>

<p align="center">
  <strong>Conversor de documentos self-hosted.</strong><br>
  PDF ↔ Markdown hoy, más pares de formato a medida que llegan las contribuciones.<br>
  Determinista, heurístico, sin llamadas externas.
</p>

---

## Qué hace

md-bridge es un servicio HTTP pequeño más una interfaz React para convertir
entre formatos de documento. Trae PDF ↔ Markdown desde el primer día; la
arquitectura admite nuevos pares de formato (DOCX, EPUB, RTF y otros) a medida
que llegan las contribuciones. La conversión es **determinista**: el mismo
archivo de entrada produce el mismo archivo de salida en cada ejecución. Sin
modelo, sin fine-tuning, sin clave de API, sin llamadas de red a terceros.

- **PDF → Markdown** con detección de encabezados, recuperación de listas,
  extracción de tablas y front matter YAML.
- **Markdown → PDF** renderizado con Chromium headless y una hoja de estilo A4
  incorporada.
- **Modo por lotes** en la interfaz: suelta una carpeta, convierte todo de
  forma secuencial y descarga archivo por archivo.
- **Endpoint de diagnóstico** para que la interfaz avise sobre PDFs etiquetados,
  necesidad de OCR o fuentes faltantes antes de iniciar una conversión.
- **Interfaz multilingüe** (inglés + portugués + español), con la elección
  guardada en `localStorage`.

## Demostración rápida

![Flujo de demostración por la interfaz de conversión](screenshots/demo.gif)

## Ejecútalo en dos comandos

```bash
git clone https://github.com/vinicq/md-bridge.git
cd md-bridge && docker compose up
```

Interfaz en `http://localhost:5173`, API en `http://localhost:8000/docs`.
Los pasos detallados de instalación están en la página
[Primeros pasos](getting-started.md).

## Por qué md-bridge

| Lo que podrías querer | Lo que te da md-bridge |
| --- | --- |
| Convertir PDFs sin subirlos a un tercero | Self-hosted; nada sale de la máquina |
| Resultados reproducibles | Misma entrada, misma salida, siempre |
| Procesar un archivo completo por lotes | Suelta una carpeta, obtén una cola |
| Integrar con tus propias herramientas | `/api/pdf-to-md`, `/api/md-to-pdf`, `/api/inspect-pdf` |
| Leer el código de la conversión | [`packages/pdf-to-markdown/scripts/convert.py`](https://github.com/vinicq/md-bridge/blob/main/packages/pdf-to-markdown/scripts/convert.py) |

## Adónde ir después

- [Primeros pasos](getting-started.md) — instalar, ejecutar, procesar una carpeta.
- [Referencia de la API](API.md) — endpoints, opciones, sobre de error.
- [Contribuir](contributing.md) — cómo abrir un issue o un PR.
- [Seguridad](security.md) — cómo reportar una vulnerabilidad en privado.
- [Changelog](changelog.md) — qué se incluyó en cada versión.

## Licencia

[MIT](https://github.com/vinicq/md-bridge/blob/main/LICENSE).
