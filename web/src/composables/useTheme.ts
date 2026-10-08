import { computed, onMounted, ref, watch } from 'vue'

export type ThemeMode = 'system' | 'light' | 'dark'

const STORAGE_KEY = 'lagrange-theme-mode'

const mode = ref<ThemeMode>(readStoredMode())
const systemPrefersDark = ref(false)
let mediaQuery: MediaQueryList | null = null

function readStoredMode(): ThemeMode {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw === 'light' || raw === 'dark' || raw === 'system') return raw
  } catch {
    /* localStorage 不可用时降级为跟随系统 */
  }
  return 'system'
}

const resolvedTheme = computed<'light' | 'dark'>(() => {
  if (mode.value === 'system') return systemPrefersDark.value ? 'dark' : 'light'
  return mode.value
})

function applyTheme() {
  const el = document.documentElement
  el.setAttribute('data-theme', resolvedTheme.value)
  el.style.colorScheme = resolvedTheme.value
}

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, mode.value)
  } catch {
    /* 忽略写入失败 */
  }
}

function handleSystemChange(e: MediaQueryListEvent) {
  systemPrefersDark.value = e.matches
}

let initialized = false
function initTheme() {
  if (initialized) return
  initialized = true
  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  systemPrefersDark.value = mediaQuery.matches
  mediaQuery.addEventListener('change', handleSystemChange)
  applyTheme()
}

watch([mode, systemPrefersDark], () => {
  persist()
  applyTheme()
})

export function useTheme() {
  onMounted(initTheme)

  const cycle = () => {
    const order: ThemeMode[] = ['system', 'light', 'dark']
    const idx = order.indexOf(mode.value)
    mode.value = order[(idx + 1) % order.length]
  }

  return {
    mode,
    resolvedTheme,
    cycle,
    /** 便于无组件上下文时（如启动阶段）手动初始化 */
    init: initTheme,
    dispose: () => {
      mediaQuery?.removeEventListener('change', handleSystemChange)
      mediaQuery = null
      initialized = false
    }
  }
}

// 启动时立即应用一次，避免首屏闪烁
if (typeof window !== 'undefined') {
  initTheme()
}
