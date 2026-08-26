<script setup lang="ts">
import { Capacitor } from '@capacitor/core'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { DayRoute, PlanResponse, RouteSpot, TransportMode } from '../types'

interface AmapWindow extends Window {
  AMap?: any
  _AMapSecurityConfig?: { securityJsCode?: string }
}

const props = defineProps<{
  plan?: PlanResponse
  route?: DayRoute
  selectedSpot?: RouteSpot
  transportMode: TransportMode
}>()
const emit = defineEmits<{ select: [spot: RouteSpot] }>()

const mapElement = ref<HTMLDivElement>()
const nativeMapElement = ref<HTMLDivElement>()
const amapReady = ref(false)
const nativeAmapReady = ref(false)
const nativeConsentPending = ref(false)
const showAllDays = ref(false)
const showDetails = ref(false)
let map: any
let nativeMap: any
let infoWindow: any
let loadPromise: Promise<boolean> | undefined
let renderToken = 0

const isNativeAndroid = Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android'

const visibleRoutes = computed(() => {
  if (!props.plan) return []
  return showAllDays.value ? props.plan.routes : (props.route ? [props.route] : [])
})

const visibleSpots = computed(() => visibleRoutes.value.flatMap((route) => route.spots))

const bounds = computed(() => {
  const spots = visibleSpots.value
  if (!spots.length) return { minLng: 120.09, maxLng: 120.17, minLat: 30.18, maxLat: 30.32 }
  const lngs = spots.map((spot) => spot.location.lng)
  const lats = spots.map((spot) => spot.location.lat)
  const padLng = Math.max((Math.max(...lngs) - Math.min(...lngs)) * 0.22, 0.008)
  const padLat = Math.max((Math.max(...lats) - Math.min(...lats)) * 0.22, 0.006)
  return {
    minLng: Math.min(...lngs) - padLng,
    maxLng: Math.max(...lngs) + padLng,
    minLat: Math.min(...lats) - padLat,
    maxLat: Math.max(...lats) + padLat,
  }
})

function mapPoint(spot: RouteSpot) {
  const box = bounds.value
  const x = 7 + ((spot.location.lng - box.minLng) / (box.maxLng - box.minLng)) * 86
  const y = 7 + ((box.maxLat - spot.location.lat) / (box.maxLat - box.minLat)) * 77
  return { x, y }
}

function svgPath(route: DayRoute) {
  return route.spots.map((spot, index) => {
    const point = mapPoint(spot)
    return `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`
  }).join(' ')
}

function segmentPosition(first: RouteSpot, second: RouteSpot) {
  const a = mapPoint(first)
  const b = mapPoint(second)
  return { left: `${(a.x + b.x) / 2}%`, top: `${(a.y + b.y) / 2}%` }
}

