<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/70 backdrop-blur border-b border-gray-200 px-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <AppLogo :height="34" class="cursor-pointer" @click="goBack" />
        <span class="hidden sm:inline text-lg font-semibold text-gray-700">错题本</span>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <button class="px-4 h-10 rounded-lg bg-white/70 border border-gray-200 text-gray-600 hover:bg-white" @click="goBack">返回</button>
      </div>
    </nav>

    <div class="max-w-5xl mx-auto pt-24 pb-20 px-4">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-8 shadow-sm mb-6 flex flex-col gap-4">
        <div class="flex flex-wrap gap-3 items-center">
          <button class="h-10 px-4 rounded-lg bg-primary text-white text-xs font-medium hover:bg-primary/90" @click="refresh" :disabled="loading">刷新</button>
          <button class="h-10 px-4 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo/90 disabled:opacity-50" :disabled="!questions.length" @click="startWrongPractice">针对错题出题</button>
          <span class="text-xs text-gray-500">共 {{ questions.length }} 道错题（最近优先）</span>
        </div>
        <div v-if="loading" class="text-sm text-gray-500">加载中...</div>
        <div v-else-if="!questions.length" class="text-sm text-gray-500">暂无错题，继续保持。</div>
      </div>

      <div v-for="(q,idx) in questions" :key="q.id" class="mb-4 rounded-xl border border-gray-200 bg-white/80 p-5 shadow-sm">
        <div class="flex items-start gap-3">
          <div class="w-7 text-xs font-semibold text-gray-500 mt-0.5 select-none">{{ idx+1 }}</div>
          <div class="flex-1">
            <div class="mb-2 flex flex-wrap items-center gap-2">
              <span class="inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-full bg-primary/10 text-primary">{{ q.type }}</span>
              <span v-if="q.batch!=null" class="text-[10px] px-2 py-0.5 bg-gray-100 rounded text-gray-500">批次 {{ q.batch }}</span>
              <span v-if="q.score!=null" class="text-[10px] px-2 py-0.5 bg-amber-50 rounded text-amber-600">分值 {{ q.score }}</span>
              <span v-if="q.knowledge_points" class="text-[10px] px-2 py-0.5 rounded bg-indigo-50 text-indigo-600">考纲: {{ q.knowledge_points }}</span>
              <span v-if="q.primary_knowledge" class="text-[10px] px-2 py-0.5 rounded bg-amber-100 text-amber-700">一级: {{ q.primary_knowledge }}</span>
            </div>
            <div class="text-gray-800 text-sm leading-relaxed whitespace-pre-line break-words">{{ q.content }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiPracticeMistakes, apiPracticeQuestions } from '../api/index'
import AppLogo from '../components/AppLogo.vue'
const router = useRouter()
const loading = ref(false)
const questions = ref([])
async function load(){
  loading.value=true
  try{ const { data } = await apiPracticeMistakes(); if(data?.success) questions.value=data.questions||[] }catch{ questions.value=[] } finally{ loading.value=false }
}
function refresh(){ load() }
function goBack(){ router.push('/practice/setup') }
async function startWrongPractice(){
  if(!questions.value.length) return
  try {
    const { data } = await apiPracticeQuestions({ wrong_only:1, limit: questions.value.length })
    if(data?.success){
      const list = data.questions||[]
      if(!list.length) return
      sessionStorage.setItem('practice_questions', JSON.stringify(list))
      sessionStorage.setItem('practice_filters', JSON.stringify({ type:'', batch:'', limit:list.length, shuffle:false, from:'mistakes' }))
      router.push('/practice/do')
    }
  } catch {}
}
onMounted(load)
</script>
<style scoped>
/* use global .text-primary from tokens.css */
</style>
