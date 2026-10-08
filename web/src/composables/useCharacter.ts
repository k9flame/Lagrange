import { computed, reactive } from 'vue'
import type { Blueprint, CharacterData, LoadStatus } from '@/types'
import { normalizeCharacter } from '@/utils/normalize'

interface CharacterState {
  status: LoadStatus
  error: string | null
  /** 实际使用的数据源地址 */
  source: string
  data: CharacterData | null
}

const DEFAULT_SOURCE = '/data/character.json'

const state = reactive<CharacterState>({
  status: 'idle',
  error: null,
  source: DEFAULT_SOURCE,
  data: null
})

/** 解析数据源：优先 `?data=` 查询参数，否则使用内置样例 */
function resolveSource(): string {
  if (typeof window === 'undefined') return DEFAULT_SOURCE
  const params = new URLSearchParams(window.location.search)
  const custom = params.get('data')
  return custom && custom.trim() ? custom.trim() : DEFAULT_SOURCE
}

let inflight: Promise<void> | null = null

/** 加载并归一化角色数据（全局单例，多个视图共享） */
export function loadCharacter(force = false): Promise<void> {
  if (inflight) return inflight
  if (!force && state.status === 'ready') return Promise.resolve()

  const source = resolveSource()
  state.source = source
  state.status = 'loading'
  state.error = null

  inflight = (async () => {
    try {
      const res = await fetch(source, { headers: { Accept: 'application/json' } })
      if (!res.ok) {
        throw new Error(`HTTP ${res.status} ${res.statusText}`)
      }
      const raw: unknown = await res.json()
      state.data = normalizeCharacter(raw)
      state.status = 'ready'
    } catch (err) {
      state.data = null
      state.status = 'error'
      state.error = err instanceof Error ? err.message : String(err)
    } finally {
      inflight = null
    }
  })()

  return inflight
}

/** 供视图使用的响应式只读视图 */
export function useCharacter() {
  const blueprints = computed<Blueprint[]>(() => state.data?.blueprints ?? [])
  const missingFields = computed<string[]>(() => state.data?.meta.missingFields ?? [])
  const hasMissingFields = computed(() => missingFields.value.length > 0)

  const findBlueprint = (id: string): Blueprint | undefined =>
    blueprints.value.find((b) => b.id === id)

  return {
    state,
    blueprints,
    missingFields,
    hasMissingFields,
    loadCharacter,
    findBlueprint
  }
}
