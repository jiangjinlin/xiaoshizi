<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiManageExamList, apiManageExamDelete, apiManageExamPublish } from '../../api/index'

const router = useRouter()
const loading = ref(false)
const exams = ref([])
const questionCount = ref(0)
const errorMsg = ref('')

function toBeijing(iso) {
  if (!iso) return ''
  try {
    const d = new Date(iso.replace(' ', 'T'))
    const parts = new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).formatToParts(d)
    const m = Object.fromEntries(parts.map(p => [p.type, p.value]))
    return `${m.year}-${m.month}-${m.day} ${m.hour}:${m.minute}:${m.second}`
  } catch { return iso }
}

function safeParseDate(str){ if(!str) return null; const d=new Date(str.replace(' ','T')); return isNaN(d.getTime())?null:d }
function runtimeStatus(e){ const st=safeParseDate(e.start_time_raw); const et=safeParseDate(e.end_time_raw); if(!st||!et) return '未知'; const now=Date.now(); if(now<st.getTime()) return '计划中'; if(now>et.getTime()) return '已结束'; return '进行中' }

async function fetchList() {
  loading.value = true
  errorMsg.value = ''
  try {
    const { data } = await apiManageExamList()
    if (data?.success) {
      exams.value = (data.exams || []).map(e => ({
        ...e,
        start_time_raw: e.start_time,
        end_time_raw: e.end_time,
        start_time: toBeijing(e.start_time),
        end_time: toBeijing(e.end_time),
        runtime_status: runtimeStatus({start_time_raw:e.start_time,end_time_raw:e.end_time})
      }))
      questionCount.value = data.question_count || 0
    } else {
      errorMsg.value = data?.error_msg || '加载失败'
    }
  } catch (e) {
    errorMsg.value = '网络错误'
  } finally {
    loading.value = false
  }
}

function addExam() { router.push('/manage/exams/new') }
function editExam(id) { router.push(`/manage/exams/edit/${id}`) }
function gotoQuestions() { router.push('/manage/questions') }

async function removeExam(id) {
  if (!confirm('确定要删除该考试吗？')) return
  try {
    const { data } = await apiManageExamDelete(id)
    if (data?.success) fetchList()
    else alert(data?.error_msg || '删除失败')
  } catch { alert('网络错误，删除失败') }
}

async function togglePublish(id, current) {
  try {
    const { data } = await apiManageExamPublish(id, !current)
    if (data?.success) fetchList()
    else alert(data?.error_msg || '操作失败')
  } catch { alert('网络错误，操作失败') }
}

onMounted(fetchList)
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">考试与题库管理</h1>
      <div class="flex gap-3">
        <button class="bg-blue-600 text-white px-4 py-2 rounded" @click="addExam"><i class="fas fa-plus mr-1"></i>新建考试</button>
        <button class="bg-blue-600 text-white px-4 py-2 rounded" @click="gotoQuestions"><i class="fas fa-list mr-1"></i>题库管理</button>
        <router-link to="/teacher" class="bg-gray-600 text-white px-4 py-2 rounded">返回</router-link>
      </div>
    </div>

    <div class="mb-4 text-gray-700">题库总量：<span class="text-blue-600 text-xl font-semibold">{{ questionCount }}</span></div>

    <div v-if="errorMsg" class="mb-4 text-red-600">{{ errorMsg }}</div>

    <div class="overflow-x-auto bg-white rounded shadow">
      <table class="min-w-[800px] w-full text-sm">
        <thead>
          <tr class="bg-blue-50 text-blue-700 text-left">
            <th class="py-3 px-4">考试名称</th>
            <th class="py-3 px-4">开始时间</th>
            <th class="py-3 px-4">结束时间</th>
            <th class="py-3 px-4 text-center">参考人数</th>
            <th class="py-3 px-4 text-center">平均分</th>
            <th class="py-3 px-4 text-center">运行状态</th>
            <th class="py-3 px-4 text-center">发布</th>
            <th class="py-3 px-4 text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in exams" :key="e.id" class="border-t hover:bg-blue-50">
            <td class="py-3 px-4">{{ e.title }}</td>
            <td class="py-3 px-4">{{ e.start_time }}</td>
            <td class="py-3 px-4">{{ e.end_time }}</td>
            <td class="py-3 px-4 text-center">{{ e.count }}</td>
            <td class="py-3 px-4 text-center">{{ e.avg }}</td>
            <td class="py-3 px-4 text-center">
              <span :class="{
                'text-gray-500': e.runtime_status==='已结束',
                'text-blue-600': e.runtime_status==='进行中',
                'text-amber-600': e.runtime_status==='计划中'
              }">{{ e.runtime_status }}</span>
            </td>
            <td class="py-3 px-4 text-center">
              <span :class="e.is_published ? 'text-green-600' : 'text-gray-400'">{{ e.is_published ? '已发布' : '未发布' }}</span>
            </td>
            <td class="py-3 px-4">
              <div class="flex flex-wrap justify-center gap-2">
                <button class="text-blue-600" @click="editExam(e.id)"><i class="fas fa-edit"></i> 编辑</button>
                <button class="text-red-600" @click="removeExam(e.id)"><i class="fas fa-trash"></i> 删除</button>
                <button class="text-white px-2 rounded" :class="e.is_published ? 'bg-red-600' : 'bg-green-600'" @click="togglePublish(e.id, e.is_published)">
                  <i class="fas fa-paper-plane mr-1"></i>{{ e.is_published ? '取消发布' : '发布' }}
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!exams.length && !loading"><td colspan="8" class="py-6 text-center text-gray-400">暂无考试数据</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
</style>
