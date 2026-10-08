<script setup lang="ts">
import { computed, onMounted } from 'vue'
import PageShell from '@/components/PageShell.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import UiIcon from '@/components/UiIcon.vue'
import { useCharacter } from '@/composables/useCharacter'
import type { BlueprintSkill } from '@/types'
import { percent } from '@/utils/format'
import { positionTone, rarityTone, shipClassTone } from '@/utils/tone'

const props = defineProps<{ id: string }>()

const { state, blueprints, loadCharacter, findBlueprint } = useCharacter()

onMounted(() => {
  loadCharacter()
})

const blueprint = computed(() => findBlueprint(props.id))

const pointsPercent = computed(() =>
  blueprint.value ? percent(blueprint.value.pointsAllocated, blueprint.value.pointsTotal) : 0
)
const pointsLabel = computed(() => {
  const bp = blueprint.value
  if (!bp) return ''
  return bp.pointsTotal > 0 ? `${bp.pointsAllocated} / ${bp.pointsTotal}` : '未加点'
})

const unlockedModules = computed(
  () => blueprint.value?.modules.filter((m) => m.unlocked).length ?? 0
)

/** 技能按系统分组，保持原始顺序 */
const skillGroups = computed(() => {
  const groups: { system: string; items: BlueprintSkill[] }[] = []
  for (const skill of blueprint.value?.skills ?? []) {
    let group = groups.find((g) => g.system === skill.system)
    if (!group) {
      group = { system: skill.system, items: [] }
      groups.push(group)
    }
    group.items.push(skill)
  }
  return groups
})

const loading = computed(
  () => (state.status === 'loading' || state.status === 'idle') && !blueprint.value
)
</script>

<template>
  <PageShell
    :back="true"
    back-to="/blueprints"
    :title="blueprint?.name ?? '蓝图详情'"
    :subtitle="blueprint ? `${blueprint.shipClass} · ${blueprint.subModel}` : undefined"
  >
    <!-- 加载中 -->
    <div v-if="loading" class="card-pad stack-12">
      <div class="skeleton" style="height: 180px; border-radius: var(--r-lg)" />
      <div class="skeleton" style="height: 120px" />
    </div>

    <!-- 加载失败 -->
    <EmptyState
      v-else-if="state.status === 'error'"
      icon="📡"
      title="数据加载失败"
      :desc="`无法读取数据源 ${state.source}。`"
      action-label="重新加载"
      @action="loadCharacter(true)"
    />

    <!-- 未找到 -->
    <EmptyState
      v-else-if="!blueprint"
      icon="🧭"
      title="未找到该蓝图"
      :desc="`数据源中不存在 ID 为 ${id} 的蓝图（当前共 ${blueprints.length} 条）。`"
      action-label="返回蓝图列表"
      @action="$router.push('/blueprints')"
    />

    <template v-else>
      <!-- 头部卡片 -->
      <section class="detail-hero enter-item">
        <div class="detail-hero__name">{{ blueprint.name }}</div>
        <div v-if="blueprint.alias" class="detail-hero__alias">“{{ blueprint.alias }}”</div>
        <div class="detail-hero__badges">
          <StatusBadge :text="blueprint.shipClass" :tone="shipClassTone(blueprint.shipClass)" />
          <StatusBadge :text="blueprint.rarity" :tone="rarityTone(blueprint.rarity)" />
          <StatusBadge
            :text="blueprint.defaultPosition"
            :tone="positionTone(blueprint.defaultPosition)"
          />
          <StatusBadge :text="blueprint.owned ? '已拥有' : '未拥有'" />
          <StatusBadge v-if="blueprint.locked" text="已锁定" />
        </div>
        <div class="detail-hero__metrics">
          <div class="detail-hero__metric">
            <div class="detail-hero__metric-label">子型号</div>
            <div class="detail-hero__metric-value" style="font-size: 14px">
              {{ blueprint.subModel }}
            </div>
          </div>
          <div class="detail-hero__metric">
            <div class="detail-hero__metric-label">默认站位</div>
            <div class="detail-hero__metric-value" style="font-size: 14px">
              {{ blueprint.defaultPosition }}
            </div>
          </div>
          <div class="detail-hero__metric">
            <div class="detail-hero__metric-label">等级</div>
            <div class="detail-hero__metric-value">Lv.{{ blueprint.level }}</div>
          </div>
        </div>
      </section>

      <!-- 加点进度 -->
      <h2 class="group-title">加点进度</h2>
      <div class="card">
        <div class="card-pad">
          <div class="metric-head">
            <span class="metric-head__label">已加点数</span>
            <span class="metric-head__value">{{ pointsLabel }}</span>
          </div>
          <ProgressBar :value="pointsPercent" :label="`${pointsPercent.toFixed(0)}%`" />
          <p class="metric-note">
            共 {{ blueprint.modules.length }} 个模块槽位，已解锁 {{ unlockedModules }} 个
          </p>
        </div>
      </div>

      <!-- 模块 -->
      <h2 class="group-title">模块</h2>
      <div class="card-list">
        <template v-if="blueprint.modules.length">
          <div v-for="mod in blueprint.modules" :key="`${mod.slot}-${mod.name}`" class="row">
            <div class="mod-slot" :class="{ 'is-on': mod.unlocked }">{{ mod.slot }}</div>
            <div class="row__body">
              <div class="row__title">{{ mod.name }}</div>
            </div>
            <span class="state-pill" :class="{ 'is-on': mod.unlocked }">
              <UiIcon :name="mod.unlocked ? 'check' : 'lock'" :size="14" />
              {{ mod.unlocked ? '已解锁' : '未解锁' }}
            </span>
          </div>
        </template>
        <div v-else class="mod-empty">该蓝图暂无模块数据</div>
      </div>

      <!-- 技能加点 -->
      <h2 class="group-title">技能加点</h2>
      <template v-if="skillGroups.length">
        <template v-for="group in skillGroups" :key="group.system">
          <div class="group-note" style="padding-bottom: 8px">{{ group.system }}</div>
          <div class="card-list">
            <div v-for="skill in group.items" :key="skill.name" class="row skill-row row--col">
              <div class="skill-head">
                <span class="skill-name">{{ skill.name }}</span>
                <span class="skill-level">{{ skill.level }} / {{ skill.max }}</span>
              </div>
              <ProgressBar
                size="sm"
                :value="percent(skill.level, skill.max)"
                :color="skill.level >= skill.max && skill.max > 0 ? 'var(--success)' : undefined"
              />
            </div>
          </div>
        </template>
      </template>
      <div v-else class="card-list">
        <div class="mod-empty">该蓝图暂无技能加点数据</div>
      </div>
    </template>
  </PageShell>
</template>

<style scoped>
.skill-row {
  flex-direction: column;
  align-items: stretch;
}
.skill-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}
.skill-level {
  font-size: 13px;
  font-weight: 600;
  color: var(--label-secondary);
  font-variant-numeric: tabular-nums;
}
</style>
