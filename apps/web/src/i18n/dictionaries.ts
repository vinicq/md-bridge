export type Locale = 'en' | 'pt' | 'es'

export const LOCALES: { code: Locale; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'pt', label: 'Português' },
  { code: 'es', label: 'Español' },
]

interface Dictionary {
  nav: {
    pdfToMd: string
    mdToPdf: string
    about: string
    mainLabel: string
  }
  a11y: {
    skipToContent: string
  }
  home: {
    title: string
    subtitle: string
    cards: {
      pdfToMd: { title: string; body: string; cta: string }
      mdToPdf: { title: string; body: string; cta: string }
    }
    matrix: {
      heading: string
      openConverter: string
      requestPair: string
      newTab: string
      status: { shipped: string; inPr: string; roadmap: string; wanted: string }
    }
  }
  pdfToMd: {
    title: string
    subtitle: string
    convert: string
    converting: string
    ready: string
    download: string
    previewEmpty: string
    success: string
    // Source-PDF preview pane (#15). `sourceIframeTitle` is the iframe's
    // accessible name and takes the file name.
    sourceIframeTitle: (name: string) => string
    sourcePaneEmpty: string
    sourcePaneError: string
    compare: {
      tablistLabel: string
      tabPdf: string
      tabMd: string
    }
    warnings: {
      // Heading on the warnings alert.
      title: string
      // Translations indexed by the backend's warning codes. Unknown
      // codes fall back to the raw string at render time.
      needs_ocr: string
      images_not_persisted: string
      // Visible reason shown when a needs_ocr result blocks its download.
      downloadBlocked: string
      // Label of the escape-hatch button that downloads the near-empty file anyway.
      downloadAnyway: string
    }
  }
  mdToPdf: {
    title: string
    subtitle: string
    paste: string
    pasteLabel: string
    generate: string
    generating: string
    download: string
    previewEmpty: string
    previewIframeTitle: string
    pastedFilename: string
    success: string
  }
  themePicker: {
    // Group label above the theme tiles.
    label: string
    // Link to the deep theme library (F2); target may be a placeholder route.
    browse: string
  }
  themesPage: {
    title: string
    subtitle: string
    back: string
  }
  optionsPanel: {
    legend: string
    frontMatter: { label: string; tip: string }
    pageBreak: { label: string; tip: string }
    withImages: { label: string; tip: string }
    blockquotes: { label: string; tip: string }
    clusterHeadings: { label: string; tip: string }
    preserveLineBreaks: { label: string; tip: string }
    footnotePairing: { label: string; tip: string }
    maxHeadingLevel: { label: string; tip: string }
  }
  pageSetup: {
    legend: string
    page: { legend: string }
    pageSize: { label: string }
    margins: { label: string; tight: string; normal: string; loose: string }
    header: { legend: string }
    footer: { legend: string }
    slot: { left: string; center: string; right: string }
    tokenHelp: string
    slotPlaceholder: string
  }
  about: {
    title: string
    intro: string
    how: { title: string; p1: string; p2: string }
    limits: { title: string; items: string[] }
    more: { title: string; body: string }
  }
  dropzone: {
    dropFile: (label: string) => string
    dropFiles: (label: string) => string
    orClick: string
    orClickMany: string
    sizeHint: (size: string) => string
    invalidType: (label: string) => string
    someInvalid: (count: number, label: string) => string
    ariaLabel: (label: string) => string
  }
  batch: {
    heading: (count: number) => string
    statusQueued: string
    statusConverting: string
    statusDone: string
    statusError: string
    progress: (done: number, total: number) => string
    convertAll: string
    downloadAll: (count: number) => string
    clear: string
    skip: string
    skipLabel: (name: string) => string
    errorTimeout: string
    errorSkipped: string
    pdfBundleName: string
    mdBundleName: string
  }
  diag: {
    title: string
    pages: string
    body: string
    headings: string
    tagged: string
    yes: string
    no: string
    loading: string
    empty: string
    fonts: (count: number) => string
    chars: string
    needsOcr: string
  }
  errors: {
    unknown: string
    // Shown when the API blocks a scanned PDF with 422 ocr_required.
    ocrRequired: {
      title: string
      message: string
      cta: string
      ctaNewTab: string
    }
  }
  languageSwitcher: {
    label: string
  }
  workshop: {
    title: string
    subtitle: string
    localesHeading: string
    completion: (filled: number, total: number) => string
    editorHeading: string
    tableCaption: string
    colKey: string
    colReference: string
    colDraft: string
    untranslatedBadge: string
    draftInputLabel: (key: string) => string
    showingCount: (total: number, untranslated: number) => string
    exportHeading: string
    copyTs: string
    copyJson: string
    copied: string
    selectLocale: string
    allDone: string
  }
}

