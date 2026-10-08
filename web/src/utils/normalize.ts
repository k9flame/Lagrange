import type {
  Blueprint,
  BlueprintModule,
  BlueprintSkill,
  CharacterCurrencies,
  CharacterData,
  CharacterMeta,
  CharacterRole
} from '@/types'

/** ------------------------- 基础取值保护 ------------------------- */

const isPlainObject = (v: unknown): v is Record<string, unknown> =>
  typeof v === 'object' && v !== null && !Array.isArray(v)

const asString = (v: unknown, fallback = ''): string =>
  typeof v === 'string' ? v : v == null ? fallback : String(v)

const asOptionalString = (v: unknown): string | undefined =>
  typeof v === 'string' && v.length > 0 ? v : undefined

const asNumber = (v: unknown, fallback = 0): number => {
  if (typeof v === 'number' && Number.isFinite(v)) return v
  if (typeof v === 'string' && v.trim() !== '') {
    const n = Number(v)
    if (Number.isFinite(n)) return n
  }
  return fallback
}

const asBoolean = (v: unknown, fallback = false): boolean =>
  typeof v === 'boolean' ? v : fallback

const asArray = <T>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : [])

/** ------------------------- 分块归一化 ------------------------- */

function normalizeMeta(raw: unknown): CharacterMeta {
  const m = isPlainObject(raw) ? raw : {}
  const completenessRaw = isPlainObject(m.completeness) ? m.completeness : {}
  const completeness: Record<string, boolean> = {}
  for (const [key, value] of Object.entries(completenessRaw)) {
    completeness[key] = asBoolean(value, false)
  }

  return {
    channel: asString(m.channel, 'unknown'),
    channelName: asString(m.channelName, '未知渠道'),
    source: (asOptionalString(m.source) ?? 'sample') as CharacterMeta['source'],
    capturedAt: asString(m.capturedAt, ''),
    protocolNote: asOptionalString(m.protocolNote),
    completeness,
    missingFields: asArray<unknown>(m.missingFields)
      .filter((v): v is string => typeof v === 'string')
  }
}

function normalizeRole(raw: unknown): CharacterRole {
  const r = isPlainObject(raw) ? raw : {}
  return {
    uid: asString(r.uid, '—'),
    nickname: asString(r.nickname, '未知指挥官'),
    level: asNumber(r.level, 0),
    serverName: asString(r.serverName, '未知区服'),
    unionName: asOptionalString(r.unionName),
    power: r.power == null ? undefined : asNumber(r.power, 0),
    updatedAt: asOptionalString(r.updatedAt)
  }
}

function normalizeCurrencies(raw: unknown): CharacterCurrencies {
  const c = isPlainObject(raw) ? raw : {}
  return {
    metal: asNumber(c.metal, 0),
    crystal: asNumber(c.crystal, 0),
    deuterium: asNumber(c.deuterium, 0),
    commandPoints: asNumber(c.commandPoints, 0),
    commandLimit: asNumber(c.commandLimit, 0),
    blueprintPoints: c.blueprintPoints == null ? undefined : asNumber(c.blueprintPoints, 0)
  }
}

function normalizeModule(raw: unknown): BlueprintModule {
  const m = isPlainObject(raw) ? raw : {}
  return {
    slot: asString(m.slot, '?'),
    name: asString(m.name, '未命名模块'),
    unlocked: asBoolean(m.unlocked, false)
  }
}

function normalizeSkill(raw: unknown): BlueprintSkill {
  const s = isPlainObject(raw) ? raw : {}
  return {
    system: asString(s.system, '未分类系统'),
    name: asString(s.name, '未命名技能'),
    level: asNumber(s.level, 0),
    max: asNumber(s.max, 0)
  }
}

function normalizeBlueprint(raw: unknown, index: number): Blueprint {
  const b = isPlainObject(raw) ? raw : {}
  return {
    id: asString(b.id, `bp-${index}`),
    name: asString(b.name, '未命名蓝图'),
    alias: asOptionalString(b.alias),
    shipClass: asString(b.shipClass, '未知舰种'),
    rarity: asString(b.rarity, '未知'),
    subModel: asString(b.subModel, '—'),
    defaultPosition: asString(b.defaultPosition, '—'),
    owned: asBoolean(b.owned, false),
    level: asNumber(b.level, 0),
    locked: asBoolean(b.locked, false),
    pointsAllocated: asNumber(b.pointsAllocated, 0),
    pointsTotal: asNumber(b.pointsTotal, 0),
    modules: asArray<unknown>(b.modules).map(normalizeModule),
    skills: asArray<unknown>(b.skills).map(normalizeSkill)
  }
}

/**
 * 将任意（可能不完整 / 非法）的原始数据归一化为标准模型。
 * 缺失字段一律优雅降级为安全默认值，保证视图不崩溃。
 */
export function normalizeCharacter(input: unknown): CharacterData {
  const raw = isPlainObject(input) ? input : {}
  return {
    meta: normalizeMeta(raw.meta),
    role: normalizeRole(raw.role),
    currencies: normalizeCurrencies(raw.currencies),
    blueprints: asArray<unknown>(raw.blueprints).map(normalizeBlueprint)
  }
}
