<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiExamSelect, apiLogout } from '../api/index'
import { useSyllabusStore } from '../stores/syllabus'
import AppLogo from '../components/AppLogo.vue'

const router = useRouter()
const s = useSyllabusStore()
const loading = ref(true)
const exams = ref([])
const err = ref('')

async function load(){
  loading.value = true
  err.value = ''
  try{
    // 使用 /api/exam-select (已发布考试列表，不限制当前时间窗口)
    const { data } = await apiExamSelect()
    if (data?.success){
      exams.value = (data.exams||[]).map(e=>({
        id: e.id || e.exam_id,
        title: e.title,
        start_time: e.start_time,
        end_time: e.end_time,
        duration: e.duration
      }))
    }else{
      err.value = data?.error_msg || '加载考试列表失败'
    }
  }catch(e){
    if (e?.response?.status === 401){
      localStorage.removeItem('user_id')
      s.clear()
      router.push('/login')
      return
    }
    err.value = e?._friendly || '网络错误或服务器异常'
  }finally{
    loading.value = false
  }
}

async function chooseExam(exam){
  const id = Number(exam.id)
  try{ sessionStorage.setItem('last_exam_id', String(id)) }catch{}
  router.push({ path: '/signin', query: { exam_id: String(id) } })
}

function goBack(){ router.push('/student') }
async function handleLogout(){ try{ await apiLogout() }catch{} localStorage.removeItem('user_id'); s.clear(); router.push('/login') }

onMounted(load)
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="goBack" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">选择考试</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <button class="px-4 h-10 rounded-lg bg-gray-100 text-gray-700 border border-gray-200" @click="goBack">返回</button>
          <button class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition" @click="handleLogout">退出</button>
        </div>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto pt-24 pb-16 px-4">
      <div class="rounded-2xl border border-gray-200 bg-white/80 p-6 shadow-sm">
        <h1 class="text-xl font-semibold text-gray-900 mb-4">请选择要参加的考试</h1>
        <div v-if="loading" class="text-sm text-gray-500">加载中...</div>
        <div v-else-if="err" class="text-sm text-red-600">{{ err }}</div>
        <div v-else>
          <div v-if="!exams.length" class="text-sm text-gray-500">暂无可参加的考试</div>
          <ul v-else class="grid gap-4 md:grid-cols-2">
            <li v-for="exam in exams" :key="exam.id" class="rounded-xl border border-gray-200 bg-white/70 p-4 hover:shadow transition cursor-pointer" @click="chooseExam(exam)">
              <div class="text-base font-medium text-gray-900 truncate">{{ exam.title }}</div>
              <div class="mt-1 text-xs text-gray-500">时间：{{ exam.start_time }} - {{ exam.end_time }}</div>
              <div class="mt-1 text-xs text-gray-500">时长：{{ exam.duration }} 分钟</div>
              <div class="mt-3">
                <button class="h-9 px-3 rounded-lg bg-primary text-white text-xs">选择此考试并去签到</button>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* use global .text-primary from tokens.css */
</style>
