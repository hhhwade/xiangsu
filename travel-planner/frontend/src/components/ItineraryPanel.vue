<script setup lang="ts">
import { ref } from 'vue'
import type { DayRoute, RouteSpot } from '../types'

const props = defineProps<{
  route?: DayRoute
  selectedSpotId?: string
}>()
const emit = defineEmits<{
  select: [spot: RouteSpot]
  reorder: [spots: RouteSpot[]]
}>()

const draggingIndex = ref<number | null>(null)
const collapsed = ref(false)

function dragStart(index: number, event: DragEvent) {
  draggingIndex.value = index
  event.dataTransfer?.setData('text/plain', String(index))
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function dropAt(index: number) {
  if (draggingIndex.value === null || draggingIndex.value === index || !props.route) {
    draggingIndex.value = null
    return
  }
  const spots = [...props.route.spots]
  const [moved] = spots.splice(draggingIndex.value, 1)
  spots.splice(index, 0, moved)
  draggingIndex.value = null
  emit('reorder', spots)
}

function endDrag() {
  draggingIndex.value = null
}
</script>

<template>
  <section v-if="route" class="itinerary-panel">
    <div class="route-summary">
      <div class="route-summary-main">
        <span class="color-orb" :style="{ backgroundColor: route.color }"></span>
        <div>
          <p class="route-overline">DAY {{ String(route.day).padStart(2, '0') }} · 主题路线</p>
          <h2>{{ route.title }}</h2>
        </div>
      </div>
      <button class="more-button" type="button" aria-label="更多路线操作">•••</button>
    </div>

    <p class="route-description">{{ route.summary }}</p>
    <div class="route-stat-row">
      <span><b>{{ route.spots.length }}</b> 个地点</span>
      <i></i>
      <span><b>{{ route.totalDistance }}</b> 路程</span>
      <i></i>
      <span><b>{{ route.totalVisitDuration }}</b> 游玩</span>
    </div>

    <div class="optimization-note">
      <span class="note-shield">✓</span>
      <span>已按区域聚类并完成 <b>2-opt 路径优化</b></span>
      <span class="verified">无回头路</span>
    </div>

    <div class="spot-list" aria-label="当日景点顺序，支持拖拽调整">
      <article
        v-for="(spot, index) in route.spots"
        :key="spot.id"
        class="spot-entry"
        :class="{ selected: selectedSpotId === spot.id, dragging: draggingIndex === index }"
        draggable="true"
        @dragstart="dragStart(index, $event)"
        @dragend="endDrag"
        @dragover.prevent
        @drop.prevent="dropAt(index)"
        @click="emit('select', spot)"
      >
        <div class="spot-time">
          <span>{{ spot.arrivalTime }}</span>
          <span class="time-rail"><i :style="{ backgroundColor: route.color }">{{ index + 1 }}</i></span>
          <span>{{ spot.leaveTime }}</span>
        </div>
        <div class="spot-card">
          <div class="drag-handle" title="拖动调整顺序"><span></span><span></span><span></span></div>
          <div class="spot-card-content">
            <div class="spot-card-title">
              <h3>{{ spot.name }}</h3>
              <button class="focus-button" type="button" title="在地图中定位" @click.stop="emit('select', spot)">⌖</button>
            </div>
            <div class="spot-meta"><span>{{ spot.type }}</span><i></i><span>游览约 {{ spot.estimatedDuration }} 分钟</span></div>
            <p>{{ spot.tips }}</p>
          </div>
        </div>
        <div v-if="index < route.spots.length - 1" class="segment-info">
          <span class="segment-line"></span>
          <span class="segment-icon">⌁</span>
          <span>{{ spot.nextDistance || '—' }}</span>
          <i>·</i>
          <span>{{ spot.nextDuration || '缓冲 15 分钟' }}</span>
        </div>
      </article>
    </div>

    <div class="day-notices">
      <div class="notice-title"><span>✦</span> 今日提醒</div>
      <ul><li v-for="notice in route.notices" :key="notice">{{ notice }}</li></ul>
    </div>
  </section>
  <section v-else class="itinerary-empty">请选择日期查看行程</section>
</template>
