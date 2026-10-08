<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** 0 - 100 */
    value: number
    label?: string
    size?: 'sm' | 'md'
    color?: string
  }>(),
  { size: 'md' }
)

const clamped = computed(() => Math.min(100, Math.max(0, props.value)))
const fillStyle = computed(() =>
  props.color ? { background: props.color } : undefined
)
</script>

<template>
  <div class="progress" :class="`progress--${size}`">
    <div class="progress__track">
      <div class="progress__fill" :style="{ width: `${clamped}%`, ...fillStyle }" />
    </div>
    <span v-if="label" class="progress__label">{{ label }}</span>
  </div>
</template>
