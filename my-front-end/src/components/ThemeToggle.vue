<script setup>
import { computed } from 'vue'
import { useUiStore } from '../stores/ui'
const ui = useUiStore()
const isDark = computed(()=> ui.theme==='dark')
function toggle(){ ui.toggleTheme() }
</script>
<template>
  <button @click="toggle" class="btn-secondary h-10 px-3 text-xs flex items-center gap-1">
    <i :class="isDark ? 'fas fa-sun' : 'fas fa-moon'" class="text-primary"></i>
    <span>{{ isDark ? '亮色' : '夜间' }}</span>
  </button>
</template>
<style scoped>
</style>
