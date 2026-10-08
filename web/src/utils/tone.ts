/** 稀有度 / 站位 / 舰种的视觉映射（仅用于展示，不改变数据契约） */

export interface Tone {
  /** 主色 */
  color: string
  /** 柔和背景色 */
  soft: string
}

const RARITY_TONES: Record<string, Tone> = {
  普通: { color: '#8e8e93', soft: 'rgba(142,142,147,0.16)' },
  稀有: { color: '#0a84ff', soft: 'rgba(10,132,255,0.14)' },
  罕见: { color: '#30d158', soft: 'rgba(48,209,88,0.16)' },
  史诗: { color: '#af52de', soft: 'rgba(175,82,222,0.16)' },
  传说: { color: '#ff9f0a', soft: 'rgba(255,159,10,0.18)' }
}

const POSITION_TONES: Record<string, Tone> = {
  前排: { color: '#ff3b30', soft: 'rgba(255,59,48,0.14)' },
  中排: { color: '#ff9500', soft: 'rgba(255,149,0,0.15)' },
  后排: { color: '#30b0c7', soft: 'rgba(48,176,199,0.16)' }
}

const SHIPCLASS_TONES: Record<string, Tone> = {
  护卫舰: { color: '#30b0c7', soft: 'rgba(48,176,199,0.15)' },
  驱逐舰: { color: '#34c759', soft: 'rgba(52,199,89,0.15)' },
  巡洋舰: { color: '#0a84ff', soft: 'rgba(10,132,255,0.15)' },
  战巡: { color: '#af52de', soft: 'rgba(175,82,222,0.15)' },
  航母: { color: '#ff9f0a', soft: 'rgba(255,159,10,0.16)' }
}

const FALLBACK: Tone = { color: '#8e8e93', soft: 'rgba(142,142,147,0.16)' }

export function rarityTone(rarity: string): Tone {
  return RARITY_TONES[rarity] ?? FALLBACK
}

export function positionTone(position: string): Tone {
  return POSITION_TONES[position] ?? FALLBACK
}

export function shipClassTone(shipClass: string): Tone {
  return SHIPCLASS_TONES[shipClass] ?? FALLBACK
}

export const RARITY_ORDER = ['普通', '稀有', '罕见', '史诗', '传说']
