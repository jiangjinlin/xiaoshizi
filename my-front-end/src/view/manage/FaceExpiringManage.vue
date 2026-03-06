<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiManageFaceExpiring } from '../../api/index'

const loading = ref(false)
const itemsRaw = ref([])
const errorMsg = ref('')

// 查询参数
const days = ref(3)
const statusFilter = ref('') // expiring|expired|''
const search = ref('')
const sortField = ref('days_left')
const sortDir = ref('asc')

// 分页
const page = ref(1)
const pageSize = ref(20)

// 新增：多选与动作
const selectedIds = ref([])
const allChecked = computed(()=> pageData.value.length>0 && pageData.value.every(it=> selectedIds.value.includes(it.user_id)))

const route = useRoute()
const router = useRouter()

// Rename applyQuery to applyQueryParams for consistency with onMounted
function applyQueryParams(){
  const q = route.query || {}
  if(q.days) { const d = parseInt(q.days); if(!isNaN(d)&&d>0) days.value=d }
  if(q.status) statusFilter.value=String(q.status)
  if(q.search) search.value=String(q.search)
  if(q.sort_field) sortField.value=String(q.sort_field)
  if(q.sort_dir) sortDir.value=String(q.sort_dir)
  if(q.page) { const p=parseInt(q.page); if(!isNaN(p)&&p>0) page.value=p }
}

function pushQuery(){
  const q={ days:days.value }
  if(statusFilter.value) q.status=statusFilter.value
  if(search.value) q.search=search.value
  if(sortField.value) { q.sort_field=sortField.value; q.sort_dir=sortDir.value }
  if(page.value>1) q.page=page.value
  router.replace({ query:q })
}

async function load(){
  loading.value=true; errorMsg.value=''; itemsRaw.value=[]
  try{
    const { data } = await apiManageFaceExpiring({ days: days.value })
    if(data?.success){ itemsRaw.value = data.items||[] } else { errorMsg.value=data?.error_msg||'加载失败' }
    page.value=1
    pushQuery()
  }catch{ errorMsg.value='网络错误' } finally { loading.value=false }
}

function toggleSort(field){
  if(sortField.value===field) sortDir.value = (sortDir.value==='asc'?'desc':'asc')
  else { sortField.value=field; sortDir.value='asc' }
}

const filtered = computed(()=>{
  let arr = itemsRaw.value
  if(statusFilter.value) arr = arr.filter(it=> it.state===statusFilter.value)
  if(search.value.trim()) { const kw = search.value.trim().toLowerCase(); arr = arr.filter(it=> String(it.username||'').toLowerCase().includes(kw) || String(it.user_id).includes(kw) ) }
  // derive days_left for expired as 0 if null
  arr = arr.map(it=> ({ ...it, _days: it.state==='expired'?0:(it.days_left==null?999999:it.days_left) }))
  if(sortField.value==='days_left'){
    arr = [...arr].sort((a,b)=>{ const av=a._days; const bv=b._days; if(av===bv) return 0; return (av>bv?1:-1)*(sortDir.value==='asc'?1:-1) })
  } else if(sortField.value==='expires_at'){
    arr=[...arr].sort((a,b)=>{ const av=a.expires_at||''; const bv=b.expires_at||''; return av.localeCompare(bv)*(sortDir.value==='asc'?1:-1) })
  }
  return arr
})
const total = computed(()=> filtered.value.length)
const pageCount = computed(()=> Math.max(1, Math.ceil(total.value / pageSize.value)))
const pageData = computed(()=> filtered.value.slice((page.value-1)*pageSize.value, (page.value-1)*pageSize.value + pageSize.value))

function prev(){ if(page.value>1){ page.value--; pushQuery() } }
function next(){ if(page.value<pageCount.value){ page.value++; pushQuery() } }

function resetFilters(){ statusFilter.value=''; search.value=''; sortField.value='days_left'; sortDir.value='asc'; page.value=1; pushQuery() }

