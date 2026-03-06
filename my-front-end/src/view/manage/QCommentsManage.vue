<template>
  <div class="p-6">
    <h1 class="text-lg font-semibold text-gray-800 mb-4">评论管理</h1>
    <div class="flex flex-wrap items-end gap-3 mb-4">
      <div>
        <label class="block text-xs text-gray-500 mb-1">题目ID</label>
        <input v-model="filters.question_id" type="text" class="h-9 px-3 rounded border border-gray-300" placeholder="可选" />
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">用户ID</label>
        <input v-model="filters.user_id" type="text" class="h-9 px-3 rounded border border-gray-300" placeholder="可选" />
      </div>
      <div class="flex-1 min-w-[200px]">
        <label class="block text-xs text-gray-500 mb-1">关键词</label>
        <input v-model="filters.keyword" type="text" class="h-9 w-full px-3 rounded border border-gray-300" placeholder="内容包含..." />
      </div>
      <button @click="loadList" class="h-9 px-4 rounded bg-primary text-white text-sm">查询</button>
      <button @click="reset" class="h-9 px-4 rounded border text-sm">重置</button>
    </div>
    <div class="bg-white/70 border rounded">
      <div v-if="loading" class="p-6 text-sm text-gray-500">加载中...</div>
      <div v-else>
        <div v-if="!items.length" class="p-6 text-sm text-gray-400">暂无数据</div>
        <ul v-else class="divide-y">
          <li v-for="it in items" :key="it.id" class="p-4">
            <div class="flex items-center justify-between">
              <div class="text-xs text-gray-500">ID: {{ it.id }} · 用户: {{ it.username }} ({{ it.user_id }}) · 题目: {{ it.question_id }} · {{ it.created_at }}</div>
              <button @click="del(it)" class="text-xs text-red-500 hover:text-red-600">删除</button>
            </div>
            <div class="mt-2 text-sm whitespace-pre-wrap break-words">{{ it.content }}</div>
            <div class="mt-1 text-[11px] text-gray-500">题干摘要：{{ it.question_snippet }}</div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { apiManageQComments, apiManageQCommentDelete } from '../../api/index'

const loading = ref(false)
const items = ref([])
const filters = reactive({ question_id: '', user_id: '', keyword: '' })

async function loadList(){
  loading.value = true
  try{
    const params = {}
    if(filters.question_id) params.question_id = filters.question_id
    if(filters.user_id) params.user_id = filters.user_id
    if(filters.keyword) params.keyword = filters.keyword
    const { data } = await apiManageQComments(params)
    items.value = data?.items || []
  } finally {
    loading.value = false
  }
}
function reset(){ filters.question_id=''; filters.user_id=''; filters.keyword=''; loadList() }
async function del(it){ if(!confirm('确定删除该评论吗？')) return; try{ await apiManageQCommentDelete(it.id); await loadList() }catch(e){ alert('删除失败，请稍后再试') } }

onMounted(loadList)
</script>
<style scoped>
.bg-primary{ background:#2563eb }
</style>

