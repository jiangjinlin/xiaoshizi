<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-5xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="$router.push('/review')" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">审查贡献榜</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <router-link class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition" to="/review">返回审查</router-link>
        </div>
      </div>
    </nav>
    <div class="max-w-5xl mx-auto pt-24 pb-16 px-4">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-800">Top 50</h2>
        </div>
        <div class="p-6 overflow-x-auto">
          <table class="min-w-[720px] w-full text-sm">
            <thead>
              <tr class="text-xs text-gray-500">
                <th class="text-left py-2">排名</th>
                <th class="text-left py-2">用户名</th>
                <th class="text-left py-2">提交数</th>
                <th class="text-left py-2">共识命中</th>
                <th class="text-left py-2">积分</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r,idx) in rank" :key="r.user_id" class="border-t border-gray-100">
                <td class="py-2">{{ idx+1 }}</td>
                <td class="py-2">{{ r.username }}</td>
                <td class="py-2">{{ r.total }}</td>
                <td class="py-2">{{ r.consensus }}</td>
                <td class="py-2 font-semibold text-primary">{{ r.score }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!rank.length" class="text-center text-gray-400 py-8">暂无数据</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { apiReviewRank } from '../api/index'
import AppLogo from '../components/AppLogo.vue'
const rank = ref([])
async function load(){
  try{ const { data } = await apiReviewRank(); if (data?.success) rank.value = data.rank || [] }catch{}
}
onMounted(load)
</script>
<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
/* use global .text-primary from tokens.css */
</style>
