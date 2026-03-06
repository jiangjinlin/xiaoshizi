<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/70 backdrop-blur border-b border-gray-200 px-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <AppLogo :height="34" class="cursor-pointer" @click="goBack" />
        <span class="hidden sm:inline text-lg font-semibold text-gray-700">专项练习统计</span>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <button class="px-4 h-10 rounded-lg bg-white/70 border border-gray-200 text-gray-600 hover:bg-white" @click="goBack">返回</button>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto pt-24 pb-20 px-4">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-8 shadow-sm">
        <h2 class="text-base font-semibold text-gray-800 mb-6">题型正确率</h2>
        <div v-if="loading" class="text-sm text-gray-500">加载中...</div>
        <div v-else class="grid sm:grid-cols-3 gap-5">
          <div v-for="(v,k) in stats.types" :key="k" class="rounded-xl border border-gray-200 bg-white/80 p-5 flex flex-col items-start gap-2">
            <span class="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">{{ k }}</span>
            <div class="text-2xl font-bold text-gray-800">{{ v.accuracy==null?'-':v.accuracy+'%' }}</div>
            <p class="text-[11px] text-gray-500">练习次数：{{ v.attempts||0 }}</p>
          </div>
        </div>
        <div class="mt-8 text-sm text-gray-600 flex items-center gap-4 flex-wrap">
          <span>当前错题数：<b class="text-primary">{{ stats.wrong_count }}</b></span>
          <button class="h-9 px-4 rounded-lg bg-primary text-white text-xs font-medium hover:bg-primary/90" @click="goMistakes">查看错题</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiPracticeStats } from '../api/index'
import AppLogo from '../components/AppLogo.vue'
const router = useRouter()
const loading = ref(false)
const stats = ref({ types:{}, wrong_count:0 })
async function load(){
  loading.value=true
  try{ const { data } = await apiPracticeStats(); if(data?.success) stats.value=data }catch{} finally{ loading.value=false }
}
function goBack(){ router.push('/student') }
function goMistakes(){ router.push('/practice/mistakes') }
onMounted(load)
</script>
<style scoped>
/* use global .text-primary from tokens.css */
</style>