function exportCsv(){
  const header=['用户ID','用户名','状态','到期时间','剩余天数']
  const lines=[header.join(',')]
  filtered.value.forEach(it=>{ lines.push([it.user_id, it.username||'', it.state==='expiring'?'即将到期':'已过期', it.expires_at||'', it.days_left!=null?it.days_left:(it.state==='expired'?0:'')].map(v=>`"${String(v).replace(/"/g,'""')}"`).join(',')) })
  const blob=new Blob(["\ufeff"+lines.join('\n')], {type:'text/csv;charset=utf-8;'})
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`face_expiring_${days.value}d.csv`; a.click(); URL.revokeObjectURL(a.href)
}

watch([days], ()=>{ load() })
watch([statusFilter, search, sortField, sortDir, pageSize], ()=>{ page.value=1; pushQuery() })
watch(pageData, ()=>{ // 页切换后清理不存在的ID
  selectedIds.value = selectedIds.value.filter(id => pageData.value.some(it=>it.user_id===id))
})

onMounted(()=>{ applyQueryParams(); load() })

function toggleAll(){ if(allChecked.value) selectedIds.value=[]; else selectedIds.value = pageData.value.map(it=>it.user_id) }
function toggleOne(id){ const i=selectedIds.value.indexOf(id); if(i>=0) selectedIds.value.splice(i,1); else selectedIds.value.push(id) }
function clearSelection(){ selectedIds.value=[] }

// 统计汇总
const expiringCount = computed(()=> filtered.value.filter(it=>it.state==='expiring').length)
const expiredCount = computed(()=> filtered.value.filter(it=>it.state==='expired').length)

// 快捷过滤
function quickFilter(state){ statusFilter.value=state; page.value=1; pushQuery() }
function quickDays(delta){ const d=days.value+delta; if(d>0){ days.value=d } }

// 导出选中
function exportSelected(){
  if(!selectedIds.value.length){ alert('请先勾选记录'); return }
  const header=['用户ID','用户名','状态','到期时间','剩余天数']
  const lines=[header.join(',')]
  filtered.value.filter(it=>selectedIds.value.includes(it.user_id)).forEach(it=>{
    lines.push([it.user_id, it.username||'', it.state==='expiring'?'即将到期':'已过期', it.expires_at||'', it.days_left!=null?it.days_left:(it.state==='expired'?0:'')].map(v=>`"${String(v).replace(/"/g,'""')}"`).join(','))
  })
  const blob=new Blob(["\ufeff"+lines.join('\n')], {type:'text/csv;charset=utf-8;'})
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`face_expiring_selected.csv`; a.click(); URL.revokeObjectURL(a.href)
}

// 复制选中ID
async function copySelected(){
  if(!selectedIds.value.length){ alert('请先勾选记录'); return }
  const text = selectedIds.value.join(',')
  try{ await navigator.clipboard.writeText(text); alert('已复制选中用户ID') }catch{ const ta=document.createElement('textarea'); ta.value=text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); alert('已复制') }
}

