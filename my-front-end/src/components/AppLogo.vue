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
    logoUrl.value = base + '/static/logo.png'
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
