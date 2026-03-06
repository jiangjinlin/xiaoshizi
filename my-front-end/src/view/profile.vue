<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiProfileInfo, apiProfileSave, apiProfileAvatar, apiFaceSupplementSubmit, apiFaceSupplementStatus } from '../api/index'
import { apiFaceEligibility, apiFaceProfile } from '../api/index'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const profile = ref({
  user_id: localStorage.getItem('user_id') || '',
  username: '',
  role: '学生',
  nickname: '',
  email: '',
  phone: '',
  class_name: '',
  dept: ''
})

const avatarUrl = computed(() => userStore.avatarUrl || profile.value.avatar_url || '')

const isStudent = computed(() => {
  const r = String(profile.value.role || '')
  return r.includes('学生') || r.toLowerCase() === 'student'
})
const isTeacher = computed(() => {
  const r = String(profile.value.role || '')
  return r.includes('老师') || r.toLowerCase() === 'teacher'
})

const vipExpiresAt = ref(null)
const faceExpiresAt = ref(null)
const faceExpired = ref(false)
const faceDaysLeft = ref(null)

async function loadProfile() {
  loading.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const { data } = await apiProfileInfo()
    if (data?.success) {
      profile.value = { ...profile.value, ...(data.profile || {}) }
      userStore.setAvatarUrl(profile.value.avatar_url || '')
      vipExpiresAt.value = data.profile?.vip_expires_at || null
      faceExpiresAt.value = data.profile?.face_expires_at || null
      faceExpired.value = !!data.profile?.face_expired
    } else {
      errorMsg.value = data?.error_msg || '获取个人信息失败'
    }
  } catch (e) {
    if (e?.response?.status === 401) { router.push('/login'); return }
    errorMsg.value = '网络错误，无法获取个人信息'
  } finally {
    loading.value = false
  }
  // 尝试获取 face profile 详细（天数）
  try {
    const { data } = await apiFaceProfile()
    if (data?.success) {
      if(data.expires_at && !faceExpiresAt.value) faceExpiresAt.value = data.expires_at
      if(typeof data.days_left === 'number') faceDaysLeft.value = data.days_left
      if(data.expired) faceExpired.value = true
    }
  } catch {}
}

async function saveProfile() {
  saving.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const payload = { ...profile.value }
    const { data } = await apiProfileSave(payload)
    if (data?.success) {
      successMsg.value = '保存成功'
      await loadProfile()
    } else {
      errorMsg.value = data?.error_msg || '保存失败'
    }
  } catch (e) {
    if (e?.response?.status === 401) { router.push('/login'); return }
    errorMsg.value = '网络错误，保存失败'
  } finally {
    saving.value = false
  }
}

function goBack() { router.back() }

// 头像上传
const fileRef = ref(null)
function triggerPick() { fileRef.value && fileRef.value.click() }
async function onPick(e) {
  const file = e?.target?.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('avatar', file)
  try {
    const { data } = await apiProfileAvatar(fd)
    if (data?.success) {
      profile.value.avatar_url = data.avatar_url
      userStore.setAvatarUrl(data.avatar_url)
      successMsg.value = '头像已更新'
    } else {
      errorMsg.value = data?.error_msg || '头像上传失败'
    }
  } catch (err) {
    errorMsg.value = '网络错误，上传失败'
  } finally {
    if (fileRef.value) fileRef.value.value = ''
  }
}

// 人脸照片补充（拍照提交 + 状态列表）
const camOn = ref(false)
const vRef = ref(null)
const cRef = ref(null)
const shot = ref('')
let stream = null
const faceMsg = ref('')
const faceLoading = ref(false)
const faceItems = ref([])
const faceElig = ref({ loading: true, eligible: false, reason: '', rank: null })
const hasApproved = computed(() => faceItems.value.some(it => it.status === 'approved'))
const canSubmitFace = computed(() => {
  // 过期后允许重新提交（即使曾经 approved），需要同时满足资格
  if(faceExpired.value) return faceElig.value.eligible && !faceLoading.value
  return faceElig.value.eligible && !hasApproved.value && !faceLoading.value
})

