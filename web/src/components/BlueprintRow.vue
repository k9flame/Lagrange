<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { Blueprint } from '@/types'
import { positionTone, rarityTone, shipClassTone } from '@/utils/tone'
import { percent } from '@/utils/format'
import ProgressBar from './ProgressBar.vue'
import StatusBadge from './StatusBadge.vue'
import UiIcon from './UiIcon.vue'

const props = defineProps<{ blueprint: Blueprint; index: number }>()
const router = useRouter()

const SHIP_ICONS: Record<string, string> = {
  护卫舰: '🛡️',
  驱逐舰: '🚀',
  巡洋舰: '⚓',
  战巡: '⚔️',
  航母: '🛰️'
}

const shipTone = computed(() => shipClassTone(props.blueprint.shipClass))
const rarTone = computed(() => rarityTone(props.blueprint.rarity))
const posTone = computed(() => positionTone(props.blueprint.defaultPosition))
const icon = computed(() => SHIP_ICONS[props.blueprint.shipClass] ?? '🛸')
const tileStyle = computed(() => ({
  background: shipTone.value.soft,
  color: shipTone.value.color
}))

const pct = computed(() => percent(props.blueprint.pointsAllocated, props.blueprint.pointsTotal))
const pointsLabel = computed(() =>
  props.blueprint.pointsTotal > 0
    ? `${props.blueprint.pointsAllocated}/${props.blueprint.pointsTotal}`
    : '未加点'
)

function open() {
  router.push(`/blueprints/${encodeURIComponent(props.blueprint.id)}`)
}
</script>

<template>
  <li
    class="bp-row row--action enter-item"
    :style="{ animationDelay: `${Math.min(index, 12) * 45}ms` }"
    @click="open"
  >
    <div class="bp-row__tile" :style="tileStyle">{{ icon }}</div>
    <div class="bp-row__body">
      <div class="bp-row__titleline">
        <span class="bp-row__name">{{ blueprint.name }}</span>
        <span v-if="blueprint.locked" class="bp-tag">🔒 锁定</span>
        <span v-else-if="!blueprint.owned" class="bp-tag">未拥有</span>
      </div>
      <div class="bp-row__badges">
        <StatusBadge :text="blueprint.shipClass" :tone="shipTone" size="sm" />
        <StatusBadge :text="blueprint.rarity" :tone="rarTone" size="sm" />
        <StatusBadge :text="blueprint.defaultPosition" :tone="posTone" size="sm" />
        <span v-if="blueprint.alias" class="bp-row__alias">{{ blueprint.alias }}</span>
      </div>
      <ProgressBar class="bp-row__progress" size="sm" :value="pct" :label="pointsLabel" />
    </div>
    <UiIcon name="chevron-right" :size="16" class="chevron" />
  </li>
</template>

<style scoped>
.bp-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  position: relative;
  cursor: pointer;
  transition: background 0.18s var(--ease-ios);
}
.bp-row:active {
  background: var(--bg-fill);
}
.bp-row + .bp-row::before {
  content: '';
  position: absolute;
  top: 0;
  left: 70px;
  right: 0;
  height: 0.5px;
  background: var(--separator);
}
.bp-row__tile {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 22px;
  flex-shrink: 0;
}
.bp-row__body {
  flex: 1;
  min-width: 0;
}
.bp-row__titleline {
  display: flex;
  align-items: center;
  gap: 6px;
}
.bp-row__name {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bp-tag {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 6px;
  background: var(--bg-fill);
  color: var(--label-secondary);
}
.bp-row__badges {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 5px;
  overflow: hidden;
}
.bp-row__alias {
  font-size: 11px;
  color: var(--label-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bp-row__progress {
  margin-top: 8px;
}
</style>
