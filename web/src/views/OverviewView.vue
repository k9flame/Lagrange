<script setup lang="ts">
import { computed, onMounted } from 'vue'
import PageShell from '@/components/PageShell.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useCharacter } from '@/composables/useCharacter'
import { formatCompact, formatDateTime, formatNumber, percent, sourceLabel } from '@/utils/format'

const { state, blueprints, missingFields, hasMissingFields, loadCharacter } = useCharacter()

onMounted(() => {
  loadCharacter()
})

const role = computed(() => state.data?.role)
const meta = computed(() => state.data?.meta)
const currencies = computed(() => state.data?.currencies)

const cpPercent = computed(() =>
  currencies.value ? percent(currencies.value.commandPoints, currencies.value.commandLimit) : 0
)
const cpRemain = computed(() =>
  currencies.value
    ? Math.max(0, currencies.value.commandLimit - currencies.value.commandPoints)
    : 0
)

const resources = computed(() => {
  const c = currencies.value
  if (!c) return []
  const list = [
    { key: 'metal', label: '金属', icon: '🔩', tone: '#8e8e93', value: c.metal },
    { key: 'crystal', label: '晶体', icon: '💎', tone: '#0a84ff', value: c.crystal },
    { key: 'deuterium', label: '重氢', icon: '⚗️', tone: '#30b0c7', value: c.deuterium }
  ]
  if (c.blueprintPoints != null) {
    list.push({
      key: 'bp',
      label: '蓝图点数',
      icon: '🧩',
      tone: '#af52de',
      value: c.blueprintPoints
    })
  }
  return list
})

const channelTone = { color: '#0a84ff', soft: 'rgba(10,132,255,0.14)' }

const COMPLETENESS_LABELS: Record<string, string> = {
  role: '角色信息',
  currencies: '资源/指挥值',
  blueprints: '蓝图列表',
  points: '加点进度',
  modules: '模块'
}

const completenessList = computed(() =>
  Object.entries(meta.value?.completeness ?? {}).map(([key, ok]) => ({
    key,
    label: COMPLETENESS_LABELS[key] ?? key,
    ok
  }))
)
</script>

<template>
  <PageShell title="角色概览" :subtitle="meta ? `${meta.channelName} · 星际猎人` : undefined">
    <!-- 加载中 -->
    <div v-if="state.status === 'loading' || state.status === 'idle'" class="card-pad stack-12">
      <div class="skeleton" style="height: 148px; border-radius: var(--r-xl)" />
      <div class="skeleton" style="height: 168px" />
      <div class="skeleton" style="height: 96px" />
    </div>

    <!-- 加载失败 -->
    <EmptyState
      v-else-if="state.status === 'error'"
      icon="📡"
      title="数据加载失败"
      :desc="`无法读取数据源 ${state.source}（${state.error ?? '未知错误'}）。可通过 ?data= 指定可访问的 JSON 地址。`"
      action-label="重新加载"
      @action="loadCharacter(true)"
    />

    <!-- 就绪 -->
    <template v-else-if="state.data">
      <!-- 缺失字段提示 -->
      <div v-if="hasMissingFields" class="notice enter-item" style="margin-bottom: 14px">
        <span class="notice__icon">⚠️</span>
        <div>
          <div class="notice__title">部分字段缺失，可手动补录</div>
          <div class="notice__desc">缺失字段：{{ missingFields.join('、') }}</div>
        </div>
      </div>

      <!-- 顶部角色卡 -->
      <section class="hero enter-item">
        <div class="hero__top">
          <div class="hero__avatar">🪐</div>
          <div class="hero__id">
            <div class="hero__name">{{ role?.nickname }}</div>
            <div class="hero__meta">UID {{ role?.uid }} · Lv.{{ role?.level }}</div>
          </div>
          <span class="hero__channel">{{ meta?.channelName }}</span>
        </div>
        <div class="hero__stats">
          <div class="hero__stat">
            <div class="hero__stat-label">等级</div>
            <div class="hero__stat-value">Lv.{{ role?.level }}</div>
          </div>
          <div class="hero__stat">
            <div class="hero__stat-label">战力</div>
            <div class="hero__stat-value">{{ formatCompact(role?.power) }}</div>
          </div>
          <div class="hero__stat">
            <div class="hero__stat-label">蓝图</div>
            <div class="hero__stat-value">{{ blueprints.length }}</div>
          </div>
        </div>
        <div class="hero__foot">
          <span>📍 {{ role?.serverName }}</span>
          <span>{{ role?.unionName ? `联盟 · ${role.unionName}` : '无联盟' }}</span>
        </div>
      </section>

      <!-- 资源 -->
      <h2 class="group-title">资源储备</h2>
      <div class="card-list">
        <div v-for="item in resources" :key="item.key" class="row">
          <div class="row__icon" :style="{ background: `${item.tone}22`, color: item.tone }">
            {{ item.icon }}
          </div>
          <div class="row__body">
            <div class="row__title">{{ item.label }}</div>
          </div>
          <div class="row__value">{{ formatNumber(item.value) }}</div>
        </div>
      </div>

      <!-- 指挥值 -->
      <h2 class="group-title">指挥值</h2>
      <div class="card">
        <div class="card-pad">
          <div class="metric-head">
            <span class="metric-head__label">指挥值占用</span>
            <span class="metric-head__value">
              <span style="color: var(--tint)">{{ currencies?.commandPoints }}</span>
              <span class="text-secondary"> / {{ currencies?.commandLimit }}</span>
            </span>
          </div>
          <ProgressBar :value="cpPercent" :label="`${cpPercent.toFixed(0)}%`" />
          <p class="metric-note">剩余可用指挥值 {{ formatNumber(cpRemain) }}</p>
        </div>
      </div>

      <!-- 采集信息 -->
      <h2 class="group-title">采集信息</h2>
      <div class="card-list">
        <div class="row">
          <div class="row__body"><div class="row__title">渠道</div></div>
          <StatusBadge :text="meta?.channelName ?? '未知渠道'" :tone="channelTone" />
        </div>
        <div class="row">
          <div class="row__body"><div class="row__title">数据来源</div></div>
          <div class="row__value row__value--muted">{{ sourceLabel(meta?.source ?? '') }}</div>
        </div>
        <div class="row">
          <div class="row__body"><div class="row__title">采集时间</div></div>
          <div class="row__value row__value--muted">{{ formatDateTime(meta?.capturedAt) }}</div>
        </div>
        <div class="row">
          <div class="row__body">
            <div class="row__title">数据源</div>
            <div class="row__subtitle">{{ state.source }}</div>
          </div>
        </div>
      </div>
      <p v-if="meta?.protocolNote" class="group-note">{{ meta.protocolNote }}</p>

      <!-- 完整性 -->
      <h2 class="group-title">数据完整性</h2>
      <div class="card">
        <div class="chips">
          <span
            v-for="item in completenessList"
            :key="item.key"
            class="chip"
            :class="item.ok ? 'is-ok' : 'is-miss'"
          >
            {{ item.ok ? '✓' : '✕' }} {{ item.label }}
          </span>
        </div>
      </div>
    </template>
  </PageShell>
</template>