// 跳转到学生管理筛选
function goStudentFiltered(state){ router.push(`/manage/students?face_status=${state}`) }
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6 flex-wrap gap-4">
      <h1 class="text-2xl font-bold flex items-center gap-3">
        人脸到期管理
        <span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 text-xs border border-amber-200" v-if="total>0">共 {{ total }}</span>
        <span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 text-xs border border-amber-200" v-if="expiringCount">即将到期 {{ expiringCount }}</span>
        <span class="px-2 py-0.5 rounded bg-red-50 text-red-600 text-xs border border-red-200" v-if="expiredCount">已过期 {{ expiredCount }}</span>
      </h1>
      <div class="flex items-center gap-2 flex-wrap text-xs">
        <button class="px-3 h-8 rounded bg-white border border-gray-300 hover:bg-gray-50" @click="load">刷新</button>
        <button class="px-3 h-8 rounded bg-white border border-gray-300 hover:bg-gray-50" @click="exportCsv" :disabled="!filtered.length">导出全部</button>
        <button class="px-3 h-8 rounded bg-white border border-gray-300 hover:bg-gray-50" @click="exportSelected" :disabled="!selectedIds.length">导出选中</button>
        <button class="px-3 h-8 rounded bg-white border border-gray-300 hover:bg-gray-50" @click="copySelected" :disabled="!selectedIds.length">复制选中ID</button>
        <button class="px-3 h-8 rounded bg-white border border-gray-300 hover:bg-gray-50" @click="resetFilters">重置</button>
        <button class="px-3 h-8 rounded bg-gray-600 text-white" @click="()=>router.push('/admin')">返回仪表盘</button>
      </div>
    </div>

    <div class="flex flex-wrap gap-3 mb-4 text-xs">
      <button class="px-2.5 h-7 rounded border bg-white hover:bg-gray-50" @click="quickFilter('')">全部</button>
      <button class="px-2.5 h-7 rounded border bg-white hover:bg-gray-50" @click="quickFilter('expiring')">仅即将到期 ({{ expiringCount }})</button>
      <button class="px-2.5 h-7 rounded border bg-white hover:bg-gray-50" @click="quickFilter('expired')">仅已过期 ({{ expiredCount }})</button>
      <button class="px-2.5 h-7 rounded border bg-white hover:bg-gray-50" @click="goStudentFiltered('expiring')">跳转学生(即将)</button>
      <button class="px-2.5 h-7 rounded border bg-white hover:bg-gray-50" @click="goStudentFiltered('expired')">跳转学生(过期)</button>
      <div class="flex items-center gap-1 ml-auto">
        <span class="text-gray-500">快速天数:</span>
        <button class="px-2 h-7 rounded border bg-white hover:bg-gray-50" @click="quickDays(1)">+1</button>
        <button class="px-2 h-7 rounded border bg-white hover:bg-gray-50" @click="quickDays(3)">+3</button>
        <button class="px-2 h-7 rounded border bg-white hover:bg-gray-50" @click="quickDays(7)">+7</button>
      </div>
    </div>

    <!-- 批量选择条 -->
    <div v-if="selectedIds.length" class="mb-4 flex items-center gap-3 bg-indigo-50 border border-indigo-200 text-indigo-700 rounded px-4 py-2 text-xs">
      <span>已选 {{ selectedIds.length }} 个用户</span>
      <button class="px-2 h-7 rounded bg-white border border-indigo-300 hover:bg-indigo-100" @click="exportSelected">导出选中</button>
      <button class="px-2 h-7 rounded bg-white border border-indigo-300 hover:bg-indigo-100" @click="copySelected">复制ID</button>
      <button class="px-2 h-7 rounded bg-white border border-indigo-300 hover:bg-indigo-100" @click="clearSelection">清空</button>
    </div>

    <div class="bg-white rounded shadow p-4 mb-6">
      <div class="grid gap-4 md:grid-cols-5 text-sm">
        <div>
          <label class="block text-gray-600 mb-1 text-xs">天数范围</label>
          <div class="flex items-center gap-2">
            <input v-model.number="days" type="number" min="1" class="w-24 h-9 border rounded px-2" />
            <span class="text-xs text-gray-400">内即将到期</span>
          </div>
        </div>
        <div>
          <label class="block text-gray-600 mb-1 text-xs">状态</label>
          <select v-model="statusFilter" class="w-full h-9 border rounded px-2">
            <option value="">全部</option>
            <option value="expiring">即将到期</option>
            <option value="expired">已过期</option>
          </select>
        </div>
        <div>
          <label class="block text-gray-600 mb-1 text-xs">搜索</label>
          <input v-model="search" type="text" placeholder="用户ID/用户名" class="w-full h-9 border rounded px-2" />
        </div>
        <div>
          <label class="block text-gray-600 mb-1 text-xs">排序字段</label>
          <select v-model="sortField" class="w-full h-9 border rounded px-2">
            <option value="days_left">剩余天数</option>
            <option value="expires_at">到期时间</option>
          </select>
        </div>
        <div>
          <label class="block text-gray-600 mb-1 text-xs">排序方向</label>
          <select v-model="sortDir" class="w-full h-9 border rounded px-2">
            <option value="asc">升序</option>
            <option value="desc">降序</option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="errorMsg" class="mb-4 px-4 py-2 rounded bg-red-50 border border-red-200 text-red-600 text-sm">{{ errorMsg }}</div>

    <!-- 表格 -->
    <div class="bg-white rounded shadow overflow-auto">
      <table class="min-w-[900px] w-full text-xs">
        <thead>
          <tr class="bg-gray-50 text-gray-600">
            <th class="py-2 px-2 text-center w-10"><input type="checkbox" :checked="allChecked" @change="toggleAll" /></th>
            <th class="py-2 px-3 text-left">用户ID</th>
            <th class="py-2 px-3 text-left">用户名</th>
            <th class="py-2 px-3 text-left">状态</th>
            <th class="py-2 px-3 text-left">到期时间</th>
            <th class="py-2 px-3 text-left">剩余天数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="py-8 text-center text-gray-400">加载中...</td></tr>
          <tr v-for="it in pageData" :key="it.user_id" class="border-t hover:bg-gray-50">
            <td class="py-2 px-2 text-center"><input type="checkbox" :checked="selectedIds.includes(it.user_id)" @change="toggleOne(it.user_id)" /></td>
            <td class="py-2 px-3">{{ it.user_id }}</td>
            <td class="py-2 px-3">{{ it.username }}</td>
            <td class="py-2 px-3">
              <span :class="{
                'px-2 py-0.5 rounded-full text-[10px] bg-amber-50 text-amber-700 border border-amber-200': it.state==='expiring',
                'px-2 py-0.5 rounded-full text-[10px] bg-red-50 text-red-600 border border-red-200': it.state==='expired'
              }">{{ it.state==='expiring' ? '即将到期' : '已过期' }}</span>
            </td>
            <td class="py-2 px-3">{{ it.expires_at || '—' }}</td>
            <td class="py-2 px-3">{{ it.days_left!=null ? it.days_left : (it.state==='expired'?0:'—') }}</td>
          </tr>
          <tr v-if="!loading && !pageData.length"><td colspan="6" class="py-10 text-center text-gray-400">暂无数据</td></tr>
        </tbody>
      </table>
    </div>
    <div class="flex items-center justify-between mt-4 text-xs" v-if="!loading && pageCount>1">
      <div>共 {{ total }} 条，页数 {{ page }} / {{ pageCount }}</div>
      <div class="flex items-center gap-2">
        <button class="px-3 h-8 rounded border bg-white disabled:opacity-40" :disabled="page===1" @click="prev">上一页</button>
        <button class="px-3 h-8 rounded border bg-white disabled:opacity-40" :disabled="page===pageCount" @click="next">下一页</button>
        <select v-model.number="pageSize" class="h-8 border rounded px-2">
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>
    </div>

    <!-- Add bottom action bar for convenience -->
    <div class="flex items-center justify-between mt-8 text-xs border-t pt-4" v-if="!loading">
      <div class="text-gray-500">快速操作：
        <button class="ml-2 px-3 h-8 rounded border bg-white hover:bg-gray-50" @click="()=>router.push('/admin')">返回仪表盘</button>
        <button class="ml-2 px-3 h-8 rounded border bg-white hover:bg-gray-50" @click="resetFilters">重置筛选</button>
      </div>
      <div>
        <span class="text-gray-400">已选 {{ selectedIds.length }} 条</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
