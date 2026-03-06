<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiManageQuestionDelete, apiManageQuestionExport, apiManageQuestionBulkDelete, apiQuestionImport, apiManageQuestionTemplate, apiManageQuestionBulkMarkReviewed } from '../../api/index'
import { useQuestionBank } from '../../composables/useQuestionBank'
// 新增：批次相关API
import { apiManageBatchStats, apiManageBatchCreate } from '../../api/index'

const router = useRouter()
// 使用组合式
const {
  loading, errorMsg, questions, questionCount, typeCounts, knowledgeOptions, primaryOptions,
  filter, page, pageSize, pageCount, pageData, fetchList, resetFilter, pendingCount
} = useQuestionBank({ enableFilterCache: true })

// 选择/批量逻辑保留
const selecting = ref(false)
const selectedIds = ref(new Set())
const excelFile = ref(null)
// 新增：批次统计与创建的状态
const batchStats = ref([])
const batchStatsLoading = ref(false)
const batchStatsMsg = ref('')
const newBatchNo = ref('')  // 为空表示自动分配
const newBatchMode = ref('move') // move|copy
const newBatchMsg = ref('')
const newBatchLoading = ref(false)

async function loadBatchStats(){
  batchStatsLoading.value = true; batchStatsMsg.value=''
  try{
    const { data } = await apiManageBatchStats({})
    if(data?.success){ batchStats.value = data.batches || [] } else { batchStats.value = []; batchStatsMsg.value = data?.error_msg || '加载失败' }
  }catch{ batchStats.value = []; batchStatsMsg.value = '网络错误' } finally { batchStatsLoading.value = false }
}

async function createNewBatch(){
  if(!selectedIds.value.size){ alert('请先在列表中勾选需要归入新批次的题目'); return }
  const ids = Array.from(selectedIds.value)
  const payload = { question_ids: ids, mode: newBatchMode.value }
  const s = String(newBatchNo.value||'').trim()
  if(s){
    const n = parseInt(s, 10)
    if(!Number.isFinite(n) || n<=0){ alert('批次号需为正整数，或留空自动分配'); return }
    payload.batch = n
  }
  if(!confirm(`确定将所选 ${ids.length} 题${newBatchMode.value==='move'?'移动到':'复制到'}${s?('批次 '+s):'“新批次”'}？`)) return
  newBatchLoading.value = true; newBatchMsg.value=''
  try{
    const { data } = await apiManageBatchCreate(payload)
    if(data?.success){
      newBatchMsg.value = `已${newBatchMode.value==='move'?'移动':'复制'}：批次 ${data.batch}，更新 ${data.updated||0}，复制 ${data.copied||0}`
      // 操作后刷新列表与批次统计，并清空选择
      await fetchList(); selectedIds.value.clear(); await loadBatchStats()
    } else {
      newBatchMsg.value = data?.error_msg || '操作失败'
    }
  }catch{ newBatchMsg.value = '网络错误，操作失败' } finally { newBatchLoading.value = false }
}

async function addQuestion(){ router.push('/manage/questions/new') }
function editQuestion(id){ router.push(`/manage/questions/edit/${id}`) }
async function deleteQuestion(id){
  if(!confirm('确定删除该题目吗？')) return
  try { const { data } = await apiManageQuestionDelete(id); if(data?.success){ await fetchList(); pruneSelection() } else alert(data?.error_msg||'删除失败') } catch { alert('网络错误，删除失败') }
}
async function bulkDelete(){
  if(!selectedIds.value.size){ alert('请先勾选题目'); return }
  if(!confirm(`确定批量删除 ${selectedIds.value.size} 条题目?`)) return
  try { const { data } = await apiManageQuestionBulkDelete(Array.from(selectedIds.value)); if(data?.success){ alert(`删除成功 ${data.deleted} 条`); await fetchList(); selectedIds.value.clear() } else alert(data?.error_msg||'操作失败') } catch { alert('网络错误，操作失败') }
}

async function bulkMark(reviewedFlag=true){
  if(!selectedIds.value.size){ alert('请先勾选题目'); return }
  const tip = reviewedFlag ? '标记为已审核' : '标记为未审核'
  if(!confirm(`确定将所选 ${selectedIds.value.size} 题${tip}？`)) return
  try {
    const { data } = await apiManageQuestionBulkMarkReviewed(Array.from(selectedIds.value), reviewedFlag)
    if(data?.success){
      alert(`${tip} 成功 ${data.changed||0} 条`)
      await fetchList(); pruneSelection()
    } else {
      alert(data?.error_msg || `${tip} 失败`)
    }
  } catch { alert('网络错误，操作失败') }
}

