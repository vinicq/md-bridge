---
hide:
  - navigation
---

<p align="center">
  <img src="brand/wordmark.png" alt="md-bridge" width="600">
</p>

<p align="center">
  <strong>Conversor de documentos self-hosted.</strong><br>
  PDF ↔ Markdown hoje, mais pares de formato conforme as contribuições chegam.<br>
  Determinístico, heurístico, sem chamadas externas.
</p>

---

## O que ele faz

O md-bridge é um serviço HTTP pequeno mais uma interface React para converter
entre formatos de documento. Já nasce com PDF ↔ Markdown; a arquitetura aceita
novos pares de formato (DOCX, EPUB, RTF e outros) conforme as contribuições
chegam. A conversão é **determinística**: o mesmo arquivo de entrada produz o
mesmo arquivo de saída em toda execução. Sem modelo, sem fine-tuning, sem chave
de API, sem chamada de rede a terceiros.

- **PDF → Markdown** com detecção de títulos, recuperação de listas, extração
  de tabelas e front matter YAML.
- **Markdown → PDF** renderizado via Chromium headless com uma folha de estilo
  A4 embutida.
- **Modo lote** na interface: solte uma pasta, converta tudo em sequência,
  baixe arquivo por arquivo.
- **Endpoint de diagnóstico** para a interface avisar sobre PDFs marcados,
  necessidade de OCR ou fontes ausentes antes de iniciar a conversão.
- **Interface multilíngue** (inglês + português + espanhol), com a escolha
  preservada no `localStorage`.

## Demonstração rápida

![Fluxo de demonstração pela interface de conversão](screenshots/demo.gif)

## Rode em dois comandos

```bash
git clone https://github.com/vinicq/md-bridge.git
cd md-bridge && docker compose up
```

Interface em `http://localhost:5173`, API em `http://localhost:8000/docs`.
Os passos detalhados de instalação estão na página
[Primeiros passos](getting-started.md).

## Por que md-bridge

| O que você pode querer | O que o md-bridge entrega |
| --- | --- |
| Converter PDFs sem enviá-los a terceiros | Self-hosted; nada sai da máquina |
| Resultados reproduzíveis | Mesma entrada, mesma saída, toda vez |
| Processar um acervo em lote | Solte uma pasta, ganhe uma fila |
| Integrar com suas próprias ferramentas | `/api/pdf-to-md`, `/api/md-to-pdf`, `/api/inspect-pdf` |
| Ler o código da conversão | [`packages/pdf-to-markdown/scripts/convert.py`](https://github.com/vinicq/md-bridge/blob/main/packages/pdf-to-markdown/scripts/convert.py) |

## Próximos passos

- [Primeiros passos](getting-started.md) — instalar, rodar, processar uma pasta.
- [Referência da API](API.md) — endpoints, opções, envelope de erro.
- [Contribuindo](contributing.md) — como abrir uma issue ou um PR.
- [Segurança](security.md) — como relatar uma vulnerabilidade em privado.
- [Changelog](changelog.md) — o que entrou em cada versão.

## Licença

[MIT](https://github.com/vinicq/md-bridge/blob/main/LICENSE).