const en: Dictionary = {
  nav: {
    pdfToMd: 'PDF · MD',
    mdToPdf: 'MD · PDF',
    about: 'About',
    mainLabel: 'Main navigation',
  },
  a11y: {
    skipToContent: 'Skip to content',
  },
  home: {
    title: 'Convert PDF and Markdown locally.',
    subtitle:
      'Deterministic heuristics between PDF and Markdown. Same input, same output, every run. No cloud, no subscriptions.',
    cards: {
      pdfToMd: {
        title: 'PDF → Markdown',
        body: 'Extracts structure: headings by font size, lists, tables and front matter. No OCR in v1.',
        cta: 'Convert a PDF',
      },
      mdToPdf: {
        title: 'Markdown → PDF',
        body: 'Renders via headless Chromium with a CSS theme. Consistent output, no GTK or wkhtmltopdf.',
        cta: 'Generate a PDF',
      },
    },
    matrix: {
      heading: 'All conversions',
      openConverter: 'Open converter',
      requestPair: 'Request this pair',
      newTab: '(opens in a new tab)',
      status: { shipped: 'Shipped', inPr: 'In PR', roadmap: 'Roadmap', wanted: 'Wanted' },
    },
  },
  pdfToMd: {
    title: 'PDF to Markdown',
    subtitle: 'Upload a PDF and extract its content as structured Markdown.',
    convert: 'Convert',
    converting: 'Converting',
    ready: 'Ready',
    download: 'Download .md',
    previewEmpty: 'The Markdown will appear here after conversion.',
    success: 'Markdown generated.',
    sourceIframeTitle: (name: string) => `Source PDF: ${name}`,
    sourcePaneEmpty: 'Drop a PDF to preview it here.',
    sourcePaneError: 'This PDF has no text layer to convert.',
    compare: {
      tablistLabel: 'Source and result view',
      tabPdf: 'PDF',
      tabMd: 'Markdown',
    },
    warnings: {
      title: 'Warnings',
      needs_ocr:
        'Very little text was extracted. The PDF may be scanned; run OCR (e.g. Tesseract) before converting.',
      images_not_persisted:
        'Image extraction is enabled but images are not persisted by the API; the markdown references images that are not served back.',
      downloadBlocked:
        'Too little text was extracted, so the download is held back. Enable OCR, or download anyway.',
      downloadAnyway: 'Download anyway',
    },
  },
  mdToPdf: {
    title: 'Markdown to PDF',
    subtitle: 'Upload a .md file or paste text and convert it to PDF with a CSS theme.',
    paste: 'Or paste markdown here...',
    pasteLabel: 'Pasted markdown',
    generate: 'Convert',
    generating: 'Converting',
    download: 'Download .pdf',
    previewEmpty: 'The preview will appear here after conversion.',
    previewIframeTitle: 'Generated PDF preview',
    pastedFilename: 'pasted.md',
    success: 'PDF ready.',
  },
  themePicker: {
    label: 'Theme',
    browse: 'Browse all themes →',
  },
  themesPage: {
    title: 'Theme library',
    subtitle: 'The full theme catalogue is on the way. For now, pick a theme from the converter.',
    back: '← Back to Markdown to PDF',
  },
  optionsPanel: {
    legend: 'Conversion options',
    frontMatter: {
      label: 'Add front matter',
      tip: 'Write the title, author, and date as a YAML block at the top of the Markdown.',
    },
    pageBreak: {
      label: 'Mark page breaks',
      tip: 'Insert a horizontal rule (---) where each PDF page ends.',
    },
    withImages: {
      label: 'Extract images',
      tip: 'Save embedded images and link them from the Markdown. The hosted demo does not serve the image files back.',
    },
    blockquotes: {
      label: 'Detect block quotes',
      tip: 'Treat consistently indented passages as block quotes.',
    },
    clusterHeadings: {
      label: 'Detect headings by font size',
      tip: 'Group font sizes into heading levels and merge headings split across lines.',
    },
    preserveLineBreaks: {
      label: 'Keep line breaks',
      tip: 'Preserve intentional line breaks, like poetry or addresses, as hard breaks.',
    },
    footnotePairing: {
      label: 'Pair footnotes',
      tip: 'Link footer footnotes to their reference marks in the text.',
    },
    maxHeadingLevel: {
      label: 'Deepest heading level',
      tip: "Limit how deep detected headings go (1–6). Applies only when 'Detect headings by font size' is on.",
    },
  },
  pageSetup: {
    legend: 'Page setup',
    page: { legend: 'Page' },
    pageSize: { label: 'Page size' },
    margins: { label: 'Margins', tight: 'Tight', normal: 'Normal', loose: 'Loose' },
    header: { legend: 'Header' },
    footer: { legend: 'Footer' },
    slot: { left: 'Left', center: 'Center', right: 'Right' },
    tokenHelp:
      'Use {{title}}, {{author}}, {{date}}, {{page}}, {{pages}} to insert values automatically.',
    slotPlaceholder: 'e.g. {{title}}',
  },
  about: {
    title: 'About md-bridge',
    intro:
      'md-bridge is an open-source, self-hosted converter between PDF and Markdown. It runs entirely on your machine. No external service, no model inference, no telemetry. The same input file produces the same output file on every run.',
    how: {
      title: 'How it works',
      p1:
        'From PDF to Markdown: hand-written PyMuPDF heuristics detect headings by font size and document outline, recover lists from bullet glyphs and numbered patterns, and extract tables via find_tables. The result is a clean Markdown file that preserves the original structure.',
      p2:
        'From Markdown to PDF: headless Chromium renders the source through a bundled A4 stylesheet, the same engine browsers use to print any web page to PDF. Output is stable across runs.',
    },
    limits: {
      title: 'Known limits',
      items: [
        'Scanned PDFs need OCR before submission. The diagnostic endpoint flags the case; md-bridge ships no OCR engine of its own.',
        'Tables with cells merged across rows or columns may come out flattened in the output.',
        'Headers and footers that repeat on every page are stripped automatically.',
      ],
    },
    more: {
      title: 'Open source',
      body:
        'md-bridge is released under the MIT license. The code lives at github.com/vinicq/md-bridge and the documentation at vinicq.github.io/md-bridge. Bug reports, feature requests, and pull requests are welcome. See CONTRIBUTING.md for the workflow.',
    },
  },
  dropzone: {
    dropFile: (label) => `Drop a ${label}`,
    dropFiles: (label) => `Drop ${label} files or a folder`,
    orClick: 'or click to select',
    orClickMany: 'or click to pick files',
    sizeHint: (size) => `${size} · click to change`,
    invalidType: (label) => `Invalid type. Expected ${label}.`,
    someInvalid: (count, label) =>
      `${count} file${count === 1 ? '' : 's'} ignored: not ${label}.`,
    ariaLabel: (label) => `Drop a ${label} file or click to choose`,
  },
  batch: {
    heading: (count) => `${count} file${count === 1 ? '' : 's'} queued`,
    statusQueued: 'Queued',
    statusConverting: 'Converting',
    statusDone: 'Done',
    statusError: 'Error',
    progress: (done, total) => `${done} of ${total} complete`,
    convertAll: 'Convert all',
    downloadAll: (count) => `Download all (${count})`,
    clear: 'Clear list',
    skip: 'Skip',
    skipLabel: (name) => `skip ${name}`,
    errorTimeout: 'Timed out',
    errorSkipped: 'Skipped',
    pdfBundleName: 'pdfs.zip',
    mdBundleName: 'markdown.zip',
  },
  diag: {
    title: 'PDF diagnostics',
    pages: 'Pages',
    body: 'Body',
    headings: 'Detected headings',
    tagged: 'PDF/UA tagged',
    yes: 'yes',
    no: 'no',
    loading: 'Analyzing PDF...',
    empty: 'Upload a PDF to see diagnostics.',
    fonts: (count) => `Fonts (${count})`,
    chars: 'chars',
    needsOcr:
      'Little extractable text. PDF is likely scanned — run OCR before converting.',
  },
  errors: {
    unknown: 'Unknown failure',
    ocrRequired: {
      title: 'OCR required',
      message:
        'This PDF has no extractable text layer, so it looks scanned. Enable OCR to convert it.',
      cta: 'How to enable OCR',
      ctaNewTab: '(opens in a new tab)',
    },
  },
  languageSwitcher: {
    label: 'Language',
  },
  workshop: {
    title: 'Language Workshop',
    subtitle:
      'Edit any translation for a locale and copy a snippet to paste into the dictionary. Keys still identical to English are flagged; a few (brand names, "Markdown") are identical on purpose.',
    localesHeading: 'Locales',
    completion: (translated, total) => `${translated} of ${total} localized`,
    editorHeading: 'Translations',
    tableCaption: 'Every translation key with its English reference and your draft.',
    colKey: 'Key',
    colReference: 'English',
    colDraft: 'Your translation',
    untranslatedBadge: 'same as English',
    draftInputLabel: (key) => `Translation for ${key}`,
    showingCount: (total, untranslated) => `${total} keys, ${untranslated} still match English`,
    exportHeading: 'Export',
    copyTs: 'Copy as TypeScript',
    copyJson: 'Copy as JSON',
    copied: 'Copied',
    selectLocale: 'Locale to translate',
    allDone: 'Every key in this locale differs from English.',
  },
}

