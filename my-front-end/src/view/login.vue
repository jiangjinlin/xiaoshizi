<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiLogin } from '../api/index'
import { getStaticURL } from '../api/http'

const username = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)
const showPassword = ref(false)
const router = useRouter()

// 站点 Logo（从后端 /static/logo.png 提供，支持局域网设置）
const logoUrl = ref('')
onMounted(() => {
  try {
    logoUrl.value = getStaticURL('/static/logo.png')
  } catch {
    logoUrl.value = '/static/logo.png'
  }
})

async function handleLogin() {
  if (loading.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    const res = await apiLogin({ username: username.value.trim(), password: password.value })
    if (res.data && res.data.success) {
      const role = res.data.role
      if (res.data.user_id) localStorage.setItem('user_id', res.data.user_id)
      if (role) localStorage.setItem('role', role)
      if (role === '学生' || role === 'VIP') router.push('/student')
      else if (role === '老师') router.push('/teacher')
      else if (role === '管理员') router.push('/admin')
      else router.push('/')
    } else {
      errorMsg.value = res.data?.error_msg || '用户名或密码错误'
    }
  } catch (e) {
    if (e.response) {
      const s = e.response.status
      if (s === 405) errorMsg.value = '请求方式不正确（应为 POST）'
      else if (s === 401) errorMsg.value = '未登录或登录已过期'
      else if (s === 500) errorMsg.value = '服务器内部错误，请稍后重试'
      else errorMsg.value = e.response.data?.detail || '请求失败，状态码：' + s
    } else if (e.request) {
      errorMsg.value = '无法连接服务器，请检查网络'
    } else {
      errorMsg.value = '未知错误：' + e.message
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gradient-to-br from-gray-50 via-indigo-50 to-white relative">
    <!-- 顶部简易导航 -->
    <div class="h-16 flex items-center justify-between px-6 md:px-10">
      <div class="flex items-center gap-2 cursor-pointer select-none" @click="router.push('/')">
        <img :src="logoUrl" alt="站点LOGO" class="h-8 w-auto" />
        <span class="hidden sm:inline text-sm text-gray-500 tracking-wide">智能无纸化考试系统</span>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <button class="px-4 py-2 rounded-md text-primary hover:bg-primary/10 transition" @click="router.push('/')">返回首页</button>
      </div>
    </div>

    <div class="flex-1 flex items-center justify-center px-4 pb-16">
      <div class="relative w-full max-w-md">
        <div class="absolute -inset-1 rounded-3xl bg-gradient-to-tr from-primary/20 via-indigo-200/30 to-transparent blur-xl opacity-70"></div>
        <div class="relative rounded-2xl border border-gray-200/70 bg-white/70 backdrop-blur-xl p-8 md:p-10 shadow-sm">
          <div class="mb-8 text-center space-y-2">
            <h1 class="text-2xl font-semibold text-gray-900">账户登录</h1>
            <p class="text-sm text-gray-500">请输入您的账号与密码以访问系统</p>
          </div>
          <form @submit.prevent="handleLogin" class="space-y-6">
            <!-- 用户名 -->
            <div class="space-y-1">
              <label class="text-xs font-medium text-gray-600 tracking-wide">用户名</label>
              <div class="relative group">
                <i class="fas fa-user absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
                <input v-model="username" autocomplete="username" placeholder="请输入用户名" class="w-full h-11 pl-10 pr-3 rounded-lg border border-gray-300/80 bg-white/70 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary text-sm transition placeholder:text-gray-400" />
              </div>
            </div>
            <!-- 密码 -->
            <div class="space-y-1">
              <label class="text-xs font-medium text-gray-600 tracking-wide">密码</label>
              <div class="relative group">
                <i class="fas fa-lock absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
                <input :type="showPassword ? 'text' : 'password'" v-model="password" autocomplete="current-password" placeholder="请输入密码" class="w-full h-11 pl-10 pr-10 rounded-lg border border-gray-300/80 bg-white/70 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary text-sm transition placeholder:text-gray-400" />
                <button type="button" @click="showPassword = !showPassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary transition" :aria-label="showPassword ? '隐藏密码' : '显示密码'">
                  <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </button>
              </div>
            </div>
            <!-- 错误提示 -->
            <transition name="fade" mode="out-in">
              <div v-if="errorMsg" class="text-xs rounded-md border border-red-200 bg-red-50 text-red-600 px-3 py-2 flex items-start gap-2">
                <i class="fas fa-circle-exclamation mt-0.5"></i>
                <span class="leading-relaxed">{{ errorMsg }}</span>
              </div>
            </transition>
            <!-- 登录按钮 -->
            <div class="space-y-3 pt-2">
              <button type="submit" :disabled="loading" class="w-full inline-flex items-center justify-center h-11 rounded-lg bg-primary text-white text-sm font-medium tracking-wide shadow-sm hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition relative">
                <span v-if="!loading">登录</span>
                <span v-else class="flex items-center gap-2">
                  <svg class="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none"><circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" stroke-width="4" stroke-linecap="round" class="opacity-90"/></svg>
                  正在登录...
                </span>
              </button>
              <div class="flex items-center justify-between text-xs text-gray-500">
                <button type="button" class="hover:text-primary transition" @click="router.push('/register')">还没有账号？去注册</button>
                <button type="button" class="hover:text-primary transition" @click="router.push('/')">返回首页</button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
.fade-enter-active, .fade-leave-active { transition: opacity .18s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>