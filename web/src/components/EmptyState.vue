<script setup lang="ts">
defineProps<{
  icon?: string
  title: string
  desc?: string
  actionLabel?: string
}>()

const emit = defineEmits<{ (e: 'action'): void }>()
</script>

<template>
  <div class="empty">
    <div class="empty__icon">{{ icon ?? '📭' }}</div>
    <div class="empty__title">{{ title }}</div>
    <p v-if="desc" class="empty__desc">{{ desc }}</p>
    <button v-if="actionLabel" type="button" class="empty__action pressable" @click="emit('action')">
      {{ actionLabel }}
    </button>
  </div>
</template>
