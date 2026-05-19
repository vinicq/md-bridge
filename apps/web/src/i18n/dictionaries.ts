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
  }
  home: {
    title: string
    subtitle: string
    cards: {
      pdfToMd: { title: string; body: string; cta: string }
      mdToPdf: { title: string; body: string; cta: string }
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
    warnings: string
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
    pastedFilename: string
    success: string
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
    downloadAll: string
    clear: string
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
  }
  languageSwitcher: {
    label: string
  }
}

const en: Dictionary = {
  nav: {
    pdfToMd: 'PDF · MD',
    mdToPdf: 'MD · PDF',
    about: 'About',
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
    warnings: 'Warnings',
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
    pastedFilename: 'pasted.md',
    success: 'PDF ready.',
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
    downloadAll: 'Download all (.zip)',
    clear: 'Clear list',
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
  },
  languageSwitcher: {
    label: 'Language',
  },
}

const pt: Dictionary = {
  nav: {
    pdfToMd: 'PDF · MD',
    mdToPdf: 'MD · PDF',
    about: 'Sobre',
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
    warnings: 'Avisos',
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
    pastedFilename: 'colado.md',
    success: 'PDF pronto.',
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
    downloadAll: 'Baixar todos (.zip)',
    clear: 'Limpar lista',
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
  },
  languageSwitcher: {
    label: 'Idioma',
  },
}

const es: Dictionary = {
  nav: {
    pdfToMd: 'PDF · MD',
    mdToPdf: 'MD · PDF',
    about: 'Acerca de',
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
    warnings: 'Advertencias',
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
    pastedFilename: 'pegado.md',
    success: 'PDF listo.',
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
    downloadAll: 'Descargar todo (.zip)',
    clear: 'Limpiar lista',
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
  },
  languageSwitcher: {
    label: 'Idioma',
  },
}

export const DICTIONARIES: Record<Locale, Dictionary> = { en, pt, es }

export type { Dictionary }
