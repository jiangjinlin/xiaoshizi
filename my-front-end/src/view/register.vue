<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import {http} from "../api/http.js";
import AppLogo from '../components/AppLogo.vue'

const router = useRouter()
const username = ref('')
const password = ref('')
const classroom = ref('')
const message = ref('')
const messageType = ref('')
const loading = ref(false)
const showPassword = ref(false)

function resetMessage(){ message.value=''; messageType.value='' }
function validate(){
  resetMessage()
  if(!username.value || !password.value || !classroom.value){ message.value='请填写所有必填项'; messageType.value='error'; return false }
  if(username.value.length < 3){ message.value='用户名长度至少 3 个字符'; messageType.value='error'; return false }
  if(/\s/.test(username.value)){ message.value='用户名不能包含空格'; messageType.value='error'; return false }
  if(password.value.length < 6){ message.value='密码长度至少 6 个字符'; messageType.value='error'; return false }
  return true
}

async function handleRegister(){
  if(loading.value) return
  if(!validate()) return
  loading.value = true
  try {
    const { data } = await http.post('/api/register', {
      username: username.value.trim(),
      password: password.value,
      classroom: classroom.value.trim()
    })
    if(!data.success){
      message.value = data.error_msg || '注册失败';
      messageType.value = 'error';
      return
    }
    message.value = '注册成功，正在跳转登录...'
    messageType.value = 'success'
    setTimeout(()=> router.push('/login'), 1200)
  } catch(e){
    message.value = e?.response?.data?.error_msg || '服务器异常，请稍后重试'
    messageType.value = 'error'
  } finally { loading.value = false }
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gradient-to-br from-gray-50 via-indigo-50 to-white relative">
    <!-- 顶部导航栏 -->
    <div class="h-16 flex items-center justify-between px-6 md:px-10">
      <div class="flex items-center gap-2 cursor-pointer select-none" @click="router.push('/')">
        <AppLogo :height="36" />
        <span class="hidden sm:inline text-sm text-gray-500 tracking-wide">智能无纸化考试系统</span>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <button class="px-4 py-2 rounded-md text-primary hover:bg-primary/10 transition" @click="router.push('/login')">去登录</button>
      </div>
    </div>

    <!-- 主体卡片 -->
    <div class="flex-1 flex items-center justify-center px-4 pb-16">
      <div class="relative w-full max-w-xl">
        <div class="absolute -inset-1 rounded-3xl bg-gradient-to-tr from-primary/20 via-indigo-200/30 to-transparent blur-xl opacity-70"></div>
        <div class="relative rounded-2xl border border-gray-200/70 bg-white/70 backdrop-blur-xl p-8 md:p-10 shadow-sm">
          <div class="mb-8 text-center space-y-2">
            <h1 class="text-2xl font-semibold text-gray-900">学生注册</h1>
            <p class="text-sm text-gray-500">仅支持学生自助注册；VIP/老师请联系管理员。人脸审核需在个人主页符合条件后发起。</p>
          </div>

          <!-- 提示消息 -->
          <transition name="fade" mode="out-in">
            <div v-if="message" :class="['mb-6 text-xs rounded-md px-3 py-2 flex items-start gap-2 border', messageType==='success' ? 'bg-emerald-50 text-emerald-600 border-emerald-200':'bg-red-50 text-red-600 border-red-200']">
              <i :class="messageType==='success' ? 'fas fa-check-circle mt-0.5':'fas fa-circle-exclamation mt-0.5'"></i>
              <span class="leading-relaxed">{{ message }}</span>
            </div>
          </transition>

          <form @submit.prevent="handleRegister" class="space-y-7">
            <!-- 用户名 -->
            <div class="space-y-1">
              <label class="text-xs font-medium text-gray-600 tracking-wide">用户名（学号）</label>
              <div class="relative">
                <i class="fas fa-user absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
                <input v-model="username" maxlength="30" autocomplete="off" placeholder="3-30 个字符，勿含空格" class="w-full h-11 pl-10 pr-3 rounded-lg border border-gray-300/80 bg-white/70 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary text-sm placeholder:text-gray-400" />
              </div>
            </div>
            <!-- 密码 -->
            <div class="space-y-1">
              <label class="text-xs font-medium text-gray-600 tracking-wide">密码</label>
              <div class="relative">
                <i class="fas fa-lock absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
                <input :type="showPassword ? 'text' : 'password'" v-model="password" placeholder="至少 6 位" class="w-full h-11 pl-10 pr-10 rounded-lg border border-gray-300/80 bg-white/70 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary text-sm placeholder:text-gray-400" />
                <button type="button" @click="showPassword=!showPassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary transition" :aria-label="showPassword?'隐藏密码':'显示密码'">
                  <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </button>
              </div>
            </div>
            <!-- 班级 -->
            <div class="space-y-1">
              <label class="text-xs font-medium text-gray-600 tracking-wide">班级</label>
              <div class="relative">
                <i class="fas fa-users-class absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
                <input v-model="classroom" placeholder="例如：22级计算机1班" class="w-full h-11 pl-10 pr-3 rounded-lg border border-gray-300/80 bg-white/70 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary text-sm placeholder:text-gray-400" />
              </div>
            </div>

            <!-- 提交 -->
            <div class="pt-2 space-y-4">
              <button type="submit" :disabled="loading" class="w-full inline-flex items-center justify-center h-11 rounded-lg bg-primary text-white text-sm font-medium tracking-wide shadow-sm hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition">
                <span v-if="!loading">注册账号</span>
                <span v-else class="flex items-center gap-2">
                  <svg class="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none"><circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" stroke-width="4" stroke-linecap="round" class="opacity-90"/></svg>
                  提交中...
                </span>
              </button>
              <div class="flex items-center justify-between text-xs text-gray-500">
                <button type="button" class="hover:text-primary transition" @click="router.push('/login')">已有账号？去登录</button>
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
.fade-enter-from, .fade-leave-to { opacity:0; }
</style>