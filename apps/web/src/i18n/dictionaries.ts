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
      'md-bridge converts files between two formats: PDF (the standard for printing and sharing finished documents) and Markdown (a lightweight text format used by developers, writers, and tools like GitHub, Obsidian, and Notion). The whole thing runs on your machine, so files never leave your computer.',
    how: {
      title: 'How it works',
      p1:
        'From PDF to Markdown: the app reads the font size and layout of the PDF to figure out what is a heading, what is a paragraph, what is a list, and what is a table. It then writes a clean Markdown file with that structure preserved.',
      p2:
        'From Markdown to PDF: the app converts the text into a styled web page and prints that page to PDF using the same engine browsers use.',
    },
    limits: {
      title: 'Known limits',
      items: [
        'Scanned PDFs (images of paper, not real text) cannot be read yet. Run an OCR tool such as Tesseract on them first.',
        'Tables with cells merged across rows or columns may come out flattened.',
        'Headers and footers that repeat on every page are dropped automatically.',
      ],
    },
    more: {
      title: 'Built with',
      body:
        'Python and FastAPI on the server side (the part that does the actual conversion), React on the page you are looking at, and a headless Chromium browser to render Markdown back into PDF. Everything is open source and ships with the project.',
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
      'O md-bridge converte arquivos entre dois formatos: PDF (o padrão para imprimir e compartilhar documentos prontos) e Markdown (um formato de texto leve usado por desenvolvedores, escritores e ferramentas como GitHub, Obsidian e Notion). Tudo roda na sua máquina, então os arquivos nunca saem do seu computador.',
    how: {
      title: 'Como funciona',
      p1:
        'De PDF para Markdown: o app lê o tamanho da fonte e a posição do texto no PDF para descobrir o que é título, parágrafo, lista ou tabela. Depois gera um Markdown limpo com essa estrutura preservada.',
      p2:
        'De Markdown para PDF: o app transforma o texto em uma página web estilizada e imprime essa página como PDF usando o mesmo motor dos navegadores.',
    },
    limits: {
      title: 'Limites conhecidos',
      items: [
        'PDFs escaneados (imagens de papel, sem texto real) ainda não funcionam. Rode antes uma ferramenta de OCR como o Tesseract.',
        'Tabelas com células mescladas entre linhas ou colunas podem sair achatadas.',
        'Cabeçalhos e rodapés que se repetem em todas as páginas são removidos automaticamente.',
      ],
    },
    more: {
      title: 'Feito com',
      body:
        'Python e FastAPI no servidor (a parte que faz a conversão de verdade), React na página que você está vendo, e um navegador Chromium em modo headless para gerar os PDFs. Tudo é open source e vem junto com o projeto.',
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
      'md-bridge convierte archivos entre dos formatos: PDF (el estándar para imprimir y compartir documentos terminados) y Markdown (un formato de texto ligero usado por desarrolladores, escritores y herramientas como GitHub, Obsidian y Notion). Todo se ejecuta en tu máquina, así que los archivos nunca salen de tu computadora.',
    how: {
      title: 'Cómo funciona',
      p1:
        'De PDF a Markdown: la app lee el tamaño de fuente y la distribución del PDF para identificar encabezados, párrafos, listas y tablas. Luego escribe un archivo Markdown limpio con esa estructura preservada.',
      p2:
        'De Markdown a PDF: la app convierte el texto en una página web con estilos e imprime esa página como PDF usando el mismo motor que usan los navegadores.',
    },
    limits: {
      title: 'Límites conocidos',
      items: [
        'Los PDF escaneados (imágenes de papel, no texto real) todavía no se pueden leer. Ejecuta antes una herramienta de OCR como Tesseract.',
        'Las tablas con celdas combinadas entre filas o columnas pueden salir aplanadas.',
        'Los encabezados y pies de página que se repiten en todas las páginas se eliminan automáticamente.',
      ],
    },
    more: {
      title: 'Construido con',
      body:
        'Python y FastAPI en el servidor (la parte que hace la conversión real), React en la página que estás viendo, y un navegador Chromium headless para renderizar Markdown de vuelta a PDF. Todo es open source y viene incluido en el proyecto.',
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