async function loadEligibility(){
  faceElig.value.loading = true
  try {
    const { data } = await apiFaceEligibility()
    if (data?.success) {
      faceElig.value = { loading: false, eligible: !!data.eligible, reason: data.reason || '', rank: data.rank || null }
    } else {
      faceElig.value = { loading: false, eligible: false, reason: data?.error_msg || '无法获取资格信息', rank: null }
    }
  } catch (e) {
    faceElig.value = { loading: false, eligible: false, reason: '资格查询失败，请稍后刷新', rank: null }
  }
}

async function loadFaceSupps(){
  try{
    const { data } = await apiFaceSupplementStatus()
    if (data?.success){ faceItems.value = data.items || [] }
  }catch{}
}
onMounted(() => { loadProfile(); loadFaceSupps(); loadEligibility() })

async function openCam(){
  faceMsg.value = ''
  try{
    stream = await navigator.mediaDevices.getUserMedia({ video:{ facingMode:'user', width:{ideal:640}, height:{ideal:480} }, audio:false })
    if (vRef.value){ vRef.value.srcObject = stream; await vRef.value.play() }
    camOn.value = true
  }catch{ faceMsg.value = '无法开启摄像头，请检查权限/设备' }
}
function closeCam(){ if (stream){ stream.getTracks().forEach(t=>t.stop()); stream=null } camOn.value=false }
function takeFace(){
  if(!vRef.value || !cRef.value) return
  const w = vRef.value.videoWidth || 640
  const h = vRef.value.videoHeight || 480
  cRef.value.width = w; cRef.value.height = h
  const ctx = cRef.value.getContext('2d')
  ctx.drawImage(vRef.value, 0, 0, w, h)
  shot.value = cRef.value.toDataURL('image/jpeg', 0.9)
}
async function submitFace(){
  if(!shot.value){ faceMsg.value='请先拍照'; return }
  if(!canSubmitFace.value){
    faceMsg.value = faceExpired.value ? '请先确认资格后重新提交过期人脸' : (hasApproved.value ? '已有人脸通过审核，无需重复提交' : (faceElig.value.reason || '当前不符合提交流程'))
    return
  }
  faceLoading.value = true
  faceMsg.value = '提交中...'
  try{
    const { data } = await apiFaceSupplementSubmit(shot.value)
    if (data?.success){
      // 根据状态提示：VIP 直接绑定则立刻显示已绑定
      if (String(data.status||'') === 'approved') {
        faceMsg.value = '已绑定成功（免审核）'
      } else {
        faceMsg.value = faceExpired.value ? '重新提交成功，等待审核' : '提交成功，等待审核'
      }
      shot.value=''
      // 刷新补充记录与资格
      await loadFaceSupps()
      await loadEligibility()
      // 关键：刷新人脸档案状态（到期时间/剩余天数/过期标记）
      try{
        const prof = await apiFaceProfile()
        const d = prof?.data
        if (d?.success){
          faceExpiresAt.value = d.expires_at || null
          faceDaysLeft.value = typeof d.days_left==='number' ? d.days_left : null
          faceExpired.value = !!d.expired
        }
      }catch{}
    } else {
      faceMsg.value = data?.error_msg || '提交失败'
    }
  }catch{ faceMsg.value='网络错误，提交失败' }
  finally{ faceLoading.value = false }
}
onUnmounted(()=> closeCam())

