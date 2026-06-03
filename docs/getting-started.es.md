# Primeros pasos

Hay dos formas admitidas de ejecutar md-bridge en local: con Docker (un comando)
o desde el código fuente (Python + Node). Ambas terminan con la misma API en
`http://localhost:8000` y la misma interfaz en `http://localhost:5173`.

## Con Docker (recomendado para probarlo)

Solo necesitas Docker Engine + Docker Compose.

```bash
git clone https://github.com/vinicq/md-bridge.git
cd md-bridge
docker compose up
```

La stack del compose espera el healthcheck de la API antes de levantar el
container web, así que la primera llamada del navegador ya encuentra un backend
vivo detrás.

Para descargar imágenes prediseñadas en lugar de construir en local (más rápido,
sin toolchain):

```bash
docker pull ghcr.io/vinicq/md-bridge-api:latest
docker pull ghcr.io/vinicq/md-bridge-web:latest
```

El archivo del compose entonces las ejecuta sin paso de build.

### Ejecutar la suite de pruebas dentro de Docker

Por defecto, la stack del compose ejecuta la aplicación, no las pruebas. Un
profile opt-in `test` levanta containers efímeros que ejecutan pytest y vitest:

```bash
docker compose --profile test run --rm tests-api   # pytest del backend
docker compose --profile test run --rm tests-web   # vitest del frontend
```

Ambos containers terminan cuando la suite acaba; nada queda ejecutándose en
segundo plano.

## Desde el código fuente

Vas a necesitar:

- Python 3.12 o más reciente
- Node 22 y npm 10 o más reciente

Los comandos de abajo funcionan igual en macOS, Linux y Windows una vez activado
el entorno virtual.

```bash
# 1. Backend: crea el entorno virtual
cd apps/api
python -m venv .venv

# Actívalo (elige la línea de tu shell):
source .venv/bin/activate                   # macOS / Linux / Git Bash
# .venv\Scripts\Activate.ps1                # Windows PowerShell

# Instala el backend y las dependencias del conversor:
python -m pip install -e ".[dev]"
python -m playwright install chromium

# 2. Frontend
cd ../web
npm install
npx playwright install chromium

# 3. Helper en la raíz (permite iniciar API e interfaz juntas)
cd ../..
npm install

# 4. Levanta los servidores de desarrollo: API en el puerto 8000, Vite en el 5173
npm run dev
```

Abre `http://localhost:5173` para la interfaz y `http://localhost:8000/docs`
para la documentación interactiva de la API.

## Primera conversión

La página PDF → Markdown de la interfaz acepta tanto archivos individuales como
carpetas enteras soltadas en la dropzone. Pruébalo con una de las fixtures de
syllabus versionadas en `apps/api/tests/fixtures/` si quieres una entrada
conocida.

Para una prueba rápida solo de API:

```bash
curl -X POST http://localhost:8000/api/pdf-to-md \
  -F "file=@apps/api/tests/fixtures/istqb-ctal-ta-syllabus-en.pdf" \
  -F 'options={"front_matter": true}'
```

La respuesta incluye el Markdown extraído, un bloque `stats` (conteo de
encabezados, de viñetas y de tablas), las advertencias que produjo la heurística
y el front matter YAML.

## Límites que conviene conocer

- La API limita las subidas a **500 MB** por petición. El nginx delante de ella
  espera hasta **10 minutos** por conversión, lo que cubre PDFs muy grandes de
  extremo a extremo.
- Los PDFs escaneados necesitan OCR antes del envío. md-bridge no incluye
  Tesseract; el endpoint de inspección te avisa cuando el OCR es el paso que
  falta.
- Las tablas con celdas combinadas pueden quedar aplanadas por el extractor
  heurístico.

## Adónde ir después

- [Referencia de la API](API.md) — cada endpoint, cada opción, cada error.
- [Contribuir](contributing.md) — estilo de código, pirámide de pruebas, reglas
  de PR.
