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
    preferences: string
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
      filter: string
      all: string
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
    previewLabel: string
    success: string
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
    livePreviewTitle: string
    pastedFilename: string
    success: string
  }
  // Markdown → DOCX page (#276). No theme/page-setup tunables and no result
  // preview (a .docx cannot render in an iframe), so there is no
  // previewIframeTitle here; the right pane previews the INPUT markdown.
  mdToDocx: {
    title: string
    subtitle: string
    paste: string
    pasteLabel: string
    generate: string
    generating: string
    download: string
    previewEmpty: string
    pastedFilename: string
    success: string
  }
  themePicker: {
    // Group label above the radio list.
    label: string
    // Status strings for loading / error states.
    loading: string
    loadError: string
  }
  themesPage: {
    title: string
    subtitle: string
    back: string
  }
  previewSamples: {
    document: string
    article: string
    resume: string
    email: string
    contract: string
    blog: string
  }
  themeLib: {
    title: string
    subtitle: string
    filter: string
    all: string
    serif: string
    sans: string
    mono: string
    preview: string
    custom: string
    source: string
    clear: string
    use: string
    downloadCss: string
    readonly: string
    customHint: string
    diagram: string
    newBadge: string
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
    dragLabel: (name: string) => string
    // Remove/reorder controls. Visible labels (moveUp/moveDown) and their
    // aria counterparts are separate so #358 can reuse the reorder keys.
    removeLabel: (name: string) => string
    moveUp: string
    moveDown: string
    moveUpLabel: (name: string) => string
    moveDownLabel: (name: string) => string
    // Keyboard-reorder a11y (#358): discoverable instruction + live announcements.
    reorderInstructions: string
    movedTo: (name: string, position: number, total: number) => string
    errorTimeout: string
    errorSkipped: string
    pdfBundleName: string
    mdBundleName: string
    docxBundleName: string
  }
  themeToggle: {
    toLight: string
    toDark: string
  }
  toast: {
    dismiss: string
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
  preferences: {
    title: string
    subtitle: string
    sections: { defaults: string; ui: string; privacy: string }
    defaultLanguage: { label: string; hint: string }
    defaultPdfTheme: { label: string; hint: string }
    pageSize: { label: string; hint: string }
    previewNewTab: { label: string; hint: string }
    accent: {
      label: string
      hint: string
      swatch: { brand: string; blue: string; green: string; graphite: string }
    }
    reduceMotion: { label: string; hint: string }
    darkMode: { label: string; hint: string }
    privacy: { badge: string; verified: string; viewReport: string }
    reset: string
    on: string
    off: string
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
    preferences: 'Preferences',
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
      filter: 'Filter',
      all: 'All',
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
    previewLabel: 'Converted Markdown',
    success: 'Markdown generated.',
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
    livePreviewTitle: 'Live theme preview',
    pastedFilename: 'pasted.md',
    success: 'PDF ready.',
  },
  mdToDocx: {
    title: 'Markdown to DOCX',
    subtitle: 'Upload a .md file or paste text and convert it to a Word document.',
    paste: 'Or paste markdown here...',
    pasteLabel: 'Pasted markdown',
    generate: 'Convert',
    generating: 'Converting',
    download: 'Download .docx',
    previewEmpty: 'The preview will appear here.',
    pastedFilename: 'pasted.md',
    success: 'DOCX ready.',
  },
  themePicker: {
    label: 'Theme',
    loading: 'Loading themes…',
    loadError: 'Could not load themes.',
  },
  themesPage: {
    title: 'Theme library',
    subtitle: 'The full theme catalogue is on the way. For now, pick a theme from the converter.',
    back: '← Back to Markdown to PDF',
  },
  previewSamples: {
    document: 'Document',
    article: 'Article',
    resume: 'Resume',
    email: 'Email',
    contract: 'Contract',
    blog: 'Blog post',
  },
  themeLib: {
    title: 'Theme library',
    subtitle:
      'Curated stylesheets for the PDF render. Pick one, preview it live on a rich sample, and layer your own CSS on top.',
    filter: 'Filter',
    all: 'All',
    serif: 'Serif',
    sans: 'Sans',
    mono: 'Mono',
    preview: 'Live preview',
    custom: 'Custom CSS',
    source: 'Theme CSS',
    clear: 'Clear',
    use: 'Use theme',
    downloadCss: 'Download .css',
    readonly: 'read-only',
    customHint:
      'Paste CSS to override the theme; it applies to the preview live, exactly like the converter stacks it after the theme.',
    diagram: 'Diagram',
    newBadge: 'NEW',
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
    dragLabel: (name) => `Drag to reorder ${name}`,
    removeLabel: (name) => `Remove ${name}`,
    moveUp: 'Up',
    moveDown: 'Down',
    moveUpLabel: (name) => `Move ${name} up`,
    moveDownLabel: (name) => `Move ${name} down`,
    reorderInstructions: 'Press Space to grab, arrow keys to move, Space to drop.',
    movedTo: (name, position, total) => `${name} moved to position ${position} of ${total}`,
    errorTimeout: 'Timed out',
    errorSkipped: 'Skipped',
    pdfBundleName: 'pdfs.zip',
    mdBundleName: 'markdown.zip',
    docxBundleName: 'docx.zip',
  },
  themeToggle: {
    toLight: 'Switch to light mode',
    toDark: 'Switch to dark mode',
  },
  toast: {
    dismiss: 'Dismiss notification',
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
  preferences: {
    title: 'Preferences',
    subtitle: 'Per-browser. Nothing leaves this device.',
    sections: { defaults: 'defaults', ui: 'UI', privacy: 'privacy' },
    defaultLanguage: {
      label: 'Default language',
      hint: 'Falls back if your browser locale is unsupported.',
    },
    defaultPdfTheme: {
      label: 'Default PDF theme',
      hint: 'Applied to every new Markdown to PDF batch.',
    },
    pageSize: {
      label: 'Default page size',
      hint: 'A4 outside the US, Letter inside.',
    },
    previewNewTab: {
      label: 'Open PDF preview in a new tab',
      hint: 'Off keeps the inline preview.',
    },
    accent: {
      label: 'Accent colour',
      hint: 'Brand red by default.',
      swatch: { brand: 'Brand red', blue: 'Blue', green: 'Green', graphite: 'Graphite' },
    },
    reduceMotion: {
      label: 'Reduce motion',
      hint: 'Skip fades and transitions. On automatically if your system asks.',
    },
    darkMode: {
      label: 'Dark mode',
      hint: 'Switch between the light and dark theme.',
    },
    privacy: {
      badge: 'No telemetry. No cookies. No accounts.',
      verified: 'Verified at build by scripts/audit-deps.py.',
      viewReport: 'View report',
    },
    reset: 'Reset all preferences',
    on: 'On',
    off: 'Off',
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
    preferences: 'Preferências',
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
      filter: 'Filtro',
      all: 'Todos',
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
    previewLabel: 'Markdown convertido',
    success: 'Markdown gerado.',
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
    livePreviewTitle: 'Preview do tema ao vivo',
    pastedFilename: 'colado.md',
    success: 'PDF pronto.',
  },
  mdToDocx: {
    title: 'Markdown para DOCX',
    subtitle: 'Suba um .md ou cole texto e converta em documento Word.',
    paste: 'Ou cole markdown aqui...',
    pasteLabel: 'Markdown colado',
    generate: 'Converter',
    generating: 'Convertendo',
    download: 'Baixar .docx',
    previewEmpty: 'O preview aparece aqui.',
    pastedFilename: 'colado.md',
    success: 'DOCX pronto.',
  },
  themePicker: {
    label: 'Tema',
    loading: 'Carregando temas…',
    loadError: 'Não foi possível carregar os temas.',
  },
  themesPage: {
    title: 'Biblioteca de temas',
    subtitle: 'O catálogo completo de temas está a caminho. Por enquanto, escolha um tema no conversor.',
    back: '← Voltar para Markdown para PDF',
  },
  previewSamples: {
    document: 'Documento',
    article: 'Artigo',
    resume: 'Currículo',
    email: 'E-mail',
    contract: 'Contrato',
    blog: 'Post de blog',
  },
  themeLib: {
    title: 'Biblioteca de temas',
    subtitle:
      'Folhas de estilo curadas para o PDF. Escolha uma, veja o preview ao vivo num exemplo rico e adicione seu próprio CSS por cima.',
    filter: 'Filtro',
    all: 'Todos',
    serif: 'Serifada',
    sans: 'Sem serifa',
    mono: 'Monoespaçada',
    preview: 'Preview ao vivo',
    custom: 'CSS custom',
    source: 'CSS do tema',
    clear: 'Limpar',
    use: 'Usar tema',
    downloadCss: 'Baixar .css',
    readonly: 'somente leitura',
    customHint:
      'Cole CSS para sobrepor o tema; aplica no preview ao vivo, do mesmo jeito que o conversor empilha depois do tema.',
    diagram: 'Diagrama',
    newBadge: 'NOVO',
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
    dragLabel: (name) => `Arrastar para reordenar ${name}`,
    removeLabel: (name) => `Remover ${name}`,
    moveUp: 'Subir',
    moveDown: 'Descer',
    moveUpLabel: (name) => `Mover ${name} para cima`,
    moveDownLabel: (name) => `Mover ${name} para baixo`,
    reorderInstructions: 'Espaço pega, setas movem, Espaço solta.',
    movedTo: (name, position, total) => `${name} movido para a posição ${position} de ${total}`,
    errorTimeout: 'Tempo esgotado',
    errorSkipped: 'Pulado',
    pdfBundleName: 'pdfs.zip',
    mdBundleName: 'markdown.zip',
    docxBundleName: 'docx.zip',
  },
  themeToggle: {
    toLight: 'Mudar para o tema claro',
    toDark: 'Mudar para o tema escuro',
  },
  toast: {
    dismiss: 'Fechar notificação',
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
  preferences: {
    title: 'Preferências',
    subtitle: 'Por navegador. Nada sai deste dispositivo.',
    sections: { defaults: 'padrões', ui: 'interface', privacy: 'privacidade' },
    defaultLanguage: {
      label: 'Idioma padrão',
      hint: 'Usado quando o idioma do navegador não é suportado.',
    },
    defaultPdfTheme: {
      label: 'Tema padrão do PDF',
      hint: 'Aplicado a cada novo lote de Markdown para PDF.',
    },
    pageSize: {
      label: 'Tamanho de página padrão',
      hint: 'A4 fora dos EUA, Letter dentro.',
    },
    previewNewTab: {
      label: 'Abrir a prévia do PDF em nova aba',
      hint: 'Desligado mantém a prévia embutida.',
    },
    accent: {
      label: 'Cor de destaque',
      hint: 'Vermelho da marca por padrão.',
      swatch: { brand: 'Vermelho da marca', blue: 'Azul', green: 'Verde', graphite: 'Grafite' },
    },
    reduceMotion: {
      label: 'Reduzir animações',
      hint: 'Corta fades e transições. Liga sozinho se o seu sistema pedir.',
    },
    darkMode: {
      label: 'Modo escuro',
      hint: 'Alterna entre o tema claro e o escuro.',
    },
    privacy: {
      badge: 'Sem telemetria. Sem cookies. Sem contas.',
      verified: 'Verificado no build por scripts/audit-deps.py.',
      viewReport: 'Ver relatório',
    },
    reset: 'Limpar todas as preferências',
    on: 'Ligado',
    off: 'Desligado',
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
    preferences: 'Preferencias',
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
      filter: 'Filtro',
      all: 'Todos',
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
    previewLabel: 'Markdown convertido',
    success: 'Markdown generado.',
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
    livePreviewTitle: 'Vista previa del tema en vivo',
    pastedFilename: 'pegado.md',
    success: 'PDF listo.',
  },
  mdToDocx: {
    title: 'Markdown a DOCX',
    subtitle: 'Sube un archivo .md o pega texto y conviértelo a un documento Word.',
    paste: 'O pega markdown aquí...',
    pasteLabel: 'Markdown pegado',
    generate: 'Convertir',
    generating: 'Convirtiendo',
    download: 'Descargar .docx',
    previewEmpty: 'La vista previa aparecerá aquí.',
    pastedFilename: 'pegado.md',
    success: 'DOCX listo.',
  },
  themePicker: {
    label: 'Tema',
    loading: 'Cargando temas…',
    loadError: 'No se pudieron cargar los temas.',
  },
  themesPage: {
    title: 'Biblioteca de temas',
    subtitle: 'El catálogo completo de temas está en camino. Por ahora, elige un tema en el conversor.',
    back: '← Volver a Markdown a PDF',
  },
  previewSamples: {
    document: 'Documento',
    article: 'Artículo',
    resume: 'Currículum',
    email: 'Correo',
    contract: 'Contrato',
    blog: 'Entrada de blog',
  },
  themeLib: {
    title: 'Biblioteca de temas',
    subtitle:
      'Hojas de estilo curadas para el PDF. Elige una, previsualízala en vivo sobre un ejemplo rico y añade tu propio CSS encima.',
    filter: 'Filtro',
    all: 'Todos',
    serif: 'Serif',
    sans: 'Sans',
    mono: 'Mono',
    preview: 'Vista previa en vivo',
    custom: 'CSS propio',
    source: 'CSS del tema',
    clear: 'Limpiar',
    use: 'Usar tema',
    downloadCss: 'Descargar .css',
    readonly: 'solo lectura',
    customHint:
      'Pega CSS para sobrescribir el tema; se aplica a la vista previa en vivo, igual que el conversor lo apila tras el tema.',
    diagram: 'Diagrama',
    newBadge: 'NUEVO',
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
    dragLabel: (name) => `Arrastrar para reordenar ${name}`,
    removeLabel: (name) => `Quitar ${name}`,
    moveUp: 'Subir',
    moveDown: 'Bajar',
    moveUpLabel: (name) => `Mover ${name} hacia arriba`,
    moveDownLabel: (name) => `Mover ${name} hacia abajo`,
    reorderInstructions: 'Espacio agarra, flechas mueven, Espacio suelta.',
    movedTo: (name, position, total) => `${name} movido a la posición ${position} de ${total}`,
    errorTimeout: 'Tiempo agotado',
    errorSkipped: 'Omitido',
    pdfBundleName: 'pdfs.zip',
    mdBundleName: 'markdown.zip',
    docxBundleName: 'docx.zip',
  },
  themeToggle: {
    toLight: 'Cambiar al modo claro',
    toDark: 'Cambiar al modo oscuro',
  },
  toast: {
    dismiss: 'Cerrar notificación',
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
  preferences: {
    title: 'Preferencias',
    subtitle: 'Por navegador. Nada sale de este dispositivo.',
    sections: { defaults: 'valores por defecto', ui: 'interfaz', privacy: 'privacidad' },
    defaultLanguage: {
      label: 'Idioma predeterminado',
      hint: 'Se usa cuando el idioma del navegador no es compatible.',
    },
    defaultPdfTheme: {
      label: 'Tema de PDF predeterminado',
      hint: 'Se aplica a cada nuevo lote de Markdown a PDF.',
    },
    pageSize: {
      label: 'Tamaño de página predeterminado',
      hint: 'A4 fuera de EE. UU., Letter dentro.',
    },
    previewNewTab: {
      label: 'Abrir la vista previa del PDF en una pestaña nueva',
      hint: 'Apagado mantiene la vista previa incrustada.',
    },
    accent: {
      label: 'Color de acento',
      hint: 'Rojo de marca por defecto.',
      swatch: { brand: 'Rojo de marca', blue: 'Azul', green: 'Verde', graphite: 'Grafito' },
    },
    reduceMotion: {
      label: 'Reducir movimiento',
      hint: 'Omite fundidos y transiciones. Se activa solo si tu sistema lo pide.',
    },
    darkMode: {
      label: 'Modo oscuro',
      hint: 'Alterna entre el tema claro y el oscuro.',
    },
    privacy: {
      badge: 'Sin telemetría. Sin cookies. Sin cuentas.',
      verified: 'Verificado en la compilación por scripts/audit-deps.py.',
      viewReport: 'Ver informe',
    },
    reset: 'Restablecer todas las preferencias',
    on: 'Activado',
    off: 'Desactivado',
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
