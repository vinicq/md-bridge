# Primeiros passos

Há duas formas suportadas de rodar o md-bridge localmente: com Docker (um
comando) ou a partir do código-fonte (Python + Node). As duas terminam com a
mesma API em `http://localhost:8000` e a mesma interface em
`http://localhost:5173`.

## Com Docker (recomendado para experimentar)

Você só precisa do Docker Engine + Docker Compose.

```bash
git clone https://github.com/vinicq/md-bridge.git
cd md-bridge
docker compose up
```

A stack do compose espera o healthcheck da API antes de subir o container web,
então a primeira chamada do navegador já encontra um backend vivo atrás dela.

Para puxar imagens prontas em vez de construir localmente (mais rápido, sem
toolchain):

```bash
docker pull ghcr.io/vinicq/md-bridge-api:latest
docker pull ghcr.io/vinicq/md-bridge-web:latest
```

O arquivo do compose então as executa sem etapa de build.

### Rodando a suíte de testes dentro do Docker

Por padrão, a stack do compose roda a aplicação, não os testes. Um profile
opt-in `test` sobe containers efêmeros que executam pytest e vitest:

```bash
docker compose --profile test run --rm tests-api   # pytest do backend
docker compose --profile test run --rm tests-web   # vitest do frontend
```

Os dois containers encerram quando a suíte termina; nada fica rodando em
segundo plano.

## A partir do código-fonte

Você vai precisar de:

- Python 3.12 ou mais recente
- Node 22 e npm 10 ou mais recente

Os comandos abaixo funcionam igual no macOS, Linux e Windows depois que o
ambiente virtual está ativado.

```bash
# 1. Backend: crie o ambiente virtual
cd apps/api
python -m venv .venv

# Ative-o (escolha a linha do seu shell):
source .venv/bin/activate                   # macOS / Linux / Git Bash
# .venv\Scripts\Activate.ps1                # Windows PowerShell

# Instale o backend e as dependências do conversor:
python -m pip install -e ".[dev]"
python -m playwright install chromium

# 2. Frontend
cd ../web
npm install
npx playwright install chromium

# 3. Helper na raiz (permite iniciar API e interface juntas)
cd ../..
npm install

# 4. Suba os servidores de dev: API na porta 8000, Vite na porta 5173
npm run dev
```

Abra `http://localhost:5173` para a interface e `http://localhost:8000/docs`
para a documentação interativa da API.

## Primeira conversão

A página PDF → Markdown da interface aceita tanto arquivos individuais quanto
pastas inteiras soltas na dropzone. Experimente com uma das fixtures de
syllabus versionadas em `apps/api/tests/fixtures/` se quiser uma entrada
conhecida.

Para um smoke test só de API:

```bash
curl -X POST http://localhost:8000/api/pdf-to-md \
  -F "file=@apps/api/tests/fixtures/istqb-ctal-ta-syllabus-en.pdf" \
  -F 'options={"front_matter": true}'
```

A resposta inclui o Markdown extraído, um bloco `stats` (contagem de títulos,
de marcadores e de tabelas), os avisos que a heurística produziu e o front
matter YAML.

## Limites que vale conhecer

- A API limita uploads em **500 MB** por requisição. O nginx à frente dela
  espera até **10 minutos** por conversão, o que cobre PDFs muito grandes de
  ponta a ponta.
- PDFs escaneados precisam de OCR antes do envio. O md-bridge não embute o
  Tesseract; o endpoint de inspeção avisa quando o OCR é o passo que falta.
- Tabelas com células mescladas podem ser achatadas pelo extrator heurístico.

## Próximos passos

- [Referência da API](API.md) — cada endpoint, cada opção, cada erro.
- [Contribuindo](contributing.md) — estilo de código, pirâmide de testes,
  regras de PR.
