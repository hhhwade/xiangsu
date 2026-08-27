import type { DayRoute, PlanResponse, TravelForm } from '../types'

const baseRoutes: DayRoute[] = [
  {
    day: 1,
    title: '西湖经典环线',
    color: '#DE7444',
    summary: '从北山街进入西湖，把最经典的湖岸风景留给步行。',
    totalDistance: '6.8 km',
    totalVisitDuration: '5.3 h',
    totalTransportDuration: '1.1 h',
    notices: ['断桥 10:30 后游客明显增多，建议按此顺序出发', '沿白堤步行，请预留 15 分钟拍照缓冲'],
    spots: [
      { id: 'hz-01', name: '断桥残雪', type: '自然风光', location: { lng: 120.1500, lat: 30.2600 }, estimatedDuration: 45, priority: 1, arrivalTime: '09:00', leaveTime: '09:45', nextSpot: '白堤', nextDistance: '0.8 km', nextDuration: '步行 12 分钟', tips: '建议清晨前往，桥东侧光线更适合拍照。', openHours: '全天开放', imageHint: '湖岸' },
      { id: 'hz-02', name: '白堤', type: '自然风光', location: { lng: 120.1433, lat: 30.2509 }, estimatedDuration: 60, priority: 2, arrivalTime: '09:57', leaveTime: '10:57', nextSpot: '平湖秋月', nextDistance: '0.7 km', nextDuration: '步行 10 分钟', tips: '租一辆共享单车也很舒适，慢行优先。', openHours: '全天开放', imageHint: '堤岸' },
      { id: 'hz-03', name: '平湖秋月', type: '网红打卡', location: { lng: 120.1367, lat: 30.2482 }, estimatedDuration: 40, priority: 3, arrivalTime: '11:07', leaveTime: '11:47', nextSpot: '楼外楼', nextDistance: '0.6 km', nextDuration: '步行 8 分钟', tips: '11 点前后湖面风平，适合取景。', openHours: '全天开放', imageHint: '湖面' },
      { id: 'hz-04', name: '楼外楼', type: '美食探店', location: { lng: 120.1304, lat: 30.2382 }, estimatedDuration: 75, priority: 4, arrivalTime: '12:10', leaveTime: '13:25', nextSpot: '曲院风荷', nextDistance: '1.2 km', nextDuration: '步行 18 分钟', tips: '可提前取号，推荐西湖醋鱼与龙井虾仁。', openHours: '10:30–20:00', imageHint: '餐厅' },
      { id: 'hz-05', name: '曲院风荷', type: '自然风光', location: { lng: 120.1248, lat: 30.2316 }, estimatedDuration: 75, priority: 5, arrivalTime: '13:43', leaveTime: '14:58', nextSpot: '苏堤春晓', nextDistance: '1.5 km', nextDuration: '步行 22 分钟', tips: '夏季荷花盛放，雨后木栈道较滑。', openHours: '全天开放', imageHint: '荷塘' },
      { id: 'hz-06', name: '苏堤春晓', type: '自然风光', location: { lng: 120.1192, lat: 30.2216 }, estimatedDuration: 60, priority: 6, arrivalTime: '15:20', leaveTime: '16:20', tips: '傍晚光线柔和，可从南端结束当天行程。', openHours: '全天开放', imageHint: '落日' },
    ],
  },
  {
    day: 2,
    title: '灵隐禅意与茶香',
    color: '#5E9C93',
    summary: '西线集中游览，寺院、石窟与茶园连成一条安静的线。',
    totalDistance: '9.4 km',
    totalVisitDuration: '5.7 h',
    totalTransportDuration: '1.4 h',
    notices: ['灵隐寺需提前预约，法定假日建议 08:00 前抵达', '飞来峰石阶较多，老人可从东侧缓坡进入'],
    spots: [
      { id: 'hz-07', name: '灵隐寺', type: '宗教寺庙', location: { lng: 120.1013, lat: 30.2338 }, estimatedDuration: 90, priority: 1, arrivalTime: '08:45', leaveTime: '10:15', nextSpot: '飞来峰', nextDistance: '0.3 km', nextDuration: '步行 5 分钟', tips: '入寺着装宜得体，香花券可线上预订。', openHours: '07:30–18:15', imageHint: '寺庙' },
      { id: 'hz-08', name: '飞来峰', type: '历史人文', location: { lng: 120.1001, lat: 30.2303 }, estimatedDuration: 75, priority: 2, arrivalTime: '10:20', leaveTime: '11:35', nextSpot: '法喜寺', nextDistance: '3.8 km', nextDuration: '驾车 13 分钟', tips: '石窟光线偏暗，拍摄可开启夜景模式。', openHours: '07:30–17:30', imageHint: '石窟' },
      { id: 'hz-09', name: '法喜寺', type: '宗教寺庙', location: { lng: 120.0869, lat: 30.1992 }, estimatedDuration: 70, priority: 3, arrivalTime: '12:03', leaveTime: '13:13', nextSpot: '龙井村', nextDistance: '2.6 km', nextDuration: '驾车 10 分钟', tips: '可在寺外简餐，午后人流相对平稳。', openHours: '06:30–18:00', imageHint: '山门' },
      { id: 'hz-10', name: '龙井村', type: '户外运动', location: { lng: 120.0952, lat: 30.1882 }, estimatedDuration: 100, priority: 4, arrivalTime: '13:38', leaveTime: '15:18', nextSpot: '中国茶叶博物馆', nextDistance: '2.1 km', nextDuration: '驾车 8 分钟', tips: '如购茶请认准正规门店，山路会车需慢行。', openHours: '全天开放', imageHint: '茶园' },
      { id: 'hz-11', name: '中国茶叶博物馆', type: '博物馆', location: { lng: 120.1060, lat: 30.1941 }, estimatedDuration: 80, priority: 5, arrivalTime: '15:41', leaveTime: '17:01', tips: '周一部分展厅闭馆，出发前请确认预约时段。', openHours: '09:00–17:00', imageHint: '博物馆' },
    ],
  },
  {
    day: 3,
    title: '运河人文慢游',
    color: '#7A71B8',
    summary: '沿大运河从历史街区步行到艺术空间，适合留白的一天。',
    totalDistance: '5.6 km',
    totalVisitDuration: '5.1 h',
    totalTransportDuration: '0.8 h',
    notices: ['拱宸桥周边周末停车紧张，建议公共交通抵达', '博物馆周一闭馆；可将小河直街延长作为替代'],
    spots: [
      { id: 'hz-12', name: '拱宸桥', type: '历史人文', location: { lng: 120.1498, lat: 30.3133 }, estimatedDuration: 45, priority: 1, arrivalTime: '09:30', leaveTime: '10:15', nextSpot: '中国京杭大运河博物馆', nextDistance: '0.5 km', nextDuration: '步行 7 分钟', tips: '桥面晨光好，建议从西岸开始步行。', openHours: '全天开放', imageHint: '古桥' },
      { id: 'hz-13', name: '中国京杭大运河博物馆', type: '博物馆', location: { lng: 120.1509, lat: 30.3090 }, estimatedDuration: 100, priority: 2, arrivalTime: '10:22', leaveTime: '12:02', nextSpot: '小河直街', nextDistance: '1.3 km', nextDuration: '步行 19 分钟', tips: '建议预约讲解，午间可在馆外咖啡店休息。', openHours: '09:00–16:30', imageHint: '展馆' },
      { id: 'hz-14', name: '小河直街历史文化街区', type: '历史人文', location: { lng: 120.1446, lat: 30.3068 }, estimatedDuration: 75, priority: 3, arrivalTime: '12:35', leaveTime: '13:50', nextSpot: '桥西历史街区', nextDistance: '1.1 km', nextDuration: '步行 16 分钟', tips: '沿河小店适合简餐，避开正午排队。', openHours: '全天开放', imageHint: '街区' },
      { id: 'hz-15', name: '桥西历史街区', type: '网红打卡', location: { lng: 120.1434, lat: 30.3161 }, estimatedDuration: 80, priority: 4, arrivalTime: '14:06', leaveTime: '15:26', nextSpot: '香积寺', nextDistance: '1.7 km', nextDuration: '步行 24 分钟', tips: '老厂房与运河景观适合慢慢逛。', openHours: '全天开放', imageHint: '艺术街区' },
      { id: 'hz-16', name: '香积寺', type: '宗教寺庙', location: { lng: 120.1533, lat: 30.3208 }, estimatedDuration: 65, priority: 5, arrivalTime: '15:50', leaveTime: '16:55', tips: '17:00 前入内更从容，寺外有运河夜景。', openHours: '08:00–17:00', imageHint: '古寺' },
    ],
  },
]

