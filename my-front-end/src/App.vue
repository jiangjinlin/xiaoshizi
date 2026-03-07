<script setup>
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore } from './stores/ui'
import { useUserStore } from './stores/user'
import { useSyllabusStore } from './stores/syllabus'

const ui = useUiStore()
const router = useRouter()
const userStore = useUserStore()
const syllabusStore = useSyllabusStore()

// Apply initial theme
onMounted(async ()=>{
  if(!document.documentElement.dataset.theme){
    document.documentElement.dataset.theme = ui.theme
  }
  try {
    const hasLocalLogin = !!localStorage.getItem('user_id')
    if (!hasLocalLogin) return
    await userStore.loadProfile(true)
    if (!userStore.userId) {
      localStorage.removeItem('user_id')
      localStorage.removeItem('role')
      userStore.clear()
      syllabusStore.clear()
      const path = router.currentRoute.value?.path || '/'
      if (path !== '/login' && path !== '/' && path !== '/register') {
        router.replace({ path: '/login', query: { redirect: router.currentRoute.value?.fullPath || path } })
      }
      return
    }
    if (userStore.role) localStorage.setItem('role', userStore.role)
    if (userStore.userId) localStorage.setItem('user_id', String(userStore.userId))
  } catch {}
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
