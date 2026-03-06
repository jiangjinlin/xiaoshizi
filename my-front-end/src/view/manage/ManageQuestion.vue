<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiManageQuestionList, apiManageQuestionDelete } from '../../api/index'

const router = useRouter()
const loading = ref(false)
const errorMsg = ref('')
const questions = ref([])
const questionCount = ref(0)
const typeCounts = ref({})
const pendingCount = ref(0)
const unreviewedOnly = ref(false)

async function fetchList() {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = {}
    if (unreviewedOnly.value) params.reviewed = 0
    const { data } = await apiManageQuestionList(params)
    if (data?.success) {
      questions.value = data.questions || []
      questionCount.value = data.question_count || 0
      typeCounts.value = data.type_counts || {}
      pendingCount.value = data.pending_count || 0
    } else {
      errorMsg.value = data?.error_msg || '加载失败'
    }
  } catch { errorMsg.value = '网络错误' } finally { loading.value = false }
}

function addQuestion() { router.push('/manage/questions/new') }
function editQuestion(id) { router.push(`/manage/questions/edit/${id}`) }
async function deleteQuestion(id) {
  if (!confirm('确定要删除该题目吗？')) return
  try { const { data } = await apiManageQuestionDelete(id); if (data?.success) fetchList(); else alert(data?.error_msg || '删除失败') } catch { alert('网络错误，删除失败') }
}
function goAdvanced(){ router.push('/manage/questions/advanced') }
function backExams(){ router.push('/manage/exams') }

watch(unreviewedOnly, fetchList)
onMounted(fetchList)
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
      <h1 class="text-2xl font-bold">题目列表（简洁）</h1>
      <div class="flex gap-3 flex-wrap items-center">
        <span class="text-xs text-amber-600 bg-amber-50 border border-amber-200 px-2 py-1 rounded" title="未审核题数">未审：{{ pendingCount }}</span>
        <label class="text-sm flex items-center gap-2 border px-3 py-2 rounded bg-white">
          <input type="checkbox" v-model="unreviewedOnly" /> 只看未审核
        </label>
        <button class="bg-blue-600 text-white px-4 py-2 rounded" @click="addQuestion"><i class="fas fa-plus mr-1"></i>新增题目</button>
        <button class="bg-indigo-600 text-white px-4 py-2 rounded" @click="goAdvanced"><i class="fas fa-filter mr-1"></i>高级筛选与导入导出</button>
        <button class="bg-gray-600 text-white px-4 py-2 rounded" @click="backExams">返回考试</button>
      </div>
    </div>

    <div class="bg-white rounded shadow p-4 mb-6 flex flex-wrap items-center gap-4">
      <div>题目总量：<span class="text-blue-600 font-semibold text-lg">{{ questionCount }}</span></div>
      <div class="text-xs text-gray-500 flex flex-wrap gap-3">
        <span v-for="(v,k) in typeCounts" :key="k">{{ k }}：{{ v }}</span>
      </div>
    </div>

    <div v-if="errorMsg" class="text-red-600 mb-4">{{ errorMsg }}</div>

    <div class="overflow-x-auto bg-white rounded shadow">
      <table class="min-w-[900px] w-full text-sm">
        <thead>
          <tr class="bg-blue-50 text-blue-700 text-left">
            <th class="py-3 px-4">题目ID</th>
            <th class="py-3 px-4">题型</th>
            <th class="py-3 px-4">内容</th>
            <th class="py-3 px-4">分数</th>
            <th class="py-3 px-4">批次</th>
            <th class="py-3 px-4">审核</th>
            <th class="py-3 px-4 text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="q in questions" :key="q.id" class="border-t hover:bg-gray-50">
            <td class="py-3 px-4">{{ q.id }}</td>
            <td class="py-3 px-4">{{ q.question_type }}</td>
            <td class="py-3 px-4" :title="q.content">{{ (q.content||'').slice(0,60) }}{{ (q.content||'').length>60?'…':'' }}</td>
            <td class="py-3 px-4">{{ q.score }}</td>
            <td class="py-3 px-4">{{ q.batch }}</td>
            <td class="py-3 px-4">
              <span v-if="q.reviewed" class="text-xs px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">已审核</span>
              <span v-else class="text-xs px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200">未审核</span>
            </td>
            <td class="py-3 px-4">
              <div class="flex justify-center gap-2">
                <button class="text-blue-600" @click="editQuestion(q.id)">编辑</button>
                <button class="text-red-600" @click="deleteQuestion(q.id)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="!questions.length && !loading"><td colspan="7" class="py-6 text-center text-gray-400">暂无题目数据</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
</style>
