<script setup lang="ts">
import { onMounted } from 'vue'
import TabBar from './components/TabBar.vue'
import { loadCharacter } from './composables/useCharacter'

onMounted(() => {
  loadCharacter()
})
</script>

<template>
  <div class="env-bg" aria-hidden="true" />
  <div class="app-root">
    <div class="device">
      <div class="device__screen">
        <main id="app-scroll" class="app-scroll">
          <RouterView v-slot="{ Component }">
            <Transition name="page" mode="out-in">
              <component :is="Component" :key="$route.path" />
            </Transition>
          </RouterView>
        </main>
        <TabBar />
      </div>
    </div>
  </div>
</template>
