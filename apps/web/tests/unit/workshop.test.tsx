import { beforeEach, describe, expect, it } from 'vitest'
import {
  computeCompletion,
  draftStorageKey,
  flattenDictionary,
  loadDraft,
  saveDraft,
  serializeDraftAsJson,
  serializeDraftAsTs,
} from '../../src/i18n/workshop'

beforeEach(() => {
  window.localStorage.clear()
})

describe('flattenDictionary', () => {
  it('keeps only string leaves with dotted paths', () => {
    const flat = flattenDictionary({ a: 'x', nested: { b: 'y', deep: { c: 'z' } } })
    expect(flat).toEqual({ a: 'x', 'nested.b': 'y', 'nested.deep.c': 'z' })
  })

  it('excludes function and array values (not plain-text translatable)', () => {
    const flat = flattenDictionary({ s: 'keep', fn: (n: number) => `${n}`, list: ['a', 'b'] })
    expect(flat).toEqual({ s: 'keep' })
    expect('fn' in flat).toBe(false)
    expect('list' in flat).toBe(false)
  })
})

describe('computeCompletion', () => {
  const en = { a: '1', b: '2', c: '3' }

  it('is 100% when every key differs from English', () => {
    const r = computeCompletion(en, { a: 'x', b: 'y', c: 'z' })
    expect(r).toMatchObject({ total: 3, translated: 3, pct: 100 })
    expect(r.untranslated).toEqual([])
  })

  it('flags keys still identical to English as untranslated', () => {
    const r = computeCompletion(en, { a: 'x', b: '2', c: '3' })
    expect(r.translated).toBe(1)
    expect(r.untranslated.sort()).toEqual(['b', 'c'])
    expect(r.pct).toBe(33)
  })

  it('counts a draft that diverges from English as translated', () => {
    const r = computeCompletion(en, { a: '1', b: '2', c: '3' }, { a: 'traducao' })
    expect(r.translated).toBe(1)
    expect(r.untranslated.sort()).toEqual(['b', 'c'])
  })

  it('keeps a draft equal to English untranslated', () => {
    const r = computeCompletion(en, { a: 'x' }, { a: '1' })
    expect(r.untranslated).toContain('a')
  })
})

describe('draft persistence', () => {
  it('round-trips per locale and isolates locales', () => {
    saveDraft('pt', { greeting: 'ola' })
    expect(loadDraft('pt')).toEqual({ greeting: 'ola' })
    expect(loadDraft('es')).toEqual({})
    expect(window.localStorage.getItem(draftStorageKey('pt'))).toContain('ola')
  })

  it('returns an empty object for malformed storage', () => {
    window.localStorage.setItem(draftStorageKey('pt'), 'not json')
    expect(loadDraft('pt')).toEqual({})
  })
})

describe('serializers', () => {
  it('serializeDraftAsJson round-trips to a nested object', () => {
    const json = serializeDraftAsJson({ 'nav.about': 'Sobre', 'home.title': 'Inicio' })
    expect(JSON.parse(json)).toEqual({ nav: { about: 'Sobre' }, home: { title: 'Inicio' } })
  })

  it('serializeDraftAsTs nests by dotted path and quotes values', () => {
    const ts = serializeDraftAsTs('pt', { 'nav.about': 'Sobre', 'home.title': 'Inicio' })
    expect(ts).toContain('nav: {')
    expect(ts).toContain("about: 'Sobre',")
    expect(ts).toContain('home: {')
    expect(ts).toContain("title: 'Inicio',")
  })

  it('escapes single quotes in TS values', () => {
    const ts = serializeDraftAsTs('pt', { k: "it's" })
    expect(ts).toContain("k: 'it\\'s',")
  })

  it('returns a comment when the draft is empty', () => {
    expect(serializeDraftAsTs('pt', {})).toContain('no translations drafted')
  })
})
