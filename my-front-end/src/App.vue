<script setup>
import { onMounted, watch } from 'vue'
import { useUiStore } from './stores/ui'
const ui = useUiStore()
// Apply initial theme
onMounted(()=>{
  if(!document.documentElement.dataset.theme){
    document.documentElement.dataset.theme = ui.theme
  }
})
watch(()=>ui.theme, t=>{ document.documentElement.dataset.theme = t })
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br">
    <router-view />
  </div>
</template>

<style scoped>
</style>
