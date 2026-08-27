<script setup lang="ts">
import { computed } from 'vue'
import type { DayRoute, RouteSpot } from '../types'

const props = defineProps<{ route?: DayRoute; selectedSpotId?: string }>()
const emit = defineEmits<{ select: [spot: RouteSpot] }>()

function minutes(value: string) {
  const [hours, mins] = value.split(':').map(Number)
  return hours * 60 + mins
}

const range = computed(() => {
  if (!props.route?.spots.length) return { start: 540, end: 1020, span: 480 }
  const start = Math.min(...props.route.spots.map((spot) => minutes(spot.arrivalTime)))
  const end = Math.max(...props.route.spots.map((spot) => minutes(spot.leaveTime)))
  return { start, end, span: Math.max(1, end - start) }
})

const ticks = computed(() => {
  const startHour = Math.floor(range.value.start / 60)
  const endHour = Math.ceil(range.value.end / 60)
  return Array.from({ length: endHour - startHour + 1 }, (_, index) => `${String(startHour + index).padStart(2, '0')}:00`)
})

function placement(spot: RouteSpot) {
  const left = ((minutes(spot.arrivalTime) - range.value.start) / range.value.span) * 100
  const width = Math.max(8, ((minutes(spot.leaveTime) - minutes(spot.arrivalTime)) / range.value.span) * 100)
  return { left: `${left}%`, width: `${Math.min(width, 100 - left)}%` }
}
</script>

<template>
  <section v-if="route" class="timeline-strip">
    <div class="timeline-heading">
      <div><span class="mini-kicker">行程时间轴</span><b>{{ route.title }}</b></div>
      <span class="timeline-total">{{ route.totalVisitDuration }} 游玩 · {{ route.totalTransportDuration }} 路上</span>
    </div>
    <div class="timeline-scroll">
      <div class="timeline-inner">
        <div class="timeline-ticks">
          <span v-for="tick in ticks" :key="tick">{{ tick }}</span>
        </div>
        <div class="timeline-track">
          <div
            v-for="spot in route.spots"
            :key="spot.id"
            class="timeline-block"
            :class="{ selected: selectedSpotId === spot.id }"
            :style="[{ backgroundColor: route.color }, placement(spot)]"
            @click="emit('select', spot)"
          >
            <span class="block-order">{{ spot.priority }}</span>
            <b>{{ spot.name }}</b>
            <small>{{ spot.arrivalTime }}–{{ spot.leaveTime }}</small>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