function fmtRemain(expStr){
  if(!expStr) return null
  try{ const d = new Date(expStr.replace(' ','T')); if(isNaN(d.getTime())) return null; const now = Date.now(); const ms = d.getTime() - now; if(ms <= 0) return '已过期'; const days = Math.floor(ms/86400000); if(days<=0) return '不足1天'; return days + ' 天'; }catch{return null}
}
const vipRemain = computed(()=> vipExpiresAt.value ? fmtRemain(vipExpiresAt.value) : null)
const faceRemain = computed(()=> faceExpiresAt.value ? fmtRemain(faceExpiresAt.value) : null)
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-10">
    <div class="max-w-7xl mx-auto px-6">
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
        <div class="flex items-start justify-between gap-4 mb-6">
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded-full ring-2 ring-white overflow-hidden bg-gray-100">
              <img v-if="avatarUrl" :src="avatarUrl" alt="avatar" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                <i class="fas fa-user text-2xl"></i>
              </div>
            </div>
            <div>
              <h2 class="text-2xl md:text-3xl font-bold text-gray-900">个人主页</h2>
              <p class="text-sm text-gray-500 mt-1">查看与维护个人资料</p>
              <div class="mt-2 flex items-center gap-3">
                <input ref="fileRef" type="file" accept="image/*" class="hidden" @change="onPick" />
                <button class="px-3 py-1.5 rounded-md bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 text-xs" @click="triggerPick">更换头像</button>
              </div>
            </div>
          </div>
          <div class="flex flex-col items-end gap-2 text-[11px] text-gray-500">
            <div v-if="vipExpiresAt" class="flex items-center gap-1">
              <i class="fas fa-crown text-amber-500"></i>
              <span>VIP 到期: {{ vipExpiresAt }}</span>
              <span v-if="vipRemain && vipRemain!=='已过期'" class="px-1.5 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-200">剩余 {{ vipRemain }}</span>
              <span v-else class="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200">已过期</span>
            </div>
            <div v-if="faceExpiresAt || faceExpired" class="flex items-center gap-1">
              <i class="fas fa-user-circle" :class="faceExpired ? 'text-red-500' : 'text-emerald-500'"></i>
              <span>人脸{{ faceExpired ? '过期' : '到期' }}: {{ faceExpiresAt || '—' }}</span>
              <span v-if="!faceExpired && faceRemain && faceRemain!=='已过期'" class="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600 border border-emerald-200">剩余 {{ faceRemain }}</span>
              <span v-else-if="faceExpired" class="px-1.5 py-0.5 rounded bg-red-50 text-red-600 border border-red-200">需重新审核</span>
            </div>
          </div>
        </div>

        <div v-if="errorMsg" class="mb-4 rounded-md border border-red-200 bg-red-50 text-red-700 px-4 py-2 text-sm">{{ errorMsg }}</div>
        <div v-if="successMsg" class="mb-4 rounded-md border border-green-200 bg-green-50 text-green-700 px-4 py-2 text-sm">{{ successMsg }}</div>

        <!-- 基本信息 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 text-sm">
          <div class="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <div class="text-gray-500">用户ID</div>
            <div class="mt-1 font-medium text-gray-900 truncate">{{ profile.user_id }}</div>
          </div>
          <div class="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <div class="text-gray-500">用户名（即学号）</div>
            <div class="mt-1 font-medium text-gray-900 truncate">{{ profile.username || '-' }}</div>
          </div>
          <div class="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <div class="text-gray-500">角色</div>
            <div class="mt-1 font-medium text-gray-900">{{ profile.role || '-' }}</div>
          </div>
        </div>

        <!-- 资料编辑（移除学号编辑） -->
        <div class="rounded-2xl border border-gray-100 p-5 mb-6">
          <h3 class="text-sm font-semibold text-gray-800 mb-4">资料编辑</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label class="block">
              <span class="block text-xs text-gray-500 mb-1">昵称</span>
              <input v-model="profile.nickname" type="text" class="w-full h-10 px-3 rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/30" placeholder="请输入昵称" />
            </label>
            <label class="block">
              <span class="block text-xs text-gray-500 mb-1">邮箱</span>
              <input v-model="profile.email" type="email" class="w-full h-10 px-3 rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/30" placeholder="例如: name@example.com" />
            </label>
            <label class="block">
              <span class="block text-xs text-gray-500 mb-1">手机号</span>
              <input v-model="profile.phone" type="tel" class="w-full h-10 px-3 rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/30" placeholder="请输入手机号" />
            </label>
            <label class="block" v-if="isStudent">
              <span class="block text-xs text-gray-500 mb-1">班级</span>
              <input v-model="profile.class_name" type="text" class="w-full h-10 px-3 rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/30" placeholder="例如: 计算机1班" />
            </label>
            <label class="block" v-if="isTeacher">
              <span class="block text-xs text-gray-500 mb-1">所属部门</span>
              <input v-model="profile.dept" type="text" class="w-full h-10 px-3 rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/30" placeholder="例如: 计算机教研室" />
            </label>
          </div>
          <div class="mt-5">
            <button class="px-5 h-10 rounded-md bg-blue-600 text-white hover:bg-blue-700 active:scale-95 transition text-sm" @click="saveProfile" :disabled="saving">
              <span v-if="!saving">保存资料</span>
              <span v-else>保存中...</span>
            </button>
          </div>
        </div>

        <!-- 人脸照片补充 -->
        <div class="rounded-2xl border border-gray-100 p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-gray-800">人脸照片补充</h3>
            <div class="text-xs" :class="canSubmitFace ? 'text-emerald-600' : 'text-gray-500'">
              <template v-if="faceElig.loading">资格检查中...</template>
              <template v-else>
                <span v-if="faceExpired" class="text-red-600">人脸已过期，请重新提交</span>
                <span v-else-if="hasApproved">已绑定（不可取消）</span>
                <span v-else>{{ faceElig.reason }}</span>
                <span v-if="!faceExpired && !hasApproved && faceElig.rank && faceElig.rank>0" class="ml-1 text-gray-400">(当前排名: {{ faceElig.rank }})</span>
              </template>
            </div>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-3">
              <div class="flex flex-wrap items-center gap-2">
                <button class="px-3 h-9 rounded-md bg-primary text-white text-xs disabled:opacity-50" :disabled="hasApproved && !faceExpired" @click="camOn ? takeFace() : openCam()">{{ camOn ? '拍照' : (faceExpired ? '重新拍照' : (hasApproved && !faceExpired ? '已绑定' : '开启摄像头')) }}</button>
                <button v-if="camOn" class="px-3 h-9 rounded-md bg-gray-200 text-gray-700 text-xs" @click="closeCam">关闭</button>
                <button class="px-3 h-9 rounded-md text-xs text-white disabled:opacity-50" :class="canSubmitFace ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-gray-300 text-gray-600'" :disabled="!canSubmitFace" @click="submitFace">
                  <span v-if="!faceLoading">{{ faceExpired ? '重新提交审核' : (hasApproved ? '已绑定' : (canSubmitFace ? '提交审核' : '暂不可提交')) }}</span>
                  <span v-else>提交中...</span>
                </button>
                <button v-if="!faceElig.loading" class="px-3 h-9 rounded-md bg-white border border-gray-200 text-gray-600 text-xs" @click="loadEligibility">刷新资格</button>
              </div>
              <div class="relative w-full aspect-video bg-black/5 rounded overflow-hidden">
                <video ref="vRef" autoplay playsinline muted class="w-full h-full object-cover"></video>
                <canvas ref="cRef" class="hidden"></canvas>
              </div>
              <div class="w-full aspect-video bg-white rounded border border-gray-200 flex items-center justify-center overflow-hidden">
                <img v-if="shot" :src="shot" alt="snapshot" class="w-full h-full object-cover" />
                <span v-else class="text-xs text-gray-400">未拍照</span>
              </div>
              <div v-if="faceMsg" class="text-xs text-gray-600">{{ faceMsg }}</div>
              <div v-if="!faceElig.loading && !faceElig.eligible && !hasApproved" class="text-[11px] text-amber-600 leading-snug">
                若您是活跃贡献者，请继续参与题目审查以提升排名；VIP 账号可联系管理员升级。
              </div>
            </div>
            <div>
              <div class="text-xs text-gray-500 mb-2">我的补充提交</div>
              <div class="space-y-2 max-h-[360px] overflow-auto pr-1">
                <div v-for="it in faceItems" :key="it.id" class="flex items-center gap-3 p-2 rounded border border-gray-200 bg-white">
                  <img v-if="it.image_url" :src="it.image_url" class="w-16 h-10 object-cover rounded" />
                  <div class="flex-1 min-w-0">
                    <div class="text-xs text-gray-700 truncate">{{ it.created_at }}</div>
                    <div class="text-[11px] text-gray-500 truncate">ID: {{ it.id }}</div>
                  </div>
                  <span class="text-[11px] px-2 py-0.5 rounded-full border" :class="{
                    'bg-amber-50 text-amber-700 border-amber-200': it.status==='pending',
                    'bg-emerald-50 text-emerald-700 border-emerald-200': it.status==='approved',
                    'bg-red-50 text-red-600 border-red-200': it.status==='rejected'
                  }">{{ it.status }}</span>
                </div>
                <div v-if="!faceItems.length" class="text-xs text-gray-400 py-6 text-center">暂无提交记录</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* 保持与首页风格一致 */
</style>
