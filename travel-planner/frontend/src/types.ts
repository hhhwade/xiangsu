export type DurationUnit = 'days' | 'hours'
export type TransportMode = 'walking' | 'riding' | 'driving' | 'transit'

export type PreferenceKey =
  | 'natural'
  | 'culture'
  | 'food'
  | 'family'
  | 'shopping'
  | 'trending'
  | 'museum'
  | 'themePark'
  | 'outdoor'
  | 'temple'

export interface PreferenceOption {
  key: PreferenceKey
  label: string
  icon: string
}

export interface TravelForm {
  destination: string
  duration: number
  durationUnit: DurationUnit
  preferences: PreferenceKey[]
  transportMode: TransportMode
  dailyHours: number
  budgetMin?: number
  budgetMax?: number
  adults: number
  children: number
  elderly: boolean
  accessible: boolean
  startDate?: string
  specialNeeds: string
}

export interface Location {
  lng: number
  lat: number
}

export interface DestinationSuggestion {
  name: string
  district?: string | null
  location?: Location | null
}

export interface RouteSpot {
  id: string
  name: string
  type: string
  location: Location
  estimatedDuration: number
  priority: number
  arrivalTime: string
  leaveTime: string
  nextSpot?: string
  nextDistance?: string
  nextDuration?: string
  tips: string
  openHours?: string
  imageHint?: string
}

export interface DayRoute {
  day: number
  title: string
  color: string
  spots: RouteSpot[]
  totalDistance: string
  totalVisitDuration: string
  totalTransportDuration: string
  summary: string
  notices: string[]
}

export interface PlanResponse {
  destination: string
  totalDays: number
  routes: DayRoute[]
  overallStats: {
    totalDistance: string
    totalSpots: number
    backtrackCheck: 'passed' | 'warning'
    totalDuration?: string
  }
  generatedAt?: string
}

export const preferenceOptions: PreferenceOption[] = [
  { key: 'natural', label: '自然风光', icon: '◒' },
  { key: 'culture', label: '历史人文', icon: '⌘' },
  { key: 'food', label: '美食探店', icon: '✦' },
  { key: 'family', label: '亲子乐园', icon: '♧' },
  { key: 'shopping', label: '购物商圈', icon: '◇' },
  { key: 'trending', label: '网红打卡', icon: '◉' },
  { key: 'museum', label: '博物馆', icon: '▣' },
  { key: 'themePark', label: '主题乐园', icon: '☆' },
  { key: 'outdoor', label: '户外运动', icon: '↗' },
  { key: 'temple', label: '宗教寺庙', icon: '☼' },
]

export const transportOptions: Array<{ value: TransportMode; label: string; icon: string }> = [
  { value: 'walking', label: '步行', icon: '♧' },
  { value: 'riding', label: '骑行', icon: '⌁' },
  { value: 'driving', label: '自驾', icon: '⌁' },
  { value: 'transit', label: '公交', icon: '▤' },
]

export const transportLabels: Record<TransportMode, string> = {
  walking: '步行',
  riding: '骑行',
  driving: '自驾',
  transit: '公共交通',
}