function cloneRoutes(days: number): DayRoute[] {
  const count = Math.max(1, Math.min(days, baseRoutes.length))
  return baseRoutes.slice(0, count).map((route) => ({
    ...route,
    spots: route.spots.map((spot) => ({ ...spot, location: { ...spot.location } })),
    notices: [...route.notices],
  }))
}

export function demoPlan(form: TravelForm): PlanResponse {
  const requestedDays = form.durationUnit === 'days'
    ? Math.round(form.duration)
    : Math.max(1, Math.ceil(form.duration / form.dailyHours))
  const routes = cloneRoutes(requestedDays)
  const totalSpots = routes.reduce((sum, route) => sum + route.spots.length, 0)
  const totalKm = routes.reduce((sum, route) => sum + Number.parseFloat(route.totalDistance), 0)

  return {
    destination: form.destination || '杭州',
    totalDays: routes.length,
    routes,
    overallStats: {
      totalDistance: `${totalKm.toFixed(1)} km`,
      totalSpots,
      backtrackCheck: 'passed',
      totalDuration: `${(routes.length * form.dailyHours).toFixed(0)} h`,
    },
    generatedAt: new Date().toISOString(),
  }
}

export const defaultForm: TravelForm = {
  destination: '杭州',
  duration: 3,
  durationUnit: 'days',
  preferences: ['natural', 'culture', 'food', 'museum'],
  transportMode: 'driving',
  dailyHours: 8,
  budgetMin: undefined,
  budgetMax: undefined,
  adults: 2,
  children: 0,
  elderly: false,
  accessible: false,
  startDate: '',
  specialNeeds: '',
}

export const destinationSuggestions = [
  { name: '杭州', detail: '浙江 · 西湖、运河与茶山' },
  { name: '苏州', detail: '江苏 · 园林与平江路' },
  { name: '上海', detail: '上海 · 城市漫游与美术馆' },
  { name: '北京', detail: '北京 · 古都人文与博物馆' },
  { name: '成都', detail: '四川 · 美食与慢生活' },
]
