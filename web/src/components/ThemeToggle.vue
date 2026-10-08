<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from '@/composables/useTheme'
import UiIcon from './UiIcon.vue'

const { mode, cycle } = useTheme()

const iconName = computed(() => (mode.value === 'system' ? 'auto' : mode.value))
const label = computed(() =>
  mode.value === 'system' ? '跟随系统' : mode.value === 'light' ? '浅色' : '深色'
)
</script>

<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="`切换外观（当前：${label}）`"
    :title="`外观：${label}`"
    @click="cycle"
  >
    <UiIcon :name="iconName" :size="18" />
  </button>
</template>

<style scoped>
.theme-toggle {
  width: 36px;
  height: 36px;
  border-radius: var(--r-pill);
  display: grid;
  place-items: center;
  color: var(--tint);
  background: var(--tint-soft);
  transition: transform 0.18s var(--ease-spring), background 0.2s var(--ease-ios);
}
.theme-toggle:active {
  transform: scale(0.9);
}
</style>
