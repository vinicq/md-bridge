/**
 * Minimal store-only ZIP encoder (no compression), dependency-free.
 *
 * md-bridge bundles markdown or PDF files for a one-click "download all". The
 * files are deterministic conversions, not size-sensitive payloads, so DEFLATE
 * buys nothing here. Storing the bytes verbatim keeps the output bit-for-bit
 * reproducible: entries are sorted by name and every timestamp is zeroed, so the
 * same set of files always produces the same archive bytes. That determinism is
 * the reason this is hand-rolled instead of pulling in a zip dependency.
 *
 * Format: APPNOTE.TXT, local file headers + central directory + EOCD, all
 * little-endian. Method 0 (store), general-purpose flag bit 11 (UTF-8 names).
 */

export interface ZipEntry {
  name: string
  data: Uint8Array
}

const CRC_TABLE = (() => {
  const table = new Uint32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    table[n] = c >>> 0
  }
  return table
})()

function crc32(data: Uint8Array): number {
  let c = 0xffffffff
  for (let i = 0; i < data.length; i++) {
    c = CRC_TABLE[(c ^ data[i]) & 0xff] ^ (c >>> 8)
  }
  return (c ^ 0xffffffff) >>> 0
}

const LOCAL_HEADER = 30
const CENTRAL_HEADER = 46
const EOCD = 22
const UTF8_FLAG = 0x0800
const VERSION = 20 // 2.0, the minimum for store

export function createStoreZip(entries: ZipEntry[]): Uint8Array<ArrayBuffer> {
  const enc = new TextEncoder()
  // Sort by name so archive bytes do not depend on input order.
  const items = [...entries]
    .sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))
    .map((e) => ({ nameBytes: enc.encode(e.name), data: e.data, crc: crc32(e.data) }))

  const localSize = items.reduce((n, it) => n + LOCAL_HEADER + it.nameBytes.length + it.data.length, 0)
  const centralSize = items.reduce((n, it) => n + CENTRAL_HEADER + it.nameBytes.length, 0)
  const buf = new Uint8Array(localSize + centralSize + EOCD)
  const dv = new DataView(buf.buffer)

  const offsets: number[] = []
  let pos = 0

  for (const it of items) {
    offsets.push(pos)
    dv.setUint32(pos, 0x04034b50, true) // local file header signature
    dv.setUint16(pos + 4, VERSION, true)
    dv.setUint16(pos + 6, UTF8_FLAG, true)
    dv.setUint16(pos + 8, 0, true) // method: store
    dv.setUint16(pos + 10, 0, true) // mod time: zeroed for determinism
    dv.setUint16(pos + 12, 0, true) // mod date: zeroed for determinism
    dv.setUint32(pos + 14, it.crc, true)
    dv.setUint32(pos + 18, it.data.length, true) // compressed size == size
    dv.setUint32(pos + 22, it.data.length, true)
    dv.setUint16(pos + 26, it.nameBytes.length, true)
    dv.setUint16(pos + 28, 0, true) // extra length
    buf.set(it.nameBytes, pos + LOCAL_HEADER)
    buf.set(it.data, pos + LOCAL_HEADER + it.nameBytes.length)
    pos += LOCAL_HEADER + it.nameBytes.length + it.data.length
  }

  const centralStart = pos
  items.forEach((it, i) => {
    dv.setUint32(pos, 0x02014b50, true) // central directory header signature
    dv.setUint16(pos + 4, VERSION, true) // version made by
    dv.setUint16(pos + 6, VERSION, true) // version needed
    dv.setUint16(pos + 8, UTF8_FLAG, true)
    dv.setUint16(pos + 10, 0, true) // method: store
    dv.setUint16(pos + 12, 0, true) // mod time
    dv.setUint16(pos + 14, 0, true) // mod date
    dv.setUint32(pos + 16, it.crc, true)
    dv.setUint32(pos + 20, it.data.length, true)
    dv.setUint32(pos + 24, it.data.length, true)
    dv.setUint16(pos + 28, it.nameBytes.length, true)
    dv.setUint16(pos + 30, 0, true) // extra length
    dv.setUint16(pos + 32, 0, true) // comment length
    dv.setUint16(pos + 34, 0, true) // disk number start
    dv.setUint16(pos + 36, 0, true) // internal attributes
    dv.setUint32(pos + 38, 0, true) // external attributes
    dv.setUint32(pos + 42, offsets[i], true) // local header offset
    buf.set(it.nameBytes, pos + CENTRAL_HEADER)
    pos += CENTRAL_HEADER + it.nameBytes.length
  })

  dv.setUint32(pos, 0x06054b50, true) // end of central directory signature
  dv.setUint16(pos + 4, 0, true) // disk number
  dv.setUint16(pos + 6, 0, true) // central dir start disk
  dv.setUint16(pos + 8, items.length, true) // entries on this disk
  dv.setUint16(pos + 10, items.length, true) // total entries
  dv.setUint32(pos + 12, centralSize, true) // central dir size
  dv.setUint32(pos + 16, centralStart, true) // central dir offset
  dv.setUint16(pos + 20, 0, true) // comment length

  return buf
}