function escapeHtml(value: string) {
  return value.replace(/[&<>'"]/g, (letter) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[letter] || letter)
}

function spotPopup(spot: RouteSpot) {
  return `<div class="amap-popup"><span>${escapeHtml(spot.type)}</span><h3>${escapeHtml(spot.name)}</h3><p>游览约 ${spot.estimatedDuration} 分钟 · ${escapeHtml(spot.arrivalTime)} 到达</p><small>${escapeHtml(spot.tips)}</small></div>`
}

function hasAcceptedNativePrivacy() {
  return window.localStorage.getItem('xingji-amap-privacy-v1') === 'accepted'
}

function setNativeTransparentSurface(enabled: boolean) {
  const targets = [document.documentElement, document.body]
  targets.forEach((target) => target.classList.toggle('native-amap-root', enabled))
}

async function initialiseNativeAmap(): Promise<boolean> {
  if (!isNativeAndroid || !nativeMapElement.value) return false
  if (!hasAcceptedNativePrivacy()) {
    nativeConsentPending.value = true
    return false
  }

  try {
    setNativeTransparentSurface(true)
    const { AMap, LogoPosition, MapType } = await import('@snewbie/capacitor-amap')
    // AMap Android SDK requires an explicit privacy disclosure/consent acknowledgement
    // before a MapView is constructed. The UI below records that acknowledgement.
    await AMap.updatePrivacyShow(true, true)
    await AMap.updatePrivacyAgree(true)
    nativeMap = await AMap.create({
      id: 'xingji-route-map',
      element: nativeMapElement.value,
      forceCreate: true,
      config: {
        logoPosition: LogoPosition.LOGO_POSITION_BOTTOM_LEFT,
        mapType: MapType.MAP_TYPE_NORMAL,
        scaleControlsEnabled: true,
        zoomControlsEnabled: true,
        compassEnabled: false,
        cameraOptions: {
          target: { latitude: 30.245, longitude: 120.145 },
          zoom: 13,
          tilt: 0,
          bearing: 0,
        },
      },
    })
    await nativeMap.setTrafficEnabled(props.transportMode === 'driving')
    nativeAmapReady.value = true
    nativeConsentPending.value = false
    return true
  } catch {
    // Keep the complete offline map preview available if a device lacks the SDK,
    // the key is not yet bound to this package/SHA1, or network tiles are unavailable.
    nativeAmapReady.value = false
    setNativeTransparentSurface(false)
    return false
  }
}

async function acceptNativePrivacy() {
  window.localStorage.setItem('xingji-amap-privacy-v1', 'accepted')
  nativeConsentPending.value = false
  await initialiseNativeAmap()
}

async function focusNativeSpot(spot: RouteSpot) {
  if (!nativeAmapReady.value || !nativeMap) return
  try {
    await nativeMap.cameraUpdatePosition({
      target: { latitude: spot.location.lat, longitude: spot.location.lng },
      zoom: 15,
      tilt: 0,
      bearing: 0,
    })
  } catch {
    // A map camera failure must never block selection in the route list.
  }
}

async function loadAmap(): Promise<boolean> {
  const apiKey = import.meta.env.VITE_AMAP_JS_KEY as string | undefined
  const securityCode = import.meta.env.VITE_AMAP_SECURITY_JS_CODE as string | undefined
  if (!apiKey) return false
  const amapWindow = window as AmapWindow
  if (amapWindow.AMap) return true
  if (loadPromise) return loadPromise

  if (securityCode) amapWindow._AMapSecurityConfig = { securityJsCode: securityCode }
  loadPromise = new Promise((resolve) => {
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(apiKey)}&plugin=AMap.Scale,AMap.ToolBar,AMap.ControlBar`
    script.async = true
    script.onload = () => resolve(Boolean((window as AmapWindow).AMap))
    script.onerror = () => resolve(false)
    document.head.appendChild(script)
  })
  return loadPromise
}

function openAmapInfo(spot: RouteSpot) {
  if (!map || !amapReady.value) return
  const AMap = (window as AmapWindow).AMap
  if (!AMap) return
  if (!infoWindow) infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -28), closeWhenClickMap: true })
  infoWindow.setContent(spotPopup(spot))
  infoWindow.open(map, [spot.location.lng, spot.location.lat])
}

function extractNavigationPath(result: any, mode: TransportMode): any[] {
  const route = result?.routes?.[0]
  if (!route) return []
  const pieces = mode === 'riding' ? route.rides : route.steps
  if (!Array.isArray(pieces)) return []
  return pieces.flatMap((step: any) => step.path || [])
}

/**
 * Replace the instant straight preview with AMap's road geometry as each leg returns.
 * We deliberately keep the colored preview until the callback succeeds: map/list
 * interactions never flash empty on a slow Directions response.
 */
function requestAmapRoadGeometry(AMap: any, route: DayRoute, token: number) {
  if (showAllDays.value || route.spots.length < 2) return
  const pluginByMode: Partial<Record<TransportMode, string>> = {
    driving: 'AMap.Driving',
    walking: 'AMap.Walking',
    riding: 'AMap.Riding',
  }
  const serviceByMode: Partial<Record<TransportMode, string>> = {
    driving: 'Driving',
    walking: 'Walking',
    riding: 'Riding',
  }
  const plugin = pluginByMode[props.transportMode]
  const serviceName = serviceByMode[props.transportMode]
  // Transfer output has multiple bus/walk segments. It remains a coloured overview
  // polyline here; a production route-detail drawer can render AMap.Transfer steps.
  if (!plugin || !serviceName) return

  AMap.plugin([plugin], () => {
    const Service = AMap[serviceName]
    if (!Service) return
    route.spots.slice(0, -1).forEach((spot, index) => {
      const next = route.spots[index + 1]
      const navigator = new Service({
        hideMarkers: true,
        autoFitView: false,
        policy: props.transportMode === 'driving' ? AMap.DrivingPolicy?.LEAST_TIME : undefined,
      })
      navigator.search(
        [spot.location.lng, spot.location.lat],
        [next.location.lng, next.location.lat],
        (status: string, result: any) => {
          if (status !== 'complete' || token !== renderToken || !map) return
          const path = extractNavigationPath(result, props.transportMode)
          if (path.length < 2) return
          map.add(new AMap.Polyline({
            path,
            strokeColor: route.color,
            strokeOpacity: 0.95,
            strokeWeight: 6,
            strokeStyle: 'solid',
            lineJoin: 'round',
            showDir: true,
            zIndex: 10,
          }))
        },
      )
    })
  })
}

function drawAmap() {
  if (!map || !amapReady.value) return
  const AMap = (window as AmapWindow).AMap
  if (!AMap) return
  const token = ++renderToken
  map.clearMap()

  for (const route of visibleRoutes.value) {
    const path = route.spots.map((spot) => [spot.location.lng, spot.location.lat])
    if (path.length > 1) {
      map.add(new AMap.Polyline({
        path,
        strokeColor: route.color,
        strokeOpacity: 0.88,
        strokeWeight: 6,
        strokeStyle: 'solid',
        lineJoin: 'round',
        showDir: true,
        zIndex: 8,
      }))
    }
    route.spots.forEach((spot, index) => {
      const selected = props.selectedSpot?.id === spot.id
      const marker = new AMap.Marker({
        position: [spot.location.lng, spot.location.lat],
        offset: new AMap.Pixel(-18, -18),
        zIndex: selected ? 30 : 15 + index,
        content: `<div class="amap-marker ${selected ? 'is-selected' : ''}" style="--pin-color:${route.color}"><b>${index + 1}</b></div>`,
        title: spot.name,
      })
      marker.on('click', () => {
        emit('select', spot)
        openAmapInfo(spot)
      })
      map.add(marker)
    })
  }

  if (!showAllDays.value && props.route) requestAmapRoadGeometry(AMap, props.route, token)
  if (visibleSpots.value.length) map.setFitView(null, false, [64, 64, 90, 64])
  if (props.selectedSpot) openAmapInfo(props.selectedSpot)
}

async function initialiseMap() {
  const nativeReady = await initialiseNativeAmap()
  if (nativeReady || (isNativeAndroid && nativeConsentPending.value)) return

  const canUseAmap = await loadAmap()
  if (!canUseAmap || !mapElement.value) return
  const AMap = (window as AmapWindow).AMap
  map = new AMap.Map(mapElement.value, {
    viewMode: '2D',
    zoom: 13,
    center: [120.145, 30.245],
    mapStyle: 'amap://styles/whitesmoke',
    resizeEnable: true,
  })
  map.addControl(new AMap.Scale({ position: { right: '16px', bottom: '112px' } }))
  map.addControl(new AMap.ToolBar({ position: { right: '16px', top: '96px' } }))
  amapReady.value = true
  await nextTick()
  drawAmap()
}

function selectFallbackSpot(spot: RouteSpot) {
  emit('select', spot)
  showDetails.value = true
}

watch([visibleRoutes, () => props.selectedSpot?.id], () => {
  if (amapReady.value) drawAmap()
  if (props.selectedSpot) void focusNativeSpot(props.selectedSpot)
}, { deep: true })

watch(showAllDays, () => {
  if (amapReady.value) drawAmap()
})

watch(() => props.transportMode, (mode) => {
  if (nativeAmapReady.value && nativeMap) void nativeMap.setTrafficEnabled(mode === 'driving')
})

onMounted(initialiseMap)
onBeforeUnmount(() => {
  map?.destroy?.()
  nativeMap?.destroy?.()
  map = undefined
  nativeMap = undefined
  setNativeTransparentSurface(false)
})
</script>

<template>
  <section class="map-canvas" :class="{ 'using-amap': amapReady, 'using-native-amap': nativeAmapReady }">
    <div ref="mapElement" class="amap-host" aria-label="高德地图路线"></div>
    <div ref="nativeMapElement" class="native-amap-host" aria-label="高德 Android 原生地图"></div>

    <div v-if="!amapReady" class="fallback-map" aria-label="路线地图预览">
      <div class="map-water water-one"></div>
      <div class="map-water water-two"></div>
      <div class="map-park park-one"></div>
      <div class="map-park park-two"></div>
      <div class="road road-a"></div><div class="road road-b"></div><div class="road road-c"></div><div class="road road-d"></div>
      <div class="district-label label-west">西湖风景区</div>
      <div class="district-label label-north">北山街</div>
      <div class="district-label label-east">湖滨商圈</div>
      <div class="district-label label-south">南山路</div>
      <svg class="route-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <marker id="route-arrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"></path></marker>
        </defs>
        <path
          v-for="route in visibleRoutes"
          :key="route.day"
          :d="svgPath(route)"
          fill="none"
          :stroke="route.color"
          stroke-width="0.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          marker-mid="url(#route-arrow)"
        />
      </svg>
      <template v-for="route in visibleRoutes" :key="`segments-${route.day}`">
        <span
          v-for="(spot, index) in route.spots.slice(0, -1)"
          :key="`${spot.id}-segment`"
          class="map-segment-label"
          :style="segmentPosition(spot, route.spots[index + 1])"
        >{{ spot.nextDuration?.replace('步行 ', '').replace('驾车 ', '') || '15 分钟' }}</span>
      </template>
      <template v-for="route in visibleRoutes" :key="`pins-${route.day}`">
        <button
          v-for="(spot, index) in route.spots"
          :key="spot.id"
          type="button"
          class="map-pin"
          :class="{ selected: selectedSpot?.id === spot.id }"
          :style="{ left: `${mapPoint(spot).x}%`, top: `${mapPoint(spot).y}%`, '--pin-color': route.color }"
          :aria-label="`查看${spot.name}`"
          @click="selectFallbackSpot(spot)"
        >
          <b>{{ index + 1 }}</b>
          <span>{{ spot.name }}</span>
        </button>
      </template>
    </div>

    <div class="map-overlay map-topbar">
      <div class="map-location"><span class="location-pulse">⌖</span><b>{{ plan?.destination || '目的地' }}</b><small>智能路线</small></div>
      <div class="map-filter">
        <button type="button" :class="{ active: !showAllDays }" @click="showAllDays = false">当天路线</button>
        <button type="button" :class="{ active: showAllDays }" @click="showAllDays = true">全部日期</button>
      </div>
    </div>

    <div class="map-overlay map-legend">
      <div v-for="item in visibleRoutes" :key="item.day"><i :style="{ background: item.color }"></i>Day {{ item.day }}</div>
      <span class="legend-divider"></span><span class="transport-legend">{{ ({ walking: '步行', riding: '骑行', driving: '自驾', transit: '公共交通' } as Record<string, string>)[transportMode] }}</span>
    </div>

    <button class="map-style-button" type="button" @click="showDetails = !showDetails"><span>⊕</span>{{ showDetails ? '收起详情' : '路线详情' }}</button>

    <aside v-if="selectedSpot && (showDetails || (!amapReady && !nativeAmapReady))" class="map-spot-card">
      <button type="button" aria-label="关闭详情" @click="showDetails = false">×</button>
      <span class="map-spot-type">{{ selectedSpot.type }}</span>
      <h3>{{ selectedSpot.name }}</h3>
      <p><b>{{ selectedSpot.arrivalTime }}</b> 到达 · 游览约 {{ selectedSpot.estimatedDuration }} 分钟</p>
      <p class="map-spot-tip">{{ selectedSpot.tips }}</p>
      <div><span>营业时间</span><b>{{ selectedSpot.openHours || '以现场为准' }}</b></div>
    </aside>

    <div v-if="nativeAmapReady" class="map-native-badge"><span>◆</span> 原生高德地图 <em>Android SDK</em></div>
    <div v-else-if="!amapReady" class="map-demo-badge"><span>⌁</span> 地图预览模式 <em>配置高德 Key 后切换为实时底图</em></div>

    <aside v-if="nativeConsentPending" class="native-privacy-card">
      <span class="native-privacy-icon">⌖</span>
      <div>
        <b>开启原生高德地图</b>
        <p>继续即表示你已阅读并同意高德开放平台隐私政策，用于加载地图底图与路线点位。</p>
      </div>
      <button type="button" @click="acceptNativePrivacy">同意并开启</button>
    </aside>
  </section>
</template>
