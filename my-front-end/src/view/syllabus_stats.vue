<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/70 backdrop-blur border-b border-gray-200 px-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <AppLogo :height="34" class="cursor-pointer" @click="goBack" />
        <span class="hidden sm:inline text-lg font-semibold text-gray-700">知识点掌握度统计</span>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <button class="px-4 h-10 rounded-lg bg-white/70 border border-gray-200 text-gray-600 hover:bg-white" @click="goBack">返回</button>
      </div>
    </nav>

    <div class="max-w-5xl mx-auto pt-24 pb-20 px-4">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-8 shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
          <h2 class="text-base font-semibold text-gray-800">知识点列表（按准确率升序）</h2>
          <div class="flex gap-2 text-xs items-center">
            <div class="flex rounded-lg overflow-hidden border border-gray-300">
              <button @click="setLevel('knowledge')" :class="['px-3 h-9 font-medium', level==='knowledge'?'bg-indigo-600 text-white':'bg-white text-gray-600 hover:bg-gray-50']">考纲</button>
              <button @click="setLevel('primary')" :class="['px-3 h-9 font-medium border-l border-gray-300', level==='primary'?'bg-indigo-600 text-white':'bg-white text-gray-600 hover:bg-gray-50']">一级</button>
            </div>
            <button class="h-9 px-4 rounded-lg bg-primary text-white font-medium hover:bg-primary/90" @click="reload" :disabled="loading">刷新</button>
            <button class="h-9 px-4 rounded-lg bg-white/70 border border-gray-300 text-gray-600 font-medium hover:bg-white" @click="goWeakPractice" :disabled="!stats.length">补弱练习</button>
          </div>
        </div>
        <div v-if="loading" class="text-sm text-gray-500">加载中...</div>
        <div v-else-if="!stats.length" class="text-sm text-gray-500">暂无数据，请先进行一定量练习。</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-xs text-left">
            <thead>
              <tr class="text-gray-600 bg-gray-50/60">
                <th class="px-3 py-2 font-medium">#</th>
                <th class="px-3 py-2 font-medium">知识点</th>
                <th class="px-3 py-2 font-medium">练习次数</th>
                <th class="px-3 py-2 font-medium">正确次数</th>
                <th class="px-3 py-2 font-medium">正确率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(k,i) in stats" :key="k.name" class="border-b border-gray-100 hover:bg-white/70">
                <td class="px-3 py-2 text-gray-400">{{ i+1 }}</td>
                <td class="px-3 py-2 text-gray-800">{{ k.name }}</td>
                <td class="px-3 py-2 text-gray-700">{{ k.total_attempts }}</td>
                <td class="px-3 py-2 text-gray-700">{{ k.correct_attempts }}</td>
                <td class="px-3 py-2">
                  <span v-if="k.accuracy!=null" :class="k.accuracy<60?'text-red-600':(k.accuracy<85?'text-amber-600':'text-green-600')" class="font-medium">{{ k.accuracy }}%</span>
                  <span v-else class="text-gray-400">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="stats.length" class="mt-6 text-[11px] text-gray-500">提示：补弱练习将优先抽取低准确率知识点题目。</div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiSyllabusStats } from '../api/index'
import AppLogo from '../components/AppLogo.vue'
const router = useRouter()
const loading = ref(false)
const stats = ref([])
const level = ref('knowledge')
async function load(){ loading.value=true; try{ const { data } = await apiSyllabusStats({ level: level.value }); if(data?.success) stats.value=data.kp_stats||[] }catch{ stats.value=[] } finally{ loading.value=false } }
function setLevel(l){ if(level.value!==l){ level.value=l; load() } }
function reload(){ load() }
function goBack(){ router.push('/syllabus/setup') }
function goWeakPractice(){ if(!stats.value.length) return; router.push({ path:'/syllabus/setup', query:{ mode:'weak', level: level.value } }) }
onMounted(load)
</script>
<style scoped>
/* use global .text-primary from tokens.css */
</style>
