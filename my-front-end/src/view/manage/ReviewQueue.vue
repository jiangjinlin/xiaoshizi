<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiManageReviewQueue, apiManageQuestionBulkMarkReviewed, apiManageReviewConsensus, apiManageReviewConsensusSave } from '../../api/index'

const router = useRouter()
const loading = ref(false)
const errorMsg = ref('')
const items = ref([])
const stats = ref({ total: 0, missing_kp: 0, missing_primary: 0, missing_analysis: 0, unreviewed: 0 })

// 筛选项
const filters = ref({
  missing_only: true,
  batch: '',
  types: { '单选': true, '多选': true, '判断': true, '操作': true, 'Office操作': true },
})

// 共识阈值（3~50）
const consensusThreshold = ref(null)
const thLoading = ref(false)
const thMsg = ref('')
async function loadThreshold(){
  try{ const { data } = await apiManageReviewConsensus(); if(data?.success){ consensusThreshold.value = Number(data.threshold) } }
  catch{}
}
async function saveThreshold(){
  const v = Number(consensusThreshold.value)
  if (!Number.isFinite(v) || v < 3 || v > 50){ alert('阈值需在 3~50 之间'); return }
  thLoading.value = true
  thMsg.value = ''
  try{
    const { data } = await apiManageReviewConsensusSave(v)
    if (data?.success){ thMsg.value = '已保存'; setTimeout(()=> thMsg.value='', 1500) }
    else { thMsg.value = data?.error_msg || '保存失败' }
  }catch{ thMsg.value = '保存失败' } finally { thLoading.value = false }
}

// 批量选择
const selecting = ref(false)
const selectedIds = ref(new Set())
function toggleSelectMode(){ selecting.value = !selecting.value; if(!selecting.value) selectedIds.value = new Set() }
function toggleOne(id){ if(selectedIds.value.has(id)) selectedIds.value.delete(id); else selectedIds.value.add(id) }
function isChecked(id){ return selectedIds.value.has(id) }
function selectAll(){ items.value.forEach(q=> selectedIds.value.add(q.id)) }
function clearSelect(){ selectedIds.value.clear() }

function buildParams(){
  const p = { limit: 200 }
  if (filters.value.missing_only) p.missing_only = 1
  if (String(filters.value.batch || '').trim()) p.batch = String(filters.value.batch).trim()
  const t = Object.keys(filters.value.types).filter(k => filters.value.types[k])
  if (t.length && t.length < Object.keys(filters.value.types).length) p.types = t.join(',')
  return p
}

async function fetchList(){
  loading.value = true
  errorMsg.value = ''
  try{
    const params = buildParams()
    const { data } = await apiManageReviewQueue(params)
    if (data?.success){
      items.value = data.items || []
      stats.value = data.stats || stats.value
      // 移除已不在结果集的选择
      const valid = new Set((items.value||[]).map(x=>x.id))
      for (const id of Array.from(selectedIds.value)) if(!valid.has(id)) selectedIds.value.delete(id)
    } else {
      errorMsg.value = data?.error_msg || '加载失败'
    }
  }catch{ errorMsg.value = '网络错误' } finally { loading.value = false }
}

async function bulkMark(reviewedFlag=true){
  if(!selectedIds.value.size){ alert('请先勾选题目'); return }
  const tip = reviewedFlag ? '标记为已审核' : '标记为未审核'
  if(!confirm(`确定将所选 ${selectedIds.value.size} 题${tip}？`)) return
  try{
    const { data } = await apiManageQuestionBulkMarkReviewed(Array.from(selectedIds.value), reviewedFlag)
    if (data?.success){
      alert(`${tip} 成功 ${data.changed||0} 条`)
      selectedIds.value.clear()
      await fetchList()
    } else {
      alert(data?.error_msg || `${tip} 失败`)
    }
  }catch{ alert('网络错误，操作失败') }
}

async function markOneReviewed(id){
  try{
    const { data } = await apiManageQuestionBulkMarkReviewed([id], true)
    if (data?.success){ await fetchList() } else { alert(data?.error_msg || '操作失败') }
  }catch{ alert('网络错误，操作失败') }
}

function goEdit(qid){ router.push(`/manage/questions/edit/${qid}`) }
function backHome(){ router.push('/teacher') }

