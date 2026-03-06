<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiManageExamList, apiManageExamSignins } from '../../api/index'

const router = useRouter()
const manageExams = ref([])
const selectedExamId = ref('')
const classFilter = ref('')
const signCounts = ref({ signed_in:0, failed:0, not_signed:0, total:0 })
const signins = ref([])
const signLoading = ref(false)
const successFilter = ref('') // '' | 'success' | 'failed'
const page = ref(1)
const pageSize = ref(20)

function toBeijing(s){ if(!s) return '-'; try{ const d=new Date(String(s).replace(' ','T')); return new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(d)}catch{return s}}

async function loadManageExams() {
  try {
    const { data } = await apiManageExamList()
    if (data?.success) {
      manageExams.value = data.exams || []
      if (!selectedExamId.value && manageExams.value.length) {
        selectedExamId.value = String(manageExams.value[0].id)
      }
    }
  } catch {}
}

async function fetchSignins() {
  if (!selectedExamId.value) return
  signLoading.value = true
  try {
    const params = { exam_id: selectedExamId.value, classroom: classFilter.value || undefined, page: page.value, page_size: pageSize.value }
    if (successFilter.value==='success') params.success = true
    else if (successFilter.value==='failed') params.success = false
    const { data } = await apiManageExamSignins(params)
    if (data?.success) {
      signins.value = (data.signins || []).map(r=>({...r, created_at: toBeijing(r.created_at)}))
      signCounts.value = data.counts || { signed_in:0, failed:0, not_signed:0, total:0 }
    } else {
      signins.value = []
      signCounts.value = { signed_in:0, failed:0, not_signed:0, total:0 }
    }
  } catch {
    signins.value = []
    signCounts.value = { signed_in:0, failed:0, not_signed:0, total:0 }
  } finally { signLoading.value = false }
}

onMounted(async () => {
  await loadManageExams()
  await fetchSignins()
})

function onSearch(){ page.value = 1; fetchSignins() }
function prevPage(){ if(page.value>1){ page.value--; fetchSignins() } }
function nextPage(){ if(page.value*pageSize.value < signCounts.value.total){ page.value++; fetchSignins() } }
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white">
    <div class="max-w-6xl mx-auto px-5 py-8">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-xl font-semibold text-gray-900">考试人脸识别签到情况</h1>
        <button class="h-9 px-3 rounded bg-white border border-gray-200 text-xs" @click="router.back()">返回</button>
      </div>

      <div class="rounded-2xl border border-gray-200 bg-white/80 p-5 mb-5">
        <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
          <div class="flex items-center gap-2 flex-wrap">
            <label class="text-sm text-gray-700">选择考试</label>
            <select v-model="selectedExamId" @change="onSearch" class="h-9 border border-gray-300 rounded px-3 text-sm bg-white">
              <option v-for="e in manageExams" :key="e.id" :value="String(e.id)">{{ e.title }}</option>
            </select>
            <label class="ml-1 text-sm text-gray-700">班级</label>
            <input v-model="classFilter" @keyup.enter="onSearch" placeholder="如 计科2301" class="h-9 border border-gray-300 rounded px-3 text-sm bg-white"/>
            <label class="ml-1 text-sm text-gray-700">结果</label>
            <select v-model="successFilter" class="h-9 border border-gray-300 rounded px-2 text-sm bg-white" @change="onSearch">
              <option value="">全部</option>
              <option value="success">成功</option>
              <option value="failed">失败/未签</option>
            </select>
            <button class="h-9 px-3 rounded bg-primary text-white text-xs" @click="onSearch">查询</button>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <span class="px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">已签到：{{ signCounts.signed_in }}</span>
            <span class="px-2 py-1 rounded-full bg-red-50 text-red-600 border border-red-200">失败：{{ signCounts.failed }}</span>
            <span class="px-2 py-1 rounded-full bg-gray-100 text-gray-600 border border-gray-200">未签到：{{ signCounts.not_signed }}</span>
            <span class="px-2 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">合计：{{ signCounts.total }}</span>
          </div>
        </div>
      </div>

      <div class="rounded-2xl border border-gray-200 bg-white/80 p-5 shadow-sm">
        <div class="overflow-x-auto">
          <table class="min-w-[880px] w-full text-xs">
            <thead>
              <tr class="bg-primary/5 text-gray-600 text-left">
                <th class="py-2.5 px-3 font-medium">用户名</th>
                <th class="py-2.5 px-3 font-medium">班级</th>
                <th class="py-2.5 px-3 font-medium">状态</th>
                <th class="py-2.5 px-3 font-medium">方式</th>
                <th class="py-2.5 px-3 font-medium">相似度</th>
                <th class="py-2.5 px-3 font-medium">失败原因</th>
                <th class="py-2.5 px-3 font-medium">时间</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 text-gray-700">
              <tr v-if="signLoading"><td colspan="7" class="py-8 text-center text-gray-400">加载中...</td></tr>
              <tr v-for="(row,idx) in signins" :key="idx" class="hover:bg-primary/5">
                <td class="py-2.5 px-3">{{ row.username }}</td>
                <td class="py-2.5 px-3">{{ row.classroom }}</td>
                <td class="py-2.5 px-3">
                  <span class="px-2 py-0.5 rounded-full text-xs font-medium"
                        :class="row.status==='signed_in' ? 'bg-emerald-100 text-emerald-700' : (row.status==='failed' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600')">
                    {{ row.status==='signed_in' ? '已签到' : (row.status==='failed' ? '失败' : '未签到') }}
                  </span>
                </td>
                <td class="py-2.5 px-3">{{ row.method || '-' }}</td>
                <td class="py-2.5 px-3">{{ typeof row.score==='number' ? row.score.toFixed(1) : '-' }}</td>
                <td class="py-2.5 px-3">{{ row.reason || '-' }}</td>
                <td class="py-2.5 px-3">{{ row.created_at || '-' }}</td>
              </tr>
              <tr v-if="!signLoading && !signins.length"><td colspan="7" class="py-8 text-center text-gray-400">暂无数据</td></tr>
            </tbody>
          </table>
        </div>
        <div class="mt-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3 text-xs">
          <div class="flex items-center gap-2">页大小
            <select v-model.number="pageSize" @change="onSearch" class="border rounded px-2 py-1">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
            <span>第 {{ page }} 页 / 共 {{ Math.ceil((signCounts.total||0)/pageSize) || 1 }} 页</span>
          </div>
          <div class="flex items-center gap-2">
            <button class="px-3 py-1 border rounded" :disabled="page===1 || signLoading" @click="prevPage">上一页</button>
            <button class="px-3 py-1 border rounded" :disabled="page*pageSize>=signCounts.total || signLoading" @click="nextPage">下一页</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.text-primary{ color:#2563eb }
</style>
