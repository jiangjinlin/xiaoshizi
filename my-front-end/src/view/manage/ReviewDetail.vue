<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="$router.push('/manage/review-stats')" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">审查详情</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <router-link to="/manage/review-stats" class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition">返回统计</router-link>
        </div>
      </div>
    </nav>

    <div class="max-w-7xl mx-auto pt-24 pb-16 px-4">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-base font-semibold text-gray-800">题目信息</h2>
          <div v-if="loadingQ" class="text-gray-500 text-sm mt-3">加载中...</div>
          <div v-else class="mt-3 text-sm text-gray-700 space-y-1">
            <div><span class="text-gray-500">ID：</span>{{ question.id }}</div>
            <div><span class="text-gray-500">题型：</span>{{ question.type }}</div>
            <div><span class="text-gray-500">题干：</span><span class="whitespace-pre-wrap">{{ question.content }}</span></div>
            <div><span class="text-gray-500">当前答案：</span>{{ question.answer || '（暂无）' }}</div>
            <div><span class="text-gray-500">考纲：</span>{{ question.knowledge_points || '（暂无）' }}</div>
            <div><span class="text-gray-500">一级：</span>{{ question.primary_knowledge || '（暂无）' }}</div>
            <div>
              <div class="text-gray-500">解析：</div>
              <div class="whitespace-pre-wrap">{{ question.analysis || '（暂无）' }}</div>
            </div>
          </div>
        </div>

        <div class="p-6">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-gray-800">审查记录</h3>
            <button class="h-8 px-3 rounded bg-white border border-gray-300 text-xs hover:bg-gray-50" @click="load">刷新</button>
          </div>
          <div v-if="loading" class="text-center text-gray-500 py-8">加载中...</div>
          <div v-else>
            <div v-if="!reviews.length" class="text-center text-gray-400 py-8">暂无审查记录</div>
            <div v-else class="divide-y divide-gray-100">
              <div v-for="r in reviews" :key="r.user_id + '_' + r.updated_at" class="py-3 text-sm">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="px-2 py-0.5 rounded bg-gray-100 text-gray-700">{{ r.username }}</span>
                  <span class="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700">答：{{ r.suggested_answer || '（空）' }}</span>
                  <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-700">考纲：{{ r.suggested_kp || '（空）' }}</span>
                  <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-700">一级：{{ r.suggested_primary || '（空）' }}</span>
                  <span v-if="r.answer_wrong" class="px-2 py-0.5 rounded bg-rose-100 text-rose-700">原答有误</span>
                  <span class="text-xs text-gray-500">更新于 {{ r.updated_at }}</span>
                </div>
                <div v-if="r.analysis" class="mt-2 text-gray-700 whitespace-pre-wrap">{{ r.analysis }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiManageReviewDetail } from '../../api/index'
import AppLogo from '../../components/AppLogo.vue'

const route = useRoute()
const qid = ref(route.params.id)
const loading = ref(false)
const loadingQ = ref(false)
const question = ref({})
const reviews = ref([])

async function load(){
  loading.value = true
  try{
    const { data } = await apiManageReviewDetail(qid.value)
    if (data?.success){
      question.value = data.question || {}
      reviews.value = data.reviews || []
    } else {
      question.value = {}
      reviews.value = []
    }
  } finally {
    loading.value = false
    loadingQ.value = false
  }
}

loadingQ.value = true
load()
</script>
<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
/* use global .text-primary from tokens.css */
</style>