const pt: Dictionary = {
  nav: {
    pdfToMd: 'PDF · MD',
    mdToPdf: 'MD · PDF',
    about: 'Sobre',
    mainLabel: 'Navegação principal',
  },
  a11y: {
    skipToContent: 'Pular para o conteúdo',
  },
  home: {
    title: 'Converta PDF e Markdown local.',
    subtitle:
      'Heurística determinística entre PDF e Markdown. Mesma entrada, mesma saída, em toda execução. Sem nuvem, sem assinatura.',
    cards: {
      pdfToMd: {
        title: 'PDF → Markdown',
        body: 'Extrai estrutura: títulos por tamanho de fonte, listas, tabelas e front matter. Sem OCR no v1.',
        cta: 'Converter um PDF',
      },
      mdToPdf: {
        title: 'Markdown → PDF',
        body: 'Renderiza via Chromium headless com tema CSS. Saída consistente, sem GTK ou wkhtmltopdf.',
        cta: 'Gerar um PDF',
      },
    },
    matrix: {
      heading: 'Todas as conversões',
      openConverter: 'Abrir conversor',
      requestPair: 'Pedir este par',
      newTab: '(abre em uma nova aba)',
      status: { shipped: 'Disponível', inPr: 'Em PR', roadmap: 'No mapa', wanted: 'Procurado' },
    },
  },
  pdfToMd: {
    title: 'PDF para Markdown',
    subtitle: 'Suba um PDF e extraia o conteúdo como Markdown estruturado.',
    convert: 'Converter',
    converting: 'Convertendo',
    ready: 'Pronto',
    download: 'Baixar .md',
    previewEmpty: 'O Markdown aparece aqui depois da conversão.',
    success: 'Markdown gerado.',
    sourceIframeTitle: (name: string) => `PDF de origem: ${name}`,
    sourcePaneEmpty: 'Solte um PDF para visualizá-lo aqui.',
    sourcePaneError: 'Este PDF não tem camada de texto para converter.',
    compare: {
      tablistLabel: 'Visão de origem e resultado',
      tabPdf: 'PDF',
      tabMd: 'Markdown',
    },
    warnings: {
      title: 'Avisos',
      needs_ocr:
        'Pouco texto foi extraído. O PDF pode estar escaneado; rode OCR (por exemplo Tesseract) antes de converter.',
      images_not_persisted:
        'A extração de imagens está habilitada, mas as imagens não são persistidas pela API; o markdown referencia imagens que não são servidas de volta.',
      downloadBlocked:
        'Pouco texto foi extraído, então o download está retido. Ative o OCR, ou baixe mesmo assim.',
      downloadAnyway: 'Baixar mesmo assim',
    },
  },
  mdToPdf: {
    title: 'Markdown para PDF',
    subtitle: 'Suba um .md ou cole texto e converta em PDF com tema CSS.',
    paste: 'Ou cole markdown aqui...',
    pasteLabel: 'Markdown colado',
    generate: 'Converter',
    generating: 'Convertendo',
    download: 'Baixar .pdf',
    previewEmpty: 'O preview aparece aqui depois da conversão.',
    previewIframeTitle: 'Pré-visualização do PDF gerado',
    pastedFilename: 'colado.md',
    success: 'PDF pronto.',
  },
  themePicker: {
    label: 'Tema',
    browse: 'Ver todos os temas →',
  },
  themesPage: {
    title: 'Biblioteca de temas',
    subtitle: 'O catálogo completo de temas está a caminho. Por enquanto, escolha um tema no conversor.',
    back: '← Voltar para Markdown para PDF',
  },
  optionsPanel: {
    legend: 'Opções de conversão',
    frontMatter: {
      label: 'Adicionar front matter',
      tip: 'Escreve título, autor e data como um bloco YAML no topo do Markdown.',
    },
    pageBreak: {
      label: 'Marcar quebras de página',
      tip: 'Insere uma régua (---) onde cada página do PDF termina.',
    },
    withImages: {
      label: 'Extrair imagens',
      tip: 'Salva as imagens embutidas e referencia no Markdown. A demo hospedada não devolve os arquivos de imagem.',
    },
    blockquotes: {
      label: 'Detectar citações',
      tip: 'Trata trechos com recuo consistente como citações.',
    },
    clusterHeadings: {
      label: 'Detectar títulos por tamanho de fonte',
      tip: 'Agrupa tamanhos de fonte em níveis de título e une títulos quebrados em linhas.',
    },
    preserveLineBreaks: {
      label: 'Manter quebras de linha',
      tip: 'Preserva quebras de linha intencionais, como poesia ou endereços, como quebras rígidas.',
    },
    footnotePairing: {
      label: 'Parear notas de rodapé',
      tip: 'Liga as notas de rodapé às marcas de referência no texto.',
    },
    maxHeadingLevel: {
      label: 'Nível de título mais profundo',
      tip: "Limita a profundidade dos títulos detectados (1–6). Só vale com 'Detectar títulos por tamanho de fonte' ligado.",
    },
  },
  pageSetup: {
    legend: 'Configuração da página',
    page: { legend: 'Página' },
    pageSize: { label: 'Tamanho da página' },
    margins: { label: 'Margens', tight: 'Estreitas', normal: 'Normais', loose: 'Largas' },
    header: { legend: 'Cabeçalho' },
    footer: { legend: 'Rodapé' },
    slot: { left: 'Esquerda', center: 'Centro', right: 'Direita' },
    tokenHelp:
      'Use {{title}}, {{author}}, {{date}}, {{page}}, {{pages}} para inserir valores automaticamente.',
    slotPlaceholder: 'ex: {{title}}',
  },
  about: {
    title: 'Sobre o md-bridge',
    intro:
      'O md-bridge é um conversor open-source e self-hosted entre PDF e Markdown. Roda inteiramente na sua máquina. Sem serviço externo, sem inferência de modelo, sem telemetria. O mesmo arquivo de entrada produz o mesmo arquivo de saída em toda execução.',
    how: {
      title: 'Como funciona',
      p1:
        'De PDF para Markdown: heurísticas escritas à mão no PyMuPDF detectam títulos pelo tamanho da fonte e pelo outline do documento, recuperam listas a partir de marcadores e padrões numerados, e extraem tabelas com find_tables. O resultado é um Markdown limpo que preserva a estrutura original.',
      p2:
        'De Markdown para PDF: Chromium headless renderiza o conteúdo através de uma folha de estilo A4 embutida, o mesmo motor que os navegadores usam para imprimir qualquer página web em PDF. A saída é estável entre execuções.',
    },
    limits: {
      title: 'Limites conhecidos',
      items: [
        'PDFs escaneados precisam de OCR antes do envio. O endpoint de diagnóstico sinaliza o caso; o md-bridge não inclui motor de OCR próprio.',
        'Tabelas com células mescladas entre linhas ou colunas podem sair achatadas na saída.',
        'Cabeçalhos e rodapés que se repetem em todas as páginas são removidos automaticamente.',
      ],
    },
    more: {
      title: 'Open source',
      body:
        'O md-bridge é distribuído sob a licença MIT. O código fica em github.com/vinicq/md-bridge e a documentação em vinicq.github.io/md-bridge. Relatos de bugs, pedidos de feature e pull requests são bem-vindos. Veja o CONTRIBUTING.md para o fluxo de trabalho.',
    },
  },
  dropzone: {
    dropFile: (label) => `Solte um ${label}`,
    dropFiles: (label) => `Solte arquivos ${label} ou uma pasta`,
    orClick: 'ou clique para selecionar',
    orClickMany: 'ou clique para escolher arquivos',
    sizeHint: (size) => `${size} · clique para trocar`,
    invalidType: (label) => `Tipo inválido. Esperado ${label}.`,
    someInvalid: (count, label) =>
      `${count} arquivo${count === 1 ? '' : 's'} ignorado${count === 1 ? '' : 's'}: não é ${label}.`,
    ariaLabel: (label) => `Solte um arquivo ${label} ou clique para escolher`,
  },
  batch: {
    heading: (count) => `${count} arquivo${count === 1 ? '' : 's'} na fila`,
    statusQueued: 'Na fila',
    statusConverting: 'Convertendo',
    statusDone: 'Pronto',
    statusError: 'Erro',
    progress: (done, total) => `${done} de ${total} concluído${total === 1 ? '' : 's'}`,
    convertAll: 'Converter todos',
    downloadAll: (count) => `Baixar todos (${count})`,
    clear: 'Limpar lista',
    skip: 'Pular',
    skipLabel: (name) => `pular ${name}`,
    errorTimeout: 'Tempo esgotado',
    errorSkipped: 'Pulado',
    pdfBundleName: 'pdfs.zip',
    mdBundleName: 'markdown.zip',
  },
  diag: {
    title: 'Diagnóstico do PDF',
    pages: 'Páginas',
    body: 'Corpo',
    headings: 'Headings detectados',
    tagged: 'PDF/UA marcado',
    yes: 'sim',
    no: 'não',
    loading: 'Analisando PDF...',
    empty: 'Suba um PDF para ver o diagnóstico.',
    fonts: (count) => `Fontes (${count})`,
    chars: 'chars',
    needsOcr:
      'Pouco texto extraível. PDF provavelmente escaneado, rode OCR antes de converter.',
  },
  errors: {
    unknown: 'Falha desconhecida',
    ocrRequired: {
      title: 'OCR necessário',
      message:
        'Este PDF não tem camada de texto extraível, então parece escaneado. Ative o OCR para convertê-lo.',
      cta: 'Como ativar o OCR',
      ctaNewTab: '(abre em uma nova aba)',
    },
  },
  languageSwitcher: {
    label: 'Idioma',
  },
  workshop: {
    title: 'Oficina de Idiomas',
    subtitle:
      'Edite qualquer tradução de um idioma e copie um trecho para colar no dicionário. Chaves ainda iguais ao inglês são sinalizadas; algumas (nomes de marca, "Markdown") são iguais de propósito.',
    localesHeading: 'Idiomas',
    completion: (translated, total) => `${translated} de ${total} traduzidas`,
    editorHeading: 'Traduções',
    tableCaption: 'Todas as chaves de tradução, com a referência em inglês e o seu rascunho.',
    colKey: 'Chave',
    colReference: 'Inglês',
    colDraft: 'Sua tradução',
    untranslatedBadge: 'igual ao inglês',
    draftInputLabel: (key) => `Tradução para ${key}`,
    showingCount: (total, untranslated) => `${total} chaves, ${untranslated} ainda iguais ao inglês`,
    exportHeading: 'Exportar',
    copyTs: 'Copiar como TypeScript',
    copyJson: 'Copiar como JSON',
    copied: 'Copiado',
    selectLocale: 'Idioma a traduzir',
    allDone: 'Todas as chaves deste idioma diferem do inglês.',
  },
}

