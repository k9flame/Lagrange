<script setup lang="ts">
import { computed } from 'vue'
import type { SegmentOption } from './segment'

const props = defineProps<{
  modelValue: string
  options: SegmentOption[]
  /** 每段最小宽度，超出则横向滚动 */
  minWidth?: number
}>()

const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()

const activeIndex = computed(() => {
  const i = props.options.findIndex((o) => o.value === props.modelValue)
  return i < 0 ? 0 : i
})

const thumbStyle = computed(() => ({
  width: `calc(100% / ${Math.max(props.options.length, 1)})`,
  transform: `translateX(${activeIndex.value * 100}%)`
}))
</script>

<template>
  <div class="seg" role="tablist">
    <div class="seg__track">
      <div class="seg__thumb" :style="thumbStyle" />
      <button
        v-for="opt in options"
        :key="opt.value"
        type="button"
        role="tab"
        class="seg__item"
        :class="{ 'is-active': opt.value === modelValue }"
        :style="{ minWidth: `${minWidth ?? 64}px` }"
        :aria-selected="opt.value === modelValue"
        @click="emit('update:modelValue', opt.value)"
      >
        {{ opt.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.seg {
  margin: 0 16px;
  padding: 2px;
  border-radius: var(--r-sm);
  background: var(--bg-fill);
  overflow-x: auto;
  scrollbar-width: none;
}
.seg::-webkit-scrollbar {
  display: none;
}
.seg__track {
  position: relative;
  display: flex;
  align-items: stretch;
  min-width: 100%;
  height: 32px;
}
.seg__thumb {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  border-radius: 7px;
  background: var(--bg-card);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.14), 0 0 0 0.5px rgba(0, 0, 0, 0.04);
  transition: transform 0.32s var(--ease-spring);
  pointer-events: none;
}
.seg__item {
  position: relative;
  z-index: 1;
  flex: 1 1 0;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--label-secondary);
  white-space: nowrap;
  transition: color 0.24s var(--ease-ios);
}
.seg__item.is-active {
  color: var(--label);
}
</style>
