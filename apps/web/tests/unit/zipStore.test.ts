import { describe, expect, it } from 'vitest'
import { createStoreZip } from '../../src/lib/zipStore'

const enc = new TextEncoder()
const LOCAL_SIG = 0x04034b50
const EOCD_SIG = 0x06054b50

function dv(buf: Uint8Array) {
  return new DataView(buf.buffer, buf.byteOffset, buf.byteLength)
}

describe('createStoreZip', () => {
  it('produces a valid store archive: local + EOCD signatures and entry count', () => {
    const zip = createStoreZip([
      { name: 'a.txt', data: enc.encode('hello') },
      { name: 'b.txt', data: enc.encode('world!') },
    ])
    const view = dv(zip)
    expect(view.getUint32(0, true)).toBe(LOCAL_SIG)
    // EOCD is the last 22 bytes.
    const eocd = zip.length - 22
    expect(view.getUint32(eocd, true)).toBe(EOCD_SIG)
    expect(view.getUint16(eocd + 10, true)).toBe(2) // total entries
  })

  it('is deterministic: same input yields byte-identical output', () => {
    const input = [
      { name: 'one.md', data: enc.encode('# one') },
      { name: 'two.md', data: enc.encode('# two') },
    ]
    const a = createStoreZip(input)
    const b = createStoreZip(input.map((e) => ({ ...e })))
    expect(a).toEqual(b)
  })

  it('is order-independent: entries are sorted by name', () => {
    const x = { name: 'x.md', data: enc.encode('x') }
    const y = { name: 'y.md', data: enc.encode('y') }
    expect(createStoreZip([x, y])).toEqual(createStoreZip([y, x]))
  })

  it('zeroes the timestamp fields for reproducibility', () => {
    const zip = createStoreZip([{ name: 'a', data: enc.encode('a') }])
    const view = dv(zip)
    expect(view.getUint16(10, true)).toBe(0) // mod time
    expect(view.getUint16(12, true)).toBe(0) // mod date
  })

  it('writes the correct CRC-32 in the local header', () => {
    // CRC-32 of "hello" is 0x3610a686.
    const zip = createStoreZip([{ name: 'a', data: enc.encode('hello') }])
    expect(dv(zip).getUint32(14, true)).toBe(0x3610a686)
  })

  it('stores the file bytes verbatim (no compression)', () => {
    const data = enc.encode('verbatim payload')
    const zip = createStoreZip([{ name: 'p.txt', data }])
    // Local header (30) + name length (5) then the raw data.
    const start = 30 + enc.encode('p.txt').length
    expect(Array.from(zip.slice(start, start + data.length))).toEqual(Array.from(data))
  })
})
