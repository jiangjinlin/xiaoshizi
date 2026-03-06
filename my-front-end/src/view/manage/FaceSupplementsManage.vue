<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiManageFaceSupplements, apiManageFaceSupplementApprove, apiManageFaceSupplementReject } from '../../api/index'
import AppLogo from '../../components/AppLogo.vue'

const router = useRouter()
const loading = ref(false)
const items = ref([])
const status = ref('pending') // pending | approved | rejected | ''
const keyword = ref('') // 支持按用户名/用户ID过滤（前端本地过滤）
const msg = ref('')

async function fetchList(){
  loading.value = true
  msg.value = ''
  try{
    const { data } = await apiManageFaceSupplements({ status: status.value || undefined })
    if (data?.success){
      items.value = data.items || []
    } else {
      items.value = []
      msg.value = data?.error_msg || '加载失败'
    }
  }catch{ msg.value='网络错误，加载失败'; items.value=[] }
  finally{ loading.value = false }
}

function filtered(){
  const k = keyword.value.trim().toLowerCase()
  if (!k) return items.value
  return items.value.filter(it => String(it.username||'').toLowerCase().includes(k) || String(it.user_id||'').includes(k))
}

async function approve(it){
  if (!confirm('确认通过此人脸补充并入库？')) return
  try{
    const { data } = await apiManageFaceSupplementApprove(it.id)
    if (data?.success){ await fetchList() }
    else { alert(data?.error_msg||'操作失败') }
  }catch{ alert('网络错误，操作失败') }
}
async function reject(it){
  const reason = prompt('请输入驳回原因（可空）：') || ''
  try{
    const { data } = await apiManageFaceSupplementReject(it.id, reason)
    if (data?.success){ await fetchList() }
    else { alert(data?.error_msg||'操作失败') }
  }catch{ alert('网络错误，操作失败') }
}

onMounted(fetchList)
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="$router.push('/admin')" />
          <span class="text-lg font-semibold text-gray-700 hidden sm:inline">人脸补充审核</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <router-link to="/admin" class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition flex items-center gap-2"><i class="fas fa-home"></i><span>返回首页</span></router-link>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto pt-20 pb-10 px-6">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 shadow-sm mb-4">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-700">状态</label>
            <select v-model="status" @change="fetchList" class="h-9 border border-gray-300 rounded px-3 text-sm bg-white">
              <option value="pending">待审核</option>
              <option value="approved">已通过</option>
              <option value="rejected">已驳回</option>
              <option value="">全部</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="keyword" placeholder="按用户名或用户ID过滤" class="h-9 w-60 border border-gray-300 rounded px-3 text-sm bg-white" />
            <button class="h-9 px-3 rounded bg-primary text-white text-xs" @click="fetchList">刷新</button>
          </div>
        </div>
      </div>

      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 shadow-sm">
        <div v-if="loading" class="text-center text-gray-400 py-10 text-sm">加载中...</div>
        <div v-else>
          <div v-if="msg" class="mb-3 text-xs text-red-600">{{ msg }}</div>
          <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div v-for="it in filtered()" :key="it.id" class="rounded-xl border border-gray-200 bg-white overflow-hidden">
              <div class="h-40 bg-gray-50 flex items-center justify-center">
                <img v-if="it.image_url" :src="it.image_url" class="max-h-full object-contain" />
                <span v-else class="text-gray-400 text-xs">无预览</span>
              </div>
              <div class="p-3 text-xs text-gray-700">
                <div class="flex items-center justify-between mb-1">
                  <div class="truncate">用户：{{ it.username }}（{{ it.user_id }}）</div>
                  <span class="px-2 py-0.5 rounded-full border" :class="{
                    'bg-amber-50 text-amber-700 border-amber-200': it.status==='pending',
                    'bg-emerald-50 text-emerald-700 border-emerald-200': it.status==='approved',
                    'bg-red-50 text-red-600 border-red-200': it.status==='rejected'
                  }">{{ it.status }}</span>
                </div>
                <div class="text-gray-500">提交时间：{{ it.created_at || '-' }}</div>
                <div class="text-gray-500" v-if="it.reason">原因：{{ it.reason }}</div>
                <div class="mt-2 flex items-center gap-2">
                  <button v-if="it.status==='pending'" class="flex-1 h-8 rounded bg-emerald-600 text-white" @click="approve(it)">通过</button>
                  <button v-if="it.status==='pending'" class="flex-1 h-8 rounded bg-red-600 text-white" @click="reject(it)">驳回</button>
                  <button v-if="it.status!=='pending'" disabled class="flex-1 h-8 rounded bg-gray-200 text-gray-500">已处理</button>
                </div>
              </div>
            </div>
          </div>
          <div v-if="!filtered().length && !loading" class="text-center text-gray-400 py-10 text-sm">暂无数据</div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.text-primary{ color:#2563eb }
</style>