onMounted(async ()=>{ await Promise.all([fetchList(), loadThreshold()]) })
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
      <h1 class="text-2xl font-bold">待审核题目</h1>
      <div class="flex items-center gap-2 text-xs">
        <span class="px-2 py-1 rounded bg-amber-50 text-amber-700 border border-amber-200">总计：{{ stats.total }}</span>
        <span class="px-2 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200" title="考纲大类为空">考纲空：{{ stats.missing_kp }}</span>
        <span class="px-2 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200" title="一级知识点为空">一级空：{{ stats.missing_primary }}</span>
        <span class="px-2 py-1 rounded bg-teal-50 text-teal-700 border border-teal-200" title="解析为空">解析空：{{ stats.missing_analysis }}</span>
        <span class="px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200" title="未标记审核">未审：{{ stats.unreviewed }}</span>
      </div>
    </div>

    <div class="bg-white rounded shadow p-4 mb-4 text-sm flex flex-wrap items-center gap-3">
      <label class="inline-flex items-center gap-2">
        <input type="checkbox" v-model="filters.missing_only" /> 仅显示缺失/未审
      </label>
      <div class="flex items-center gap-2">
        <span>批次</span>
        <input v-model="filters.batch" placeholder="如 1" class="h-9 border border-gray-300 rounded px-3 text-sm bg-white w-28" />
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <span>题型</span>
        <label v-for="(v,k) in filters.types" :key="k" class="inline-flex items-center gap-2 mr-2">
          <input type="checkbox" v-model="filters.types[k]" /> {{ k }}
        </label>
      </div>
      <!-- 新增：共识阈值设置 -->
      <div class="flex items-center gap-2">
        <span>共识阈值</span>
        <input type="number" min="3" max="50" v-model.number="consensusThreshold" class="h-9 w-20 border border-gray-300 rounded px-2 text-sm bg-white"/>
        <button class="h-9 px-3 rounded bg-gray-800 text-white text-xs disabled:opacity-50" :disabled="thLoading" @click="saveThreshold">{{ thLoading? '保存中...' : '保存' }}</button>
        <span v-if="thMsg" class="text-[11px] text-emerald-600">{{ thMsg }}</span>
      </div>
      <div class="ml-auto flex items-center gap-2">
        <button class="h-9 px-3 rounded bg-primary text-white text-xs" @click="fetchList">应用</button>
        <button class="h-9 px-3 rounded border text-xs bg-white hover:bg-gray-50" @click="backHome">返回</button>
      </div>
    </div>

    <div class="bg-white rounded shadow p-4 mb-4 text-xs flex flex-wrap items-center gap-2">
      <button class="px-3 h-8 rounded bg-amber-600 text-white" @click="toggleSelectMode">{{ selecting ? '退出多选' : '批量操作' }}</button>
      <template v-if="selecting">
        <button class="px-3 h-8 rounded bg-emerald-600 text-white" @click="bulkMark(true)">标记已审核</button>
        <button class="px-3 h-8 rounded bg-rose-600 text-white" @click="bulkMark(false)">标记未审核</button>
        <button class="px-3 h-8 rounded bg-gray-200 text-gray-700" @click="selectAll">本页全选</button>
        <button class="px-3 h-8 rounded bg-gray-200 text-gray-700" @click="clearSelect">清空</button>
      </template>
      <span class="ml-auto text-[11px] text-gray-400" v-if="selecting">已选 {{ selectedIds.size }} 条</span>
    </div>

    <div v-if="errorMsg" class="text-red-600 mb-3">{{ errorMsg }}</div>

    <div class="overflow-x-auto bg-white rounded shadow">
      <table class="min-w-[1040px] w-full text-sm">
        <thead>
          <tr class="bg-primary/5 text-gray-700 text-left">
            <th v-if="selecting" class="py-3 px-2 w-8">选</th>
            <th class="py-3 px-4">题目ID</th>
            <th class="py-3 px-4">题型</th>
            <th class="py-3 px-4">内容</th>
            <th class="py-3 px-4">批次</th>
            <th class="py-3 px-4">原因</th>
            <th class="py-3 px-4 text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="q in items" :key="q.id" class="border-t hover:bg-gray-50">
            <td v-if="selecting" class="py-3 px-2"><input type="checkbox" :checked="isChecked(q.id)" @change="toggleOne(q.id)"/></td>
            <td class="py-3 px-4">{{ q.id }}</td>
            <td class="py-3 px-4">{{ q.question_type }}</td>
            <td class="py-3 px-4" :title="q.content">{{ (q.content||'').slice(0,80) }}{{ (q.content||'').length>80?'…':'' }}</td>
            <td class="py-3 px-4">{{ q.batch ?? '-' }}</td>
            <td class="py-3 px-4">
              <div class="flex flex-wrap gap-1">
                <span v-for="r in (q.reasons||[])" :key="r" class="text-[11px] px-2 py-0.5 rounded border" :class="{
                  'bg-amber-50 text-amber-700 border-amber-200': r.includes('考纲'),
                  'bg-indigo-50 text-indigo-700 border-indigo-200': r.includes('一级'),
                  'bg-teal-50 text-teal-700 border-teal-200': r.includes('解析'),
                  'bg-rose-50 text-rose-700 border-rose-200': r.includes('未审核'),
                }">{{ r }}</span>
              </div>
            </td>
            <td class="py-3 px-4 text-center">
              <div class="inline-flex items-center gap-3">
                <button class="text-blue-600 hover:underline" @click="goEdit(q.id)">编辑</button>
                <button class="text-emerald-600 hover:underline" @click="markOneReviewed(q.id)">标记已审核</button>
              </div>
            </td>
          </tr>
          <tr v-if="!items.length && !loading"><td :colspan="selecting?7:6" class="py-8 text-center text-gray-400">暂无待处理题目</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
</style>
