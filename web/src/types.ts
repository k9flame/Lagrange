/**
 * 角色数据模型 —— 严格对应 /workspace/shared/data-model.md 中的共享契约。
 * 前端只消费该模型，不扩展契约之外的字段。
 */

export type Channel = 'official' | 'bili' | string
export type DataSource = 'mitmproxy' | 'emulator' | 'sample' | 'manual'
export type ShipPosition = '前排' | '中排' | '后排'

export interface CharacterMeta {
  /** 渠道标识，如 official / bili */
  channel: Channel
  /** 渠道显示名，如 "官服" / "B服" */
  channelName: string
  /** 数据来源通道 */
  source: DataSource
  /** 采集时间，ISO8601 */
  capturedAt: string
  /** 协议说明（可选） */
  protocolNote?: string
  /** 各模块是否采集到 */
  completeness: Record<string, boolean>
  /** 缺失字段键 */
  missingFields: string[]
}

export interface CharacterRole {
  uid: string
  nickname: string
  level: number
  serverName: string
  unionName?: string
  power?: number
  updatedAt?: string
}

export interface CharacterCurrencies {
  metal: number
  crystal: number
  deuterium: number
  /** 已占用指挥值 */
  commandPoints: number
  /** 指挥值上限 */
  commandLimit: number
  /** 蓝图点数（如可获取） */
  blueprintPoints?: number
}

export interface BlueprintModule {
  slot: string
  name: string
  unlocked: boolean
}

export interface BlueprintSkill {
  system: string
  name: string
  level: number
  max: number
}

export interface Blueprint {
  id: string
  name: string
  alias?: string
  /** 护卫舰 / 驱逐舰 / 巡洋舰 / 战巡 / 航母 ... */
  shipClass: string
  /** 普通 / 稀有 / 罕见 / 史诗 / 传说 */
  rarity: string
  /** 子型号，如 通用型 / 重炮型 */
  subModel: string
  defaultPosition: ShipPosition | string
  owned: boolean
  level: number
  locked: boolean
  pointsAllocated: number
  pointsTotal: number
  modules: BlueprintModule[]
  skills: BlueprintSkill[]
}

export interface CharacterData {
  meta: CharacterMeta
  role: CharacterRole
  currencies: CharacterCurrencies
  blueprints: Blueprint[]
}

/** 数据加载状态 */
export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error'
