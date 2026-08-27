<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { defaultForm, destinationSuggestions } from '../data/sample'
import { autocompleteDestination } from '../services/api'
import { preferenceOptions, transportOptions, type PreferenceKey, type TravelForm, type TransportMode } from '../types'

const props = defineProps<{ initial?: TravelForm; busy?: boolean }>()
const emit = defineEmits<{
  submit: [form: TravelForm]
  transportChange: [mode: TransportMode]
}>()

const form = reactive<TravelForm>({
  ...defaultForm,
  ...props.initial,
  preferences: [...(props.initial?.preferences || defaultForm.preferences)],
})
const showSuggestions = ref(false)
const showAdvanced = ref(false)

const filteredSuggestions = computed(() => {
  const keyword = form.destination.trim().toLowerCase()
  if (!keyword) return destinationSuggestions
  return destinationSuggestions.filter((item) => item.name.toLowerCase().includes(keyword))
})

function selectDestination(name: string) {
  form.destination = name
  showSuggestions.value = false
}

function hideSuggestions() {
  window.setTimeout(() => { showSuggestions.value = false }, 140)
}

function togglePreference(key: PreferenceKey) {
  form.preferences = form.preferences.includes(key)
    ? form.preferences.filter((item) => item !== key)
    : [...form.preferences, key]
}

function setTransport(mode: TransportMode) {
  form.transportMode = mode
  emit('transportChange', mode)
}

function submit() {
  emit('submit', {
    ...form,
    preferences: [...form.preferences],
    budgetMin: form.budgetMin || undefined,
    budgetMax: form.budgetMax || undefined,
    specialNeeds: form.specialNeeds.trim(),
  })
}
</script>

<template>
  <form class="trip-form" @submit.prevent="submit">
    <div class="form-section first-section">
      <div class="section-kicker"><span class="kicker-dot"></span>旅程设置</div>
      <label class="field-label" for="destination">目的地</label>
      <div class="destination-field">
        <span class="field-icon">⌖</span>
        <input
          id="destination"
          v-model="form.destination"
          autocomplete="off"
          placeholder="城市、景区或区域"
          @focus="showSuggestions = true"
          @blur="hideSuggestions"
        />
        <button v-if="form.destination" class="clear-input" type="button" aria-label="清空目的地" @mousedown.prevent="form.destination = ''">×</button>
        <div v-if="showSuggestions && filteredSuggestions.length" class="suggestion-menu">
          <button v-for="item in filteredSuggestions" :key="item.name" type="button" @mousedown.prevent="selectDestination(item.name)">
            <span class="suggestion-pin">⌖</span>
            <span><b>{{ item.name }}</b><small>{{ item.detail }}</small></span>
          </button>
        </div>
      </div>

      <div class="two-field-row">
        <label>
          <span class="field-label">停留时间</span>
          <div class="mini-field duration-input">
            <input v-model.number="form.duration" type="number" min="1" max="30" />
            <select v-model="form.durationUnit" aria-label="时间单位">
              <option value="days">天</option>
              <option value="hours">小时</option>
            </select>
          </div>
        </label>
        <label>
          <span class="field-label">每日游玩</span>
          <div class="mini-field hours-field"><input v-model.number="form.dailyHours" type="number" min="2" max="16" /><span>小时</span></div>
        </label>
      </div>
    </div>

    <div class="form-section preference-section">
      <div class="field-label with-hint"><span>想怎么玩</span><em>可多选</em></div>
      <div class="preference-grid">
        <button
          v-for="item in preferenceOptions"
          :key="item.key"
          type="button"
          class="preference-chip"
          :class="{ selected: form.preferences.includes(item.key) }"
          @click="togglePreference(item.key)"
        >
          <span>{{ item.icon }}</span>{{ item.label }}
        </button>
      </div>
    </div>

    <div class="form-section transport-section">
      <div class="field-label">出行方式</div>
      <div class="transport-row">
        <button
          v-for="item in transportOptions"
          :key="item.value"
          type="button"
          :class="{ selected: form.transportMode === item.value }"
          @click="setTransport(item.value)"
        >
          <span class="transport-icon">{{ item.icon }}</span>{{ item.label }}
        </button>
      </div>
    </div>

    <button class="advanced-toggle" type="button" @click="showAdvanced = !showAdvanced">
      <span class="advanced-plus">{{ showAdvanced ? '−' : '+' }}</span>
      {{ showAdvanced ? '收起高级偏好' : '完善高级偏好' }}
      <span class="advanced-note">预算、同行人、时间</span>
    </button>

    <div v-if="showAdvanced" class="advanced-fields">
      <div class="two-field-row">
        <label><span class="field-label">预算 ¥</span><div class="mini-field"><input v-model.number="form.budgetMin" type="number" min="0" placeholder="最低" /></div></label>
        <label><span class="field-label">&nbsp;</span><div class="mini-field"><input v-model.number="form.budgetMax" type="number" min="0" placeholder="最高" /></div></label>
      </div>
      <div class="two-field-row compact-row">
        <label><span class="field-label">成人</span><div class="mini-field"><input v-model.number="form.adults" type="number" min="1" max="20" /></div></label>
        <label><span class="field-label">儿童</span><div class="mini-field"><input v-model.number="form.children" type="number" min="0" max="20" /></div></label>
      </div>
      <label class="date-field"><span class="field-label">出发日期与时间</span><input v-model="form.startDate" type="datetime-local" /></label>
      <div class="check-row">
        <label><input v-model="form.elderly" type="checkbox" /> 有老人同行</label>
        <label><input v-model="form.accessible" type="checkbox" /> 无障碍需求</label>
      </div>
      <label class="special-field"><span class="field-label">特殊需求</span><textarea v-model="form.specialNeeds" rows="2" placeholder="如：宠物友好、素食优先、避开人群…"></textarea></label>
    </div>

    <button class="generate-button" :disabled="busy || !form.destination.trim()" type="submit">
      <span v-if="busy" class="loading-orbit"></span>
      <span v-else class="spark">✦</span>
      {{ busy ? '正在编排最优路线…' : '生成智能路线' }}
      <span v-if="!busy" class="button-arrow">→</span>
    </button>
    <p class="form-footnote"><span>✓</span> 将自动校验营业时间、缓冲时间与回头路</p>
  </form>
</template>
