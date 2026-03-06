<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiFaceStatus, apiFaceSignin } from '../api/index'

const router = useRouter()
const route = useRoute()
const checking = ref(true)
const signedIn = ref(false)
const ttl = ref(0)
const msg = ref('')

const mode = ref('auto') // local/cloud/auto
const examId = ref('')

// 摄像头
const cameraOn = ref(false)
const videoRef = ref(null)
const canvasRef = ref(null)
const snapshot = ref('')
let mediaStream = null

function initParams(){
  const qid = route?.query?.exam_id ? String(route.query.exam_id) : ''
  examId.value = qid
  return true
}

async function checkStatus(){
  checking.value = true
  try{
    const params = {}
    if (examId.value) params.exam_id = examId.value
    const { data } = await apiFaceStatus(params)
    signedIn.value = !!data?.signed_in
    ttl.value = Number(data?.ttl_minutes || 0)
  }catch{ signedIn.value = false }
  finally{ checking.value = false }
}

async function startCamera(){
  msg.value = ''
  try{
    mediaStream = await navigator.mediaDevices.getUserMedia({ video:{ facingMode:'user', width:{ideal:640}, height:{ideal:480} }, audio:false })
    if (videoRef.value){ videoRef.value.srcObject = mediaStream; await videoRef.value.play() }
    cameraOn.value = true
  }catch{ msg.value = '无法开启摄像头，请检查权限/设备' }
}
function stopCamera(){ if(mediaStream){ mediaStream.getTracks().forEach(t=>t.stop()); mediaStream=null } cameraOn.value=false }
function takeShot(){
  if(!videoRef.value || !canvasRef.value) return
  const w = videoRef.value.videoWidth || 640
  const h = videoRef.value.videoHeight || 480
  canvasRef.value.width = w; canvasRef.value.height = h
  const ctx = canvasRef.value.getContext('2d')
  ctx.drawImage(videoRef.value, 0, 0, w, h)
  snapshot.value = canvasRef.value.toDataURL('image/jpeg', 0.9)
}
async function doSignin(){
  if(!snapshot.value){ msg.value='请先拍照'; return }
  msg.value='识别中...'
  try{
    const payload = { image_base64: snapshot.value, mode: mode.value }
    if (examId.value) payload.exam_id = Number(examId.value)
    const { data } = await apiFaceSignin(payload.image_base64, payload.exam_id, payload.mode)
    if(data?.success){
      signedIn.value = true; msg.value='签到成功'; stopCamera()
      const redirect = route.query.redirect ? String(route.query.redirect) : ''
      if (examId.value){
        setTimeout(()=>router.push({ path:'/exam', query:{ exam_id: String(examId.value) } }), 600)
      } else if (redirect) {
        setTimeout(()=>router.push(redirect), 600)
      } else {
        setTimeout(()=>router.push('/practice/setup'), 600)
      }
    }
    else { msg.value = (data?.error_msg || '签到失败，请重试') + (data?.method?`（方式：${data.method}）`: '') }
  }catch{ msg.value='网络异常，请稍后重试' }
}

onMounted(async()=>{ initParams(); await checkStatus() })
onUnmounted(()=> stopCamera())
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white">
    <div class="max-w-4xl mx-auto px-5 py-8">
      <h1 class="text-2xl font-semibold text-gray-900 mb-4">人脸验证</h1>
      <div class="rounded-2xl border border-gray-200 bg-white/80 p-5 mb-6">
        <div class="mb-3 grid gap-3 md:grid-cols-2">
          <div>
            <label class="block text-xs text-gray-600 mb-1">识别模式</label>
            <select v-model="mode" class="h-10 w-full border border-gray-300 rounded px-3 text-sm bg-white">
              <option value="auto">自动（优先本地，失败再云端）</option>
              <option value="local">仅本地</option>
              <option value="cloud">仅云端</option>
            </select>
          </div>
        </div>
        <ol class="list-decimal pl-5 text-sm text-gray-700 space-y-1">
          <li>签到通过后 {{ ttl || 120 }} 分钟内有效。</li>
          <li v-if="examId">当前为考试签到，仅对本场考试生效。</li>
          <li v-else>当前为通用验证，可用于专项练习与知识点练习。</li>
        </ol>
      </div>

      <div class="rounded-2xl border border-gray-200 bg-white/80 p-5 shadow-sm">
        <div v-if="checking" class="text-sm text-gray-500">状态检查中...</div>
        <div v-else-if="signedIn" class="flex items-center justify-between">
          <div class="text-emerald-700 text-sm">已完成人脸验证，可以继续操作。</div>
          <router-link v-if="examId" :to="{ path:'/exam', query:{ exam_id: examId } }" class="px-4 h-10 rounded-md bg-primary text-white text-sm flex items-center">进入考试</router-link>
          <router-link v-else :to="(route.query.redirect? String(route.query.redirect): '/practice/setup')" class="px-4 h-10 rounded-md bg-primary text-white text-sm flex items-center">返回</router-link>
        </div>
        <div v-else class="space-y-3">
          <div class="flex items-center gap-2">
            <button class="px-3 h-9 rounded-md bg-primary text-white text-xs bg-emerald-600" @click="cameraOn ? takeShot() : startCamera()">{{ cameraOn ? '拍照' : '开始识别' }}</button>
            <button v-if="cameraOn" class="px-3 h-9 rounded-md bg-gray-200 text-gray-700 text-xs" @click="stopCamera">关闭</button>
            <button class="px-3 h-9 rounded-md bg-emerald-600 text-white text-xs" @click="doSignin">提交</button>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="relative w-full aspect-video bg-black/5 rounded overflow-hidden">
              <video ref="videoRef" autoplay playsinline muted class="w-full h-full object-cover"></video>
              <canvas ref="canvasRef" class="hidden"></canvas>
            </div>
            <div class="w-full aspect-video bg-white rounded border border-gray-200 flex items-center justify-center overflow-hidden">
              <img v-if="snapshot" :src="snapshot" alt="snapshot" class="w-full h-full object-cover" />
              <span v-else class="text-xs text-gray-400">未拍照</span>
            </div>
          </div>
          <div v-if="msg" class="text-xs text-gray-600">{{ msg }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.text-primary{ color:#2563eb }
</style>
