<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageShell from '@/components/PageShell.vue'
import SegmentedControl from '@/components/SegmentedControl.vue'
import type { SegmentOption } from '@/components/segment'
import BlueprintRow from '@/components/BlueprintRow.vue'
import EmptyState from '@/components/EmptyState.vue'
import UiIcon from '@/components/UiIcon.vue'
import { useCharacter } from '@/composables/useCharacter'
import { RARITY_ORDER } from '@/utils/tone'

const { state, blueprints, loadCharacter } = useCharacter()

onMounted(() => {
  loadCharacter()
})

const ALL = '__all__'
const query = ref('')
const shipClassFilter = ref(ALL)
const rarityFilter = ref(ALL)

const shipClassOptions = computed<SegmentOption[]>(() => {
  const seen: string[] = []
  for (const bp of blueprints.value) {
    if (!seen.includes(bp.shipClass)) seen.push(bp.shipClass)
  }
  return [{ value: ALL, label: '全部' }, ...seen.map((s) => ({ value: s, label: s }))]
})

const rarityOptions = computed<SegmentOption[]>(() => {
  const present = new Set(blueprints.value.map((b) => b.rarity))
  const ordered = RARITY_ORDER.filter((r) => present.has(r))
  for (const r of present) {
    if (!ordered.includes(r)) ordered.push(r)
  }
  return [{ value: ALL, label: '全部' }, ...ordered.map((r) => ({ value: r, label: r }))]
})

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return blueprints.value.filter((bp) => {
    if (shipClassFilter.value !== ALL && bp.shipClass !== shipClassFilter.value) return false
    if (rarityFilter.value !== ALL && bp.rarity !== rarityFilter.value) return false
    if (!q) return true
    return (
      bp.name.toLowerCase().includes(q) ||
      (bp.alias ?? '').toLowerCase().includes(q) ||
      bp.id.toLowerCase().includes(q) ||
      bp.subModel.toLowerCase().includes(q)
    )
  })
})

const hasData = computed(() => state.status === 'ready' && blueprints.value.length > 0)
const noResult = computed(() => hasData.value && filtered.value.length === 0)
</script>

<template>
  <PageShell title="蓝图" :subtitle="hasData ? `共 ${blueprints.length} 艘 · 当前显示 ${filtered.length} 艘` : undefined">
    <!-- 加载中 -->
    <div v-if="state.status === 'loading' || state.status === 'idle'" class="card-pad stack-12">
      <div class="skeleton" style="height: 36px; border-radius: var(--r-sm)" />
      <div class="skeleton" style="height: 36px; border-radius: var(--r-sm)" />
      <div class="skeleton" style="height: 260px" />
    </div>

    <!-- 加载失败 -->
    <EmptyState
      v-else-if="state.status === 'error'"
      icon="📡"
      title="数据加载失败"
      :desc="`无法读取数据源 ${state.source}（${state.error ?? '未知错误'}）。`"
      action-label="重新加载"
      @action="loadCharacter(true)"
    />

    <template v-else>
      <!-- 搜索框 -->
      <div class="searchbar">
        <UiIcon name="search" :size="17" />
        <input v-model="query" type="search" placeholder="搜索名称 / 别名 / 型号" aria-label="搜索蓝图" />
      </div>

      <!-- 舰种筛选 -->
      <h2 class="group-title">按舰种</h2>
      <SegmentedControl v-model="shipClassFilter" :options="shipClassOptions" :min-width="56" />

      <!-- 稀有度筛选 -->
      <h2 class="group-title">按稀有度</h2>
      <SegmentedControl v-model="rarityFilter" :options="rarityOptions" :min-width="56" />

      <!-- 列表 -->
      <h2 class="group-title">蓝图列表</h2>

      <EmptyState
        v-if="!hasData"
        icon="📦"
        title="暂无蓝图数据"
        desc="当前数据源未包含蓝图列表，或该模块未采集成功。"
      />
      <EmptyState
        v-else-if="noResult"
        icon="🔍"
        title="没有匹配的蓝图"
        desc="试试调整搜索关键词或筛选条件。"
      />
      <ul v-else class="card-list">
        <BlueprintRow
          v-for="(bp, i) in filtered"
          :key="bp.id"
          :blueprint="bp"
          :index="i"
        />
      </ul>
    </template>
  </PageShell>
</template>
