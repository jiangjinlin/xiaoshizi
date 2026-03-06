<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="$router.push('/admin')" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">审查统计</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <router-link to="/admin" class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition">返回后台</router-link>
        </div>
      </div>
    </nav>

    <div class="max-w-7xl mx-auto pt-24 pb-16 px-4">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-800">每题审查进度与分歧</h2>
          <div class="flex items-center gap-3 text-sm">
            <input v-model.trim="queryId" placeholder="按题目ID筛选（可空）" class="h-9 px-3 rounded border border-gray-300 bg-white/80 text-sm outline-none focus:ring-2 focus:ring-primary/30" />
            <button @click="load" class="h-9 px-4 rounded-lg bg-primary text-black text-xs font-medium shadow-sm hover:bg-primary/90 transition">刷新</button>
          </div>
        </div>
        <div class="p-6 overflow-x-auto">
          <table class="min-w-[900px] w-full text-sm">
            <thead>
              <tr class="text-xs text-gray-500">
                <th class="text-left py-2 w-20">题目ID</th>
                <th class="text-left py-2">题干</th>
                <th class="text-left py-2 w-24">题型</th>
                <th class="text-left py-2 w-28">总审查数</th>
                <th class="text-left py-2 w-[360px]">分组（意见/人数）</th>
                <th class="text-left py-2 w-28">状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.question_id" class="border-t border-gray-100 align-top">
                <td class="py-2">{{ item.question_id }}</td>
                <td class="py-2 whitespace-pre-wrap">{{ item.content }}</td>
                <td class="py-2">{{ item.type }}</td>
                <td class="py-2">{{ item.total_reviews }}</td>
                <td class="py-2">
                  <div class="flex flex-col gap-1">
                    <div v-for="g in item.groups" :key="g.suggested_answer + g.suggested_kp + g.suggested_primary + String(g.answer_wrong)" class="text-xs">
                      <span class="px-1.5 py-0.5 rounded bg-gray-100 text-gray-700">答：{{ g.suggested_answer || '（空）' }}</span>
                      <span class="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 ml-1">考纲：{{ g.suggested_kp || '（空）' }}</span>
                      <span class="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 ml-1">一级：{{ g.suggested_primary || '（空）' }}</span>
                      <span v-if="g.answer_wrong" class="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 ml-1">原答有误</span>
                      <span class="ml-2 text-gray-500">× {{ g.count }}</span>
                    </div>
                  </div>
                </td>
                <td class="py-2">
                  <div class="flex items-center gap-2">
                    <span v-if="item.consensus" class="text-green-700 bg-green-50 border border-green-200 text-xs px-2 py-1 rounded">已达共识</span>
                    <span v-else-if="item.conflict" class="text-amber-700 bg-amber-50 border border-amber-200 text-xs px-2 py-1 rounded">存在分歧</span>
                    <span v-else class="text-gray-600 bg-gray-50 border border-gray-200 text-xs px-2 py-1 rounded">进展中</span>
                    <router-link :to="'/manage/review-detail/'+item.question_id" class="ml-2 text-primary text-xs hover:underline">查看详情</router-link>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="!loading && !items.length" class="text-center text-gray-400 py-10">暂无数据</div>
          <div v-if="loading" class="text-center text-gray-400 py-10">加载中...</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { apiManageReviewStats } from '../../api/index'
import AppLogo from '../../components/AppLogo.vue'
const items = ref([])
const loading = ref(false)
const queryId = ref('')
async function load(){
  loading.value = true
  try{
    const params = {}
    if (queryId.value && String(queryId.value).trim()) params.question_id = String(queryId.value).trim()
    const { data } = await apiManageReviewStats(params)
    if (data?.success){ items.value = data.items || [] } else { items.value = [] }
  }catch{ items.value = [] }
  finally{ loading.value = false }
}
onMounted(load)
</script>
<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
/* use global .text-primary from tokens.css */
</style>
