<script setup>
import { useRouter } from 'vue-router';
import { apiExamList, apiLogout, apiProfileInfo } from '../api/index';
import { onMounted, computed } from 'vue'
import { useUserStore } from '../stores/user'
import { useSyllabusStore } from '../stores/syllabus'
import ThemeToggle from '../components/ThemeToggle.vue'
import SyllabusPicker from '../components/SyllabusPicker.vue'
import AppLogo from '../components/AppLogo.vue'

const router = useRouter();
const userStore = useUserStore()
const s = useSyllabusStore()
const avatarUrl = computed(() => userStore.avatarUrl)
const username = computed(() => userStore.username || '用户')
const role = computed(() => userStore.role || '学生')

async function startExam() {
  // 调整为：先进入考试选择页，再前往签到
  try {
    await apiExamList();
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      router.push('/login');
      return;
    }
    router.push('/exam_select');
  } catch (e) {
    if (e.response && e.response.status === 401) {
      localStorage.removeItem('user_id');
      userStore.clear()
      s.clear()
      router.push('/login');
    } else {
      alert('网络错误或服务器异常');
    }
  }
}

// 成绩查询
function goScoreQuery() {
  router.push('/score_query');
}

// 新增：专项练习
function goPractice() {
  router.push('/practice');
}

// 新增：个人主页
function goProfile() { router.push('/profile') }

// 新增：题目审查
function goReview() { router.push('/review') }

// 退出登录
async function handleLogout() {
  try {
    await apiLogout();
  } catch (e) {
    // 忽略错误
  }
  localStorage.removeItem('user_id');
  userStore.clear()
  s.clear()
  router.push('/login');
}

onMounted(async () => {
  try {
    // 优先加载全局资料，确保头像同步
    await userStore.loadProfile()
    // 兼容：如果需要，也保留一次直接请求（可选）
    const { data } = await apiProfileInfo()
    if (data?.success) userStore.setAvatarUrl(data.profile?.avatar_url || '')
  } catch {}
})
</script>

<template>
  <!-- 新结构：渐变背景 + 顶部导航 + 居中内容卡片 -->
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="router.push('/')" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">学生首页</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <SyllabusPicker />
          <ThemeToggle />
          <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/60 border border-gray-200 text-gray-600">
            <div class="w-7 h-7 rounded-full overflow-hidden bg-gray-100">
              <img v-if="avatarUrl" :src="avatarUrl" alt="avatar" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-400"><i class="fas fa-user"></i></div>
            </div>
            <span class="max-w-[90px] truncate" :title="username">{{ username }}</span>
            <span class="px-1.5 py-0.5 text-[10px] rounded bg-primary/10 text-primary">{{ role }}</span>
          </div>
          <button class="btn-secondary h-10 px-4 flex items-center gap-2" @click="handleLogout">
            <i class="fas fa-sign-out-alt"></i><span>退出</span>
          </button>
        </div>
      </div>
    </nav>

    <div class="pt-24 pb-16 px-4">
      <div class="max-w-xl mx-auto">
        <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-10 shadow-sm hover:shadow-md transition flex flex-col items-center">
          <!-- 这里用头像替换默认图标 -->
          <div class="w-24 h-24 rounded-full overflow-hidden bg-gray-100 ring-2 ring-white mb-6">
            <img v-if="avatarUrl" :src="avatarUrl" alt="avatar" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
              <i class="fas fa-user text-4xl"></i>
            </div>
          </div>
          <h1 class="text-2xl font-bold text-gray-800 mb-8 tracking-tight">欢迎使用智能无纸化考试系统</h1>
          <div class="w-full flex flex-col gap-4">
            <button class="btn-primary h-12" @click="startExam">开始考试</button>
            <button class="btn-primary h-12" @click="goPractice">专项练习</button>
            <button class="btn-primary h-12" @click="goScoreQuery">成绩查询</button>
            <button class="btn-secondary h-12" @click="goProfile">个人主页</button>
            <button class="btn-secondary h-12" @click="goReview">题目审查</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
/* use global .text-primary/.bg-primary/.rounded-button from tokens.css */
</style>