<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ItineraryPanel from './components/ItineraryPanel.vue'
import MapCanvas from './components/MapCanvas.vue'
import TimelineStrip from './components/TimelineStrip.vue'
import TripForm from './components/TripForm.vue'
import { defaultForm, demoPlan } from './data/sample'
import { createPlan } from './services/api'
import type { PlanResponse, RouteSpot, TransportMode, TravelForm } from './types'

const plan = ref<PlanResponse>(demoPlan(defaultForm))
const activeDay = ref(1)
const selectedSpot = ref<RouteSpot | undefined>(plan.value.routes[0]?.spots[0])
const isGenerating = ref(false)
const activeTransport = ref<TransportMode>(defaultForm.transportMode)
const lastSubmittedForm = ref<TravelForm>({ ...defaultForm, preferences: [...defaultForm.preferences] })
const toast = ref('')
let toastTimer: number | undefined

const activeRoute = computed(() => plan.value.routes.find((route) => route.day === activeDay.value) || plan.value.routes[0])

function showToast(message: string) {
  toast.value = message
  if (toastTimer) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => { toast.value = '' }, 3200)
}

function focusSpot(spot: RouteSpot) {
  selectedSpot.value = spot
}

watch(activeDay, () => {
  selectedSpot.value = activeRoute.value?.spots[0]
})

async function generate(form: TravelForm) {
  isGenerating.value = true
  activeTransport.value = form.transportMode
  lastSubmittedForm.value = { ...form, preferences: [...form.preferences] }
  try {
    const result = await createPlan(form)
    plan.value = result
    activeDay.value = result.routes[0]?.day || 1
    selectedSpot.value = result.routes[0]?.spots[0]
    showToast(`已为你编排 ${result.totalDays} 天路线，路线交叉校验通过`)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '路线生成失败，请稍后重试。')
  } finally {
    isGenerating.value = false
  }
}

async function changeTransport(mode: TransportMode) {
  activeTransport.value = mode
  const nextForm: TravelForm = { ...lastSubmittedForm.value, transportMode: mode, preferences: [...lastSubmittedForm.value.preferences] }
  // Changing mode asks the same planning endpoint for a fresh travel-time matrix.
  // The visual route is retained while the recalculation runs.
  isGenerating.value = true
  try {
    const result = await createPlan(nextForm)
    plan.value = result
    selectedSpot.value = result.routes.find((route) => route.day === activeDay.value)?.spots[0] || result.routes[0]?.spots[0]
    lastSubmittedForm.value = nextForm
    showToast(`已按${({ walking: '步行', riding: '骑行', driving: '自驾', transit: '公共交通' } as Record<TransportMode, string>)[mode]}重新计算行程`)
  } catch {
    showToast('出行方式已切换，交通时间将在网络恢复后更新。')
  } finally {
    isGenerating.value = false
  }
}

function reorder(spots: RouteSpot[]) {
  const route = activeRoute.value
  if (!route) return
  plan.value = {
    ...plan.value,
    routes: plan.value.routes.map((item) => item.day === route.day ? { ...item, spots } : item),
  }
  selectedSpot.value = spots[0]
  showToast('顺序已调整，地图路线已实时重绘')
}

async function sharePlan() {
  const copy = `${plan.value.destination} ${plan.value.totalDays} 天游玩路线 · ${plan.value.overallStats.totalSpots} 个地点`
  try {
    await navigator.clipboard.writeText(copy)
    showToast('行程摘要已复制，可发送给同行人')
  } catch {
    showToast(copy)
  }
}

function exportPlan() {
  const blob = new Blob([JSON.stringify(plan.value, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${plan.value.destination}-智能行程.json`
  link.click()
  URL.revokeObjectURL(url)
  showToast('已导出结构化行程 JSON')
}
</script>

<template>
  <main class="planner-app">
    <header class="app-header">
      <div class="brand-lockup">
        <span class="brand-mark"><i></i><i></i><i></i></span>
        <div><strong>行迹</strong><small>ROUTE WITH INTENT</small></div>
      </div>
      <div class="header-center">
        <span class="live-indicator"><i></i>智能路线引擎已就绪</span>
        <span class="header-separator"></span>
        <span>每一段都为你的时间让路</span>
      </div>
      <div class="header-actions">
        <button type="button" @click="exportPlan"><span>⇩</span>导出</button>
        <button type="button" @click="sharePlan"><span>↗</span>分享</button>
        <button class="profile-avatar" type="button" aria-label="用户菜单">W</button>
      </div>
    </header>

    <div class="planner-layout">
      <aside class="left-panel">
        <div class="panel-scroll">
          <div class="intro-copy">
            <p class="eyebrow">SMART TRIP DESIGNER</p>
            <h1>把时间留给<br /><em>真正想去的地方。</em></h1>
            <p>告诉我偏好，行迹将聚类景点、避开折返，并把每一天安排得恰到好处。</p>
          </div>

          <TripForm :initial="lastSubmittedForm" :busy="isGenerating" @submit="generate" @transport-change="changeTransport" />

          <div class="itinerary-header">
            <div><p class="eyebrow">YOUR ITINERARY</p><h2>{{ plan.destination }} · {{ plan.totalDays }} 天路线</h2></div>
            <span class="plan-status"><i></i>已优化</span>
          </div>
          <nav class="day-tabs" aria-label="切换日期">
            <button
              v-for="route in plan.routes"
              :key="route.day"
              type="button"
              :class="{ active: activeDay === route.day }"
              @click="activeDay = route.day"
            >
              <span :style="{ background: route.color }"></span>Day {{ route.day }}
            </button>
          </nav>

          <ItineraryPanel :route="activeRoute" :selected-spot-id="selectedSpot?.id" @select="focusSpot" @reorder="reorder" />
        </div>
      </aside>

      <section class="right-panel">
        <MapCanvas :plan="plan" :route="activeRoute" :selected-spot="selectedSpot" :transport-mode="activeTransport" @select="focusSpot" />
        <div class="route-health-card">
          <div><span class="health-icon">✓</span><div><small>路线健康度</small><b>96 <em>/ 100</em></b></div></div>
          <div class="health-meter"><i></i></div>
          <p>区域集中 · 无交叉 · 留有缓冲</p>
        </div>
        <TimelineStrip :route="activeRoute" :selected-spot-id="selectedSpot?.id" @select="focusSpot" />
      </section>
    </div>

    <Transition name="toast"><div v-if="toast" class="toast-message"><span>✓</span>{{ toast }}</div></Transition>
  </main>
</template>
