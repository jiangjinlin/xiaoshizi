<script setup>
import { ref, onMounted, computed } from 'vue'
import { getLanConfig } from '../api/http'

const props = defineProps({
  height: { type: [Number, String], default: 36 },
  alt: { type: String, default: '站点LOGO' }
})

const logoUrl = ref('/static/logo.png')
onMounted(() => {
  try {
    const base = (getLanConfig().baseURL || '').replace(/\/$/, '')
    // 使用绝对路径解析，确保路径始终相对于 origin，不叠加 baseURL 中可能存在的路径
    logoUrl.value = base ? new URL('/static/logo.png', base).href : '/static/logo.png'
  } catch {
    logoUrl.value = '/static/logo.png'
  }
})

const resolvedHeight = computed(() => {
  const h = props.height
  return typeof h === 'number' ? `${h}px` : h
})
</script>

<template>
  <img :src="logoUrl" :alt="alt" :style="{ height: resolvedHeight, width: 'auto' }" class="select-none" />
</template>