const es: Dictionary = {
  nav: {
    pdfToMd: 'PDF · MD',
    mdToPdf: 'MD · PDF',
    about: 'Acerca de',
    mainLabel: 'Navegación principal',
  },
  a11y: {
    skipToContent: 'Saltar al contenido',
  },
  home: {
    title: 'Convierte PDF y Markdown localmente.',
    subtitle:
      'Heurísticas deterministas entre PDF y Markdown. La misma entrada produce la misma salida en cada ejecución. Sin nube ni suscripciones.',
    cards: {
      pdfToMd: {
        title: 'PDF → Markdown',
        body: 'Extrae estructura: encabezados por tamaño de fuente, listas, tablas y front matter. Sin OCR en v1.',
        cta: 'Convertir un PDF',
      },
      mdToPdf: {
        title: 'Markdown → PDF',
        body: 'Renderiza con Chromium headless y un tema CSS. Salida consistente, sin GTK ni wkhtmltopdf.',
        cta: 'Generar un PDF',
      },
    },
    matrix: {
      heading: 'Todas las conversiones',
      openConverter: 'Abrir conversor',
      requestPair: 'Solicitar este par',
      newTab: '(se abre en una pestaña nueva)',
      status: { shipped: 'Disponible', inPr: 'En PR', roadmap: 'En la hoja de ruta', wanted: 'Buscado' },
    },
  },
  pdfToMd: {
    title: 'PDF a Markdown',
    subtitle: 'Sube un PDF y extrae su contenido como Markdown estructurado.',
    convert: 'Convertir',
    converting: 'Convirtiendo',
    ready: 'Listo',
    download: 'Descargar .md',
    previewEmpty: 'El Markdown aparecerá aquí después de la conversión.',
    success: 'Markdown generado.',
    sourceIframeTitle: (name: string) => `PDF de origen: ${name}`,
    sourcePaneEmpty: 'Suelta un PDF para verlo aquí.',
    sourcePaneError: 'Este PDF no tiene capa de texto para convertir.',
    compare: {
      tablistLabel: 'Vista de origen y resultado',
      tabPdf: 'PDF',
      tabMd: 'Markdown',
    },
    warnings: {
      title: 'Advertencias',
      needs_ocr:
        'Se extrajo muy poco texto. El PDF puede estar escaneado; ejecuta OCR (por ejemplo Tesseract) antes de convertir.',
      images_not_persisted:
        'La extracción de imágenes está activa, pero las imágenes no se persisten en la API; el markdown referencia imágenes que no se sirven de vuelta.',
      downloadBlocked:
        'Se extrajo muy poco texto, así que la descarga queda retenida. Activa el OCR, o descarga de todos modos.',
      downloadAnyway: 'Descargar de todos modos',
    },
  },
  mdToPdf: {
    title: 'Markdown a PDF',
    subtitle: 'Sube un archivo .md o pega texto y conviértelo a PDF con un tema CSS.',
    paste: 'O pega markdown aquí...',
    pasteLabel: 'Markdown pegado',
    generate: 'Convertir',
    generating: 'Convirtiendo',
    download: 'Descargar .pdf',
    previewEmpty: 'La vista previa aparecerá aquí después de la conversión.',
    previewIframeTitle: 'Vista previa del PDF generado',
    pastedFilename: 'pegado.md',
    success: 'PDF listo.',
  },
  themePicker: {
    label: 'Tema',
    browse: 'Ver todos los temas →',
  },
  themesPage: {
    title: 'Biblioteca de temas',
    subtitle: 'El catálogo completo de temas está en camino. Por ahora, elige un tema en el conversor.',
    back: '← Volver a Markdown a PDF',
  },
  optionsPanel: {
    legend: 'Opciones de conversión',
    frontMatter: {
      label: 'Añadir front matter',
      tip: 'Escribe el título, el autor y la fecha como un bloque YAML al inicio del Markdown.',
    },
    pageBreak: {
      label: 'Marcar saltos de página',
      tip: 'Inserta una regla (---) donde termina cada página del PDF.',
    },
    withImages: {
      label: 'Extraer imágenes',
      tip: 'Guarda las imágenes incrustadas y las enlaza desde el Markdown. La demo alojada no devuelve los archivos de imagen.',
    },
    blockquotes: {
      label: 'Detectar citas',
      tip: 'Trata los pasajes con sangría constante como citas.',
    },
    clusterHeadings: {
      label: 'Detectar encabezados por tamaño de fuente',
      tip: 'Agrupa los tamaños de fuente en niveles de encabezado y une encabezados partidos en líneas.',
    },
    preserveLineBreaks: {
      label: 'Conservar saltos de línea',
      tip: 'Conserva los saltos de línea intencionales, como poesía o direcciones, como saltos duros.',
    },
    footnotePairing: {
      label: 'Emparejar notas al pie',
      tip: 'Vincula las notas al pie con sus marcas de referencia en el texto.',
    },
    maxHeadingLevel: {
      label: 'Nivel de encabezado más profundo',
      tip: "Limita la profundidad de los encabezados detectados (1–6). Solo aplica con 'Detectar encabezados por tamaño de fuente' activado.",
    },
  },
  pageSetup: {
    legend: 'Configuración de página',
    page: { legend: 'Página' },
    pageSize: { label: 'Tamaño de página' },
    margins: { label: 'Márgenes', tight: 'Estrechos', normal: 'Normales', loose: 'Amplios' },
    header: { legend: 'Encabezado' },
    footer: { legend: 'Pie de página' },
    slot: { left: 'Izquierda', center: 'Centro', right: 'Derecha' },
    tokenHelp:
      'Usa {{title}}, {{author}}, {{date}}, {{page}}, {{pages}} para insertar valores automáticamente.',
    slotPlaceholder: 'ej: {{title}}',
  },
  about: {
    title: 'Acerca de md-bridge',
    intro:
      'md-bridge es un conversor open-source y self-hosted entre PDF y Markdown. Se ejecuta íntegramente en tu máquina. Sin servicio externo, sin inferencia de modelo, sin telemetría. La misma entrada produce la misma salida en cada ejecución.',
    how: {
      title: 'Cómo funciona',
      p1:
        'De PDF a Markdown: heurísticas escritas a mano sobre PyMuPDF identifican encabezados por tamaño de fuente y por el outline del documento, recuperan listas a partir de viñetas y patrones numerados, y extraen tablas con find_tables. El resultado es un Markdown limpio que preserva la estructura original.',
      p2:
        'De Markdown a PDF: Chromium headless renderiza el contenido con una hoja de estilo A4 incluida, el mismo motor que los navegadores usan para imprimir cualquier página web a PDF. La salida es estable entre ejecuciones.',
    },
    limits: {
      title: 'Límites conocidos',
      items: [
        'Los PDF escaneados requieren OCR antes del envío. El endpoint de diagnóstico señala el caso; md-bridge no incluye motor de OCR propio.',
        'Las tablas con celdas combinadas entre filas o columnas pueden salir aplanadas en la salida.',
        'Los encabezados y pies de página que se repiten en todas las páginas se eliminan automáticamente.',
      ],
    },
    more: {
      title: 'Open source',
      body:
        'md-bridge se distribuye bajo la licencia MIT. El código vive en github.com/vinicq/md-bridge y la documentación en vinicq.github.io/md-bridge. Reportes de bugs, solicitudes de features y pull requests son bienvenidos. Consulta CONTRIBUTING.md para el flujo de trabajo.',
    },
  },
  dropzone: {
    dropFile: (label) => `Suelta un ${label}`,
    dropFiles: (label) => `Suelta archivos ${label} o una carpeta`,
    orClick: 'o haz clic para seleccionar',
    orClickMany: 'o haz clic para elegir archivos',
    sizeHint: (size) => `${size} · haz clic para cambiar`,
    invalidType: (label) => `Tipo inválido. Se esperaba ${label}.`,
    someInvalid: (count, label) =>
      `${count} archivo${count === 1 ? '' : 's'} ignorado${count === 1 ? '' : 's'}: no es ${label}.`,
    ariaLabel: (label) => `Suelta un archivo ${label} o haz clic para elegirlo`,
  },
  batch: {
    heading: (count) => `${count} archivo${count === 1 ? '' : 's'} en cola`,
    statusQueued: 'En cola',
    statusConverting: 'Convirtiendo',
    statusDone: 'Listo',
    statusError: 'Error',
    progress: (done, total) => `${done} de ${total} completado${total === 1 ? '' : 's'}`,
    convertAll: 'Convertir todo',
    downloadAll: (count) => `Descargar todo (${count})`,
    clear: 'Limpiar lista',
    skip: 'Omitir',
    skipLabel: (name) => `omitir ${name}`,
    errorTimeout: 'Tiempo agotado',
    errorSkipped: 'Omitido',
    pdfBundleName: 'pdfs.zip',
    mdBundleName: 'markdown.zip',
  },
  diag: {
    title: 'Diagnóstico del PDF',
    pages: 'Páginas',
    body: 'Cuerpo',
    headings: 'Encabezados detectados',
    tagged: 'PDF/UA etiquetado',
    yes: 'sí',
    no: 'no',
    loading: 'Analizando PDF...',
    empty: 'Sube un PDF para ver el diagnóstico.',
    fonts: (count) => `Fuentes (${count})`,
    chars: 'caracteres',
    needsOcr:
      'Hay poco texto extraíble. Probablemente el PDF esté escaneado; ejecuta OCR antes de convertir.',
  },
  errors: {
    unknown: 'Fallo desconocido',
    ocrRequired: {
      title: 'OCR requerido',
      message:
        'Este PDF no tiene una capa de texto extraíble, así que parece escaneado. Activa el OCR para convertirlo.',
      cta: 'Cómo activar el OCR',
      ctaNewTab: '(se abre en una pestaña nueva)',
    },
  },
  languageSwitcher: {
    label: 'Idioma',
  },
  workshop: {
    title: 'Taller de Idiomas',
    subtitle:
      'Edita cualquier traducción de un idioma y copia un fragmento para pegar en el diccionario. Las claves aún idénticas al inglés se señalan; algunas (nombres de marca, "Markdown") son idénticas a propósito.',
    localesHeading: 'Idiomas',
    completion: (translated, total) => `${translated} de ${total} traducidas`,
    editorHeading: 'Traducciones',
    tableCaption: 'Todas las claves de traducción, con la referencia en inglés y tu borrador.',
    colKey: 'Clave',
    colReference: 'Inglés',
    colDraft: 'Tu traducción',
    untranslatedBadge: 'igual al inglés',
    draftInputLabel: (key) => `Traducción para ${key}`,
    showingCount: (total, untranslated) => `${total} claves, ${untranslated} aún iguales al inglés`,
    exportHeading: 'Exportar',
    copyTs: 'Copiar como TypeScript',
    copyJson: 'Copiar como JSON',
    copied: 'Copiado',
    selectLocale: 'Idioma a traducir',
    allDone: 'Todas las claves de este idioma difieren del inglés.',
  },
}

export const DICTIONARIES: Record<Locale, Dictionary> = { en, pt, es }

export type { Dictionary }