async function onImport(){
  if(!excelFile.value?.files?.length){ alert('请选择Excel文件'); return }
  const fd = new FormData(); fd.append('excel_file', excelFile.value.files[0])
  try { const { data } = await apiQuestionImport(fd); if(data?.success){ alert(data?.message||'导入成功'); excelFile.value.value=''; await fetchList(); pruneSelection() } else alert(data?.error_msg||'导入失败') } catch { alert('网络错误，导入失败') }
}
async function downloadTemplate(){
  try { const res = await apiManageQuestionTemplate(); const blob = new Blob([res.data], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='question_import_template.xlsx'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url) } catch { alert('模板下载失败') }
}

async function doExport(params={}, suffix='all'){
  try { const res = await apiManageQuestionExport(params); const blob = new Blob([res.data], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); const ts=new Date().toISOString().replace(/[-:T.Z]/g,'').slice(0,14); a.href=url; a.download=`questions_${suffix}_${ts}.xlsx`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url) } catch { alert('导出失败') }
}
function exportAll(){ doExport({}, 'all') }
function exportFiltered(){
  const params = {}
  if (filter.value.types.length) params.types = filter.value.types.join(',')
  if (filter.value.batch) params.batch = filter.value.batch
  if (filter.value.knowledge) params.knowledge = filter.value.knowledge
  if (filter.value.primary) params.primary = filter.value.primary
  if (filter.value.keyword) params.keyword = filter.value.keyword
  if (filter.value.unreviewedOnly) params.reviewed = 0
  doExport(params, 'filtered')
}

function onSearch(){ page.value = 1; fetchList().then(pruneSelection) }
function onReset(){ resetFilter(); pruneSelection() }

function goSimple(){ router.push('/manage/questions') }

async function bulkDeleteByType(qType='操作') {
  if (loading.value) return
  // 临时基于现有筛选调用：只取该题型
  const want = questions.value.filter(q => q.question_type === qType).map(q => q.id)
  if (!want.length) { alert(`当前结果中无 ${qType} 题可删`); return }
  if (!confirm(`确定批量删除当前结果中全部 ${qType} 题 (${want.length} 条) ?`)) return
  try {
    const { data } = await apiManageQuestionBulkDelete(want)
    if (data?.success) { alert(`删除成功 ${data.deleted} 条 ${qType} 题`); await fetchList(); selectedIds.value.clear() } else { alert(data?.error_msg || '批量删除失败') }
  } catch { alert('网络错误，批量删除失败') }
}

