<script setup lang="ts">
import UiIcon from './UiIcon.vue'

const tabs = [
  { to: '/', name: 'overview', label: '概览', icon: 'gauge' },
  { to: '/blueprints', name: 'blueprints', label: '蓝图', icon: 'grid' }
] as const
</script>

<template>
  <nav class="tabbar" aria-label="主导航">
    <RouterLink
      v-for="tab in tabs"
      :key="tab.name"
      :to="tab.to"
      class="tabbar__item"
      :class="{ 'is-active': $route.name === tab.name || ($route.name === 'blueprint-detail' && tab.name === 'blueprints') }"
    >
      <UiIcon :name="tab.icon" :size="25" />
      <span class="tabbar__label">{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.tabbar__item {
  flex: 1;
  max-width: 128px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 6px 0;
  color: var(--label-secondary);
  border-radius: var(--r-md);
  transition: color 0.2s var(--ease-ios), transform 0.18s var(--ease-spring);
}
.tabbar__item:active {
  transform: scale(0.94);
}
.tabbar__item.is-active {
  color: var(--tint);
}
.tabbar__label {
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.01em;
}
</style>
