import { useCallback, useRef, useState, type DragEvent } from 'react'
import { useTranslation } from '../i18n'
import './DropZone.css'

interface DropZoneProps {
  accept: string
  acceptLabel: string
  /**
   * Called with the list of files the user dropped or selected. Always
   * receives an array, so callers can choose between single-file and batch
   * UIs based on its length.
   */
  onFiles: (files: File[]) => void
  disabled?: boolean
  /** When true, the input accepts more than one file at once. */
  multiple?: boolean
}

function matchesAccept(file: File, accept: string): boolean {
  const tokens = accept
    .split(',')
    .map((t) => t.trim().toLowerCase())
    .filter(Boolean)
  if (tokens.length === 0) return true
  const name = file.name.toLowerCase()
  const mime = file.type.toLowerCase()
  return tokens.some((t) => {
    if (t.startsWith('.')) return name.endsWith(t)
    return mime === t
  })
}

/**
 * Walk a folder dropped via the DataTransfer API and flatten it into a
 * `File[]`. Falls back to a flat file list when the folder API is missing.
 */
async function readDroppedFiles(items: DataTransferItemList | null, fallback: FileList | null): Promise<File[]> {
  if (!items || items.length === 0) {
    return fallback ? Array.from(fallback) : []
  }
  const out: File[] = []
  const walkers: Promise<void>[] = []
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.kind !== 'file') continue
    const entry = (item as unknown as { webkitGetAsEntry?: () => FileSystemEntry | null }).webkitGetAsEntry?.()
    if (entry) {
      walkers.push(walkEntry(entry, out))
    } else {
      const file = item.getAsFile()
      if (file) out.push(file)
    }
  }
  await Promise.all(walkers)
  return out
}

async function walkEntry(entry: FileSystemEntry, out: File[]): Promise<void> {
  if (entry.isFile) {
    const fileEntry = entry as FileSystemFileEntry
    await new Promise<void>((resolve) => {
      fileEntry.file(
        (file) => {
          out.push(file)
          resolve()
        },
        () => resolve(),
      )
    })
    return
  }
  if (entry.isDirectory) {
    const dirEntry = entry as FileSystemDirectoryEntry
    const reader = dirEntry.createReader()
    const readBatch = (): Promise<FileSystemEntry[]> =>
      new Promise((resolve) => {
        reader.readEntries(
          (entries) => resolve(entries),
          () => resolve([]),
        )
      })
    let batch = await readBatch()
    while (batch.length > 0) {
      for (const child of batch) {
        await walkEntry(child, out)
      }
      batch = await readBatch()
    }
  }
}

export function DropZone({
  accept,
  acceptLabel,
  onFiles,
  disabled = false,
  multiple = false,
}: DropZoneProps) {
  const { t } = useTranslation()
  const [over, setOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement | null>(null)
  // Depth counter for drag enter/leave. Crossing into a child fires dragleave
  // on the container before the child's dragenter; counting keeps the highlight
  // steady until the drag truly leaves the zone (#359). A counter rather than
  // relatedTarget/contains because some engines (and jsdom) report a null
  // relatedTarget on dragleave.
  const dragDepth = useRef(0)

  const handleFiles = useCallback(
    (selected: File[]) => {
      const valid = selected.filter((f) => matchesAccept(f, accept))
      const rejected = selected.length - valid.length
      if (valid.length === 0) {
        setError(t.dropzone.invalidType(acceptLabel))
        return
      }
      setError(rejected > 0 ? t.dropzone.someInvalid(rejected, acceptLabel) : null)
      onFiles(valid)
    },
    [accept, acceptLabel, onFiles, t.dropzone],
  )

  const onDrop = async (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    dragDepth.current = 0
    setOver(false)
    if (disabled) return
    const files = await readDroppedFiles(
      event.dataTransfer.items,
      event.dataTransfer.files,
    )
    if (files.length === 0) return
    handleFiles(multiple ? files : files.slice(0, 1))
  }

  const onDragEnter = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    if (disabled) return
    dragDepth.current += 1
    setOver(true)
  }

  const onDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    if (!disabled) setOver(true)
  }

  const onDragLeave = () => {
    // Balance the enter count; only drop the highlight once the drag has left
    // the zone and all of its children (#359).
    dragDepth.current = Math.max(0, dragDepth.current - 1)
    if (dragDepth.current === 0) setOver(false)
  }

  return (
    <div className="dropzone-wrapper">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="dropzone__input"
        disabled={disabled}
        multiple={multiple}
        tabIndex={-1}
        aria-hidden="true"
        onChange={(e) => {
          const list = e.target.files ? Array.from(e.target.files) : []
          if (list.length > 0) handleFiles(list)
          e.target.value = ''
        }}
      />
      <div
        className={`dropzone ${over ? 'is-over' : ''} ${disabled ? 'is-disabled' : ''}`.trim()}
        onDrop={onDrop}
        onDragEnter={onDragEnter}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        role="button"
        tabIndex={disabled ? -1 : 0}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (disabled) return
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            inputRef.current?.click()
          }
        }}
        aria-disabled={disabled || undefined}
        aria-label={t.dropzone.ariaLabel(acceptLabel)}
      >
        <div className="dropzone__inner">
          <strong className="dropzone__name">
            {multiple ? t.dropzone.dropFiles(acceptLabel) : t.dropzone.dropFile(acceptLabel)}
          </strong>
          <span className="dropzone__hint">
            {multiple ? t.dropzone.orClickMany : t.dropzone.orClick}
          </span>
          {error && (
            <span className="dropzone__error" role="alert">
              {error}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