onMounted(async ()=>{ await fetchList(); pruneSelection(); await loadBatchStats() })
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- 标题与返回 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-xl font-semibold">题库高级筛选</h1>
      <div class="flex flex-wrap gap-2 md:gap-3 items-center">
        <span class="text-xs text-amber-600 bg-amber-50 border border-amber-200 px-2 py-1 rounded" title="未审核题数">未审：{{ pendingCount }}</span>
        <button class="bg-blue-600 text-white px-4 py-2 rounded" @click="addQuestion">新增题目</button>
        <button class="bg-gray-600 text-white px-4 py-2 rounded" @click="goSimple">返回简洁列表</button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="bg-white rounded shadow p-4 space-y-4">
      <div class="grid gap-4 md:grid-cols-5">
        <div class="md:col-span-2 space-y-2">
          <label class="block text-gray-600 text-xs font-medium">题型(多选)</label>
          <div class="flex flex-wrap gap-2">
            <label v-for="t in Object.keys(typeCounts)" :key="t" class="flex items-center gap-1 border px-2 py-1 rounded text-xs cursor-pointer bg-gray-50 hover:bg-gray-100">
              <input type="checkbox" :value="t" v-model="filter.types" class="scale-90" /> {{ t }}
            </label>
          </div>
        </div>
        <div class="space-y-2">
          <label class="block text-gray-600 text-xs font-medium">批次</label>
          <input v-model="filter.batch" type="number" class="w-full md:w-40 border rounded px-2 py-1 text-sm"/>
        </div>
        <div class="space-y-2">
          <label class="block text-gray-600 text-xs font-medium">知识点</label>
          <select v-model="filter.knowledge" class="w-full md:w-44 border rounded px-2 py-1 text-sm">
            <option value="">全部</option>
            <option v-for="k in knowledgeOptions" :key="k" :value="k">{{ k }}</option>
          </select>
        </div>
        <div class="space-y-2">
          <label class="block text-gray-600 text-xs font-medium">一级知识点</label>
          <select v-model="filter.primary" class="w-full md:w-44 border rounded px-2 py-1 text-sm">
            <option value="">全部</option>
            <option v-for="k in primaryOptions" :key="k" :value="k">{{ k }}</option>
          </select>
        </div>
      </div>
      <div class="flex flex-col md:flex-row md:items-end gap-4">
        <div class="flex-1 min-w-[220px]">
          <label class="block text-gray-600 text-xs font-medium">关键字(题干)</label>
          <input v-model="filter.keyword" type="text" class="w-full border rounded px-2 py-1 text-sm" />
        </div>
        <label class="text-sm flex items-center gap-2 border px-3 py-2 rounded bg-white/80">
          <input type="checkbox" v-model="filter.unreviewedOnly" /> 只看未审核
        </label>
        <div class="flex gap-2 flex-wrap">
          <button class="bg-blue-600 text-white px-4 py-2 rounded text-sm" @click="onSearch">查询</button>
          <button class="bg-gray-300 text-gray-700 px-4 py-2 rounded text-sm" @click="onReset">重置</button>
        </div>
      </div>
    </div>

    <!-- 汇总与操作 -->
    <div class="bg-white rounded shadow p-4 flex flex-col gap-4">
      <div class="flex flex-wrap items-center gap-4">
        <div>题目：<span class="text-blue-600 font-semibold">{{ questionCount }}</span></div>
        <div class="text-xs text-gray-500 flex flex-wrap gap-3">
          <span v-for="(v,k) in typeCounts" :key="k">{{ k }}: {{ v }}</span>
        </div>
        <div class="flex items-center gap-2 ml-auto flex-wrap">
          <input ref="excelFile" type="file" accept=".xls,.xlsx" class="border px-2 py-1 rounded text-xs" />
          <button class="bg-green-600 text-white px-3 py-2 rounded text-xs" @click="onImport">导入</button>
          <button class="bg-gray-600 text-white px-3 py-2 rounded text-xs" @click="downloadTemplate">模板</button>
          <button class="bg-indigo-600 text-white px-3 py-2 rounded text-xs" @click="exportAll">导出全部</button>
          <button class="bg-indigo-500 text-white px-3 py-2 rounded text-xs" @click="exportFiltered">按筛选导出</button>
          <button class="bg-amber-600 text-white px-3 py-2 rounded text-xs" @click="toggleSelectMode">{{ selecting? '退出多选':'批量操作' }}</button>
          <button v-if="selecting" class="bg-emerald-600 text-white px-3 py-2 rounded text-xs" @click="bulkMark(true)">标记已审核</button>
          <button v-if="selecting" class="bg-rose-600 text-white px-3 py-2 rounded text-xs" @click="bulkMark(false)">标记未审核</button>
          <button v-if="selecting" class="bg-red-600 text-white px-3 py-2 rounded text-xs" @click="bulkDelete">删所选</button>
          <button v-if="selecting" class="bg-rose-600 text-white px-3 py-2 rounded text-xs" @click="bulkDeleteByType('操作')">删全部操作题</button>
          <button v-if="selecting" class="bg-gray-300 px-3 py-2 rounded text-xs" @click="selectAll">本页全选</button>
          <button v-if="selecting" class="bg-gray-300 px-3 py-2 rounded text-xs" @click="clearSelect">清空</button>
        </div>
      </div>
      <div class="text-[11px] text-gray-400">提示：可以先用“只看未审核”筛选，再批量标记为已审核。</div>
    </div>

    <!-- 新增：批次统计与新批次创建 -->
    <div class="bg-white rounded shadow p-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-gray-800">批次统计</h2>
        <button class="px-3 h-8 rounded bg-white border border-gray-300 text-xs hover:bg-gray-50" @click="loadBatchStats">刷新</button>
      </div>
      <div v-if="batchStatsLoading" class="text-xs text-gray-500 py-2">加载中...</div>
      <div v-else>
        <div v-if="batchStatsMsg" class="text-xs text-rose-600 py-2">{{ batchStatsMsg }}</div>
        <div class="overflow-x-auto">
          <table class="min-w-[520px] w-full text-xs">
            <thead>
              <tr class="bg-gray-50 text-gray-600">
                <th class="py-2 px-3 text-left w-24">批次</th>
                <th class="py-2 px-3 text-left w-32">题目数量</th>
                <th class="py-2 px-3 text-left w-32">总分</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in batchStats" :key="b.batch" class="border-t hover:bg-gray-50">
                <td class="py-2 px-3">{{ b.batch }}</td>
                <td class="py-2 px-3">{{ b.question_count }}</td>
                <td class="py-2 px-3">{{ b.total_score }}</td>
              </tr>
              <tr v-if="!batchStats.length"><td colspan="3" class="py-6 text-center text-gray-400">暂无数据</td></tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="mt-5 border-t pt-4">
        <h3 class="text-sm font-semibold text-gray-800 mb-2">新建批次（基于所选题目）</h3>
        <div class="flex flex-wrap items-center gap-3 text-xs">
          <label class="inline-flex items-center gap-2">
            <span>批次号</span>
            <input v-model="newBatchNo" placeholder="留空自动分配" class="h-8 w-32 border rounded px-2" />
          </label>
          <label class="inline-flex items-center gap-2">
            <input type="radio" value="move" v-model="newBatchMode" /> 移动
          </label>
          <label class="inline-flex items-center gap-2">
            <input type="radio" value="copy" v-model="newBatchMode" /> 复制
          </label>
          <button class="h-8 px-3 rounded bg-indigo-600 text-white disabled:opacity-50" :disabled="newBatchLoading" @click="createNewBatch">{{ newBatchLoading? '处理中...' : '执行' }}</button>
          <span class="text-[11px] text-gray-500">已选 {{ selectedIds.size }} 题</span>
          <span v-if="newBatchMsg" class="text-[11px] text-emerald-600">{{ newBatchMsg }}</span>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="text-red-600 text-sm">{{ errorMsg }}</div>

    <!-- 列表 -->
    <div class="overflow-x-auto bg-white rounded shadow">
      <table class="min-w-[1000px] w-full text-sm">
        <thead>
          <tr class="bg-blue-50 text-blue-700 text-left">
            <th v-if="selecting" class="py-3 px-2 w-8">选</th>
            <th class="py-3 px-4">ID</th>
            <th class="py-3 px-4">题型</th>
            <th class="py-3 px-4">内容</th>
            <th class="py-3 px-4">分数</th>
            <th class="py-3 px-4">批次</th>
            <th class="py-3 px-4">审核</th>
            <th class="py-3 px-4">知识点</th>
            <th class="py-3 px-4">一级知识点</th>
            <th class="py-3 px-4 text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="q in pageData" :key="q.id" class="border-t hover:bg-gray-50">
            <td v-if="selecting" class="py-3 px-2"><input type="checkbox" :checked="isChecked(q.id)" @change="toggleOne(q.id)"/></td>
            <td class="py-3 px-4">{{ q.id }}</td>
            <td class="py-3 px-4">{{ q.question_type }}</td>
            <td class="py-3 px-4" :title="q.content">{{ (q.content||'').slice(0,32) }}{{ (q.content||'').length>32?'…':'' }}</td>
            <td class="py-3 px-4">{{ q.score }}</td>
            <td class="py-3 px-4">{{ q.batch }}</td>
            <td class="py-3 px-4">
              <span v-if="q.reviewed" class="text-[11px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">已审核</span>
              <span v-else class="text-[11px] px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">未审核</span>
            </td>
            <td class="py-3 px-4">{{ q.knowledge_points }}</td>
            <td class="py-3 px-4">{{ q.primary_knowledge }}</td>
            <td class="py-3 px-4">
              <div class="flex flex-wrap justify-center gap-2">
                <button class="text-blue-600" @click="editQuestion(q.id)">编辑</button>
                <button class="text-red-600" v-if="!selecting" @click="deleteQuestion(q.id)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="!pageData.length && !loading"><td :colspan="selecting?11:10" class="py-6 text-center text-gray-400">暂无数据</td></tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 text-xs">
      <div class="flex items-center gap-2">页大小
        <select v-model.number="pageSize" class="border rounded px-2 py-1" @change="page=1">
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
        <span> 第 {{ page }} / {{ pageCount }} 页 （共 {{ questionCount }} 条）</span>
      </div>
      <div class="flex items-center gap-2">
        <button class="px-3 py-1 border rounded" :disabled="page===1" @click="page=1">首页</button>
        <button class="px-3 py-1 border rounded" :disabled="page===1" @click="page=page-1">上一页</button>
        <button class="px-3 py-1 border rounded" :disabled="page===pageCount" @click="page=page+1">下一页</button>
        <button class="px-3 py-1 border rounded" :disabled="page===pageCount" @click="page=pageCount">末页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
