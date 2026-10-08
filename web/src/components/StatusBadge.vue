<script setup lang="ts">
import { computed } from 'vue'
import type { Tone } from '@/utils/tone'

const props = withDefaults(
  defineProps<{
    text: string
    tone?: Tone
    size?: 'sm' | 'md'
  }>(),
  { size: 'md' }
)

const style = computed(() =>
  props.tone
    ? { color: props.tone.color, background: props.tone.soft }
    : undefined
)
</script>

<template>
  <span class="badge" :class="`badge--${size}`" :style="style">{{ text }}</span>
</template>

<style scoped>
.badge--sm {
  height: 19px;
  padding: 0 7px;
  font-size: 11px;
  border-radius: 6px;
}
</style>
