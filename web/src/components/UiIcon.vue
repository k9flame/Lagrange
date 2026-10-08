<script setup lang="ts">
import { computed } from 'vue'

/**
 * 轻量线性图标集（stroke = currentColor，24x24）。
 * 仅用于 UI chrome；游戏内资源等使用 emoji，避免引入图标库。
 */
const ICONS: Record<string, string> = {
  'chevron-right': '<path d="M9 6l6 6-6 6"/>',
  'chevron-left': '<path d="M15 6l-6 6 6 6"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/>',
  home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.6V20h13V9.6"/>',
  grid:
    '<rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><rect x="13" y="13" width="7" height="7" rx="2"/>',
  gauge: '<path d="M12 13.5 16 9"/><path d="M4.5 19a9 9 0 1 1 15 0"/><circle cx="12" cy="13.5" r="1.4" fill="currentColor" stroke="none"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2.2M12 19.8V22M4.2 4.2l1.6 1.6M18.2 18.2l1.6 1.6M2 12h2.2M19.8 12H22M4.2 19.8l1.6-1.6M18.2 5.8l1.6-1.6"/>',
  moon: '<path d="M21 12.9A8.5 8.5 0 1 1 11.1 3a6.6 6.6 0 0 0 9.9 9.9z"/>',
  auto: '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" stroke="none"/>',
  lock: '<rect x="5" y="11" width="14" height="9" rx="2.4"/><path d="M8.2 11V8a3.8 3.8 0 0 1 7.6 0v3"/>',
  check: '<path d="M5 12.5l4.2 4.2L19 6.5"/>',
  refresh:
    '<path d="M4.5 12a7.5 7.5 0 0 1 12.9-5.2L20 9"/><path d="M20 4v5h-5"/><path d="M19.5 12a7.5 7.5 0 0 1-12.9 5.2L4 15"/><path d="M4 20v-5h5"/>',
  link: '<path d="M9.5 14.5 14.5 9.5"/><path d="M8 12 6 14a3.5 3.5 0 0 0 5 5l2-2"/><path d="M16 12l2-2a3.5 3.5 0 0 0-5-5l-2 2"/>'
}

const props = withDefaults(defineProps<{ name: string; size?: number | string }>(), {
  size: 20
})

const inner = computed(() => ICONS[props.name] ?? '')
const px = computed(() => (typeof props.size === 'number' ? `${props.size}px` : props.size))
</script>

<template>
  <svg
    class="ui-icon"
    :style="{ width: px, height: px }"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    v-html="inner"
  />
</template>

<style scoped>
.ui-icon {
  display: block;
  flex-shrink: 0;
}
</style>
