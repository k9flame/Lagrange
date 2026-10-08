<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import UiIcon from './UiIcon.vue'
import ThemeToggle from './ThemeToggle.vue'

const props = withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    /** 是否显示返回按钮 */
    back?: boolean
    /** 返回目标路由 */
    backTo?: string
  }>(),
  { back: false, backTo: '/' }
)

const router = useRouter()
const scrolled = ref(false)
let scrollEl: HTMLElement | null = null

function handleScroll() {
  scrolled.value = (scrollEl?.scrollTop ?? 0) > 46
}

onMounted(() => {
  scrollEl = document.getElementById('app-scroll')
  scrollEl?.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
})

onBeforeUnmount(() => {
  scrollEl?.removeEventListener('scroll', handleScroll)
})

function goBack() {
  router.push(props.backTo)
}
</script>

<template>
  <div class="page">
    <!-- 滚动后出现的毛玻璃紧凑导航栏 -->
    <div class="compactbar" :class="{ 'is-visible': scrolled }">
      <button v-if="back" type="button" class="iconbtn pressable" aria-label="返回" @click="goBack">
        <UiIcon name="chevron-left" :size="22" />
      </button>
      <span class="compactbar__title">{{ title }}</span>
      <span class="compactbar__spacer" />
      <slot name="actions" />
    </div>

    <header class="large-header">
      <div class="large-header__text">
        <button
          v-if="back"
          type="button"
          class="backline pressable"
          aria-label="返回"
          @click="goBack"
        >
          <UiIcon name="chevron-left" :size="18" />
          <span>返回</span>
        </button>
        <h1 class="large-title">{{ title }}</h1>
        <p v-if="subtitle" class="large-subtitle">{{ subtitle }}</p>
      </div>
      <div class="large-header__actions">
        <ThemeToggle />
      </div>
    </header>

    <div class="page__body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.page__body {
  padding-top: 4px;
}
.iconbtn {
  width: 32px;
  height: 32px;
  margin-left: -6px;
  border-radius: var(--r-pill);
  display: grid;
  place-items: center;
  color: var(--tint);
}
.backline {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin-bottom: 6px;
  margin-left: -4px;
  font-size: 17px;
  font-weight: 500;
  color: var(--tint);
}
</style>
