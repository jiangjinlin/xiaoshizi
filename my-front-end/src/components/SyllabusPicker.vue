<script setup>
import { onMounted } from 'vue'
import { useSyllabusStore } from '../stores/syllabus'

const s = useSyllabusStore()

onMounted(async ()=>{
  if (!s.provinces.length) await s.loadPresets()
})

function onProvinceChange(e){ s.setProvince(e.target.value) }
function onMajorChange(e){ s.setMajor(e.target.value) }
</script>

<template>
  <div class="flex items-center gap-2 text-xs">
    <label class="text-gray-500">考纲</label>
    <select :value="s.province" @change="onProvinceChange" class="h-8 px-2 rounded border border-gray-300 bg-white/70">
      <option value="">全部省份</option>
      <option v-for="p in s.provinces" :key="p" :value="p">{{ p }}</option>
    </select>
    <select :value="s.major" @change="onMajorChange" class="h-8 px-2 rounded border border-gray-300 bg-white/70" :disabled="!s.province">
      <option value="">全部专业</option>
      <option v-for="m in s.getMajors" :key="m" :value="m">{{ m }}</option>
    </select>
  </div>
</template>

<style scoped>
</style>

