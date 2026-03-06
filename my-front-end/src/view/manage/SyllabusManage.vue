<template>
  <div class="min-h-screen flex bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <div class="flex-1 pt-16 pb-10 px-6 lg:px-8">
      <header class="sticky top-0 z-10 -mx-6 px-6 py-3 bg-white/70 backdrop-blur border-b border-gray-200 flex items-center justify-between">
        <h1 class="text-lg font-semibold text-gray-800">考纲管理</h1>
        <div class="flex items-center gap-2 text-xs text-gray-500">
          <span>管理省份/专业下的考纲大类与一级知识点条目；支持导入/编辑/删除。</span>
        </div>
      </header>

      <section class="mt-6 rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 shadow-sm">
        <div class="grid md:grid-cols-3 gap-3">
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-700 whitespace-nowrap">省份</label>
            <select v-model="state.province" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm min-w-[160px]">
              <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
            </select>
            <input v-if="!provinces.length" v-model="state.province" placeholder="如 四川省" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm"/>
          </div>
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-700 whitespace-nowrap">专业</label>
            <select v-model="state.major" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm min-w-[160px]">
              <option v-for="m in majorOptions" :key="m" :value="m">{{ m }}</option>
            </select>
            <input v-if="!majorOptions.length" v-model="state.major" placeholder="如 计算机类" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm"/>
          </div>
          <div class="flex items-center gap-2 justify-end">
            <button class="h-9 px-3 rounded bg-primary text-white text-xs" @click="openImport">一键导入</button>
            <button class="h-9 px-3 rounded bg-white border text-xs" :disabled="!state.province||!state.major" @click="clearAll">清空本专业</button>
          </div>
        </div>
        <div class="mt-4 flex flex-wrap items-center gap-3 text-sm">
          <div class="flex items-center gap-2">
            <span class="text-gray-600">大类</span>
            <div class="flex flex-wrap gap-2">
              <button class="px-2 py-1 rounded-full border text-xs" :class="!filters.kp ? 'bg-primary/10 text-primary border-primary/30' : 'bg-white text-gray-700 border-gray-300'" @click="setKP('')">全部</button>
              <button v-for="k in kpList" :key="k" class="px-2 py-1 rounded-full border text-xs" :class="filters.kp===k ? 'bg-primary/10 text-primary border-primary/30' : 'bg-white text-gray-700 border-gray-300'" @click="setKP(k)">{{ k }}<span class="ml-1 text-[10px] text-gray-500">{{ kpCounts[k]||0 }}</span></button>
            </div>
          </div>
          <div class="ml-auto flex items-center gap-2">
            <input v-model="filters.keyword" @keyup.enter="loadList" placeholder="搜索一级知识点" class="h-9 px-3 rounded border border-gray-300 bg-white text-sm w-56"/>
            <select v-model.number="state.pageSize" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
            <button class="h-9 px-3 rounded bg-white border text-xs" @click="loadList">刷新</button>
          </div>
        </div>
      </section>

      <section class="mt-6 rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 shadow-sm">
        <div class="mb-3 text-sm font-semibold text-gray-700">新增条目</div>
        <div class="grid md:grid-cols-3 gap-3">
          <input v-model.trim="createForm.kp" placeholder="考纲大类（如 计算机基础）" class="h-10 px-3 rounded border border-gray-300 bg-white text-sm"/>
          <input v-model.trim="createForm.primary" placeholder="一级知识点条目" class="h-10 px-3 rounded border border-gray-300 bg-white text-sm"/>
          <div class="flex items-center gap-2">
            <button class="h-10 px-4 rounded bg-primary text-white text-xs" :disabled="!canCreate" @click="createItem">保存</button>
            <button v-if="filters.kp" class="h-10 px-3 rounded bg-white border text-xs" @click="clearByKP(filters.kp)">清空该大类</button>
          </div>
        </div>
      </section>

      <section class="mt-6 rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-2 shadow-sm">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-primary/5 text-gray-600">
              <th class="py-2 px-3 text-left">考纲大类</th>
              <th class="py-2 px-3 text-left">一级知识点</th>
              <th class="py-2 px-3 text-left w-36">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="it in items" :key="it.id" class="hover:bg-primary/5">
              <td class="py-2 px-3"><input v-model="it.kp" class="w-full px-2 py-1 rounded border border-gray-300 bg-white text-sm"/></td>
              <td class="py-2 px-3"><input v-model="it.primary" class="w-full px-2 py-1 rounded border border-gray-300 bg-white text-sm"/></td>
              <td class="py-2 px-3 flex items-center gap-2">
                <button class="h-8 px-3 rounded bg-white border text-xs" @click="saveItem(it)">保存</button>
                <button class="h-8 px-3 rounded bg-white border text-xs" @click="deleteItem(it)">删除</button>
              </td>
            </tr>
            <tr v-if="!items.length"><td colspan="3" class="py-8 text-center text-gray-400">暂无数据</td></tr>
          </tbody>
        </table>
        <div class="p-3 flex items-center justify-end gap-2 text-sm">
          <span class="text-xs text-gray-500">共 {{ total }} 条</span>
          <button class="h-8 px-3 rounded bg-white border text-xs" :disabled="state.page<=1" @click="state.page--; loadList()">上一页</button>
          <span class="text-xs">第 {{ state.page }} 页</span>
          <button class="h-8 px-3 rounded bg-white border text-xs" :disabled="state.page*state.pageSize>=total" @click="state.page++; loadList()">下一页</button>
        </div>
      </section>

      <!-- 导入弹窗 -->
      <div v-if="showImport" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20">
        <div class="w-[720px] max-w-[95vw] rounded-2xl bg-white shadow-xl border border-gray-200 p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="text-sm font-semibold text-gray-800">考纲一键导入</div>
            <button class="text-gray-500 hover:text-gray-800" @click="showImport=false">×</button>
          </div>
          <div class="grid md:grid-cols-3 gap-3 mb-3">
            <div class="flex items-center gap-2">
              <label class="text-sm text-gray-700 whitespace-nowrap">省份</label>
              <input v-model="state.province" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm w-full"/>
            </div>
            <div class="flex items-center gap-2">
              <label class="text-sm text-gray-700 whitespace-nowrap">专业</label>
              <input v-model="state.major" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm w-full"/>
            </div>
            <div class="flex items-center gap-2">
              <label class="text-sm text-gray-700 whitespace-nowrap">模式</label>
              <select v-model="importMode" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm w-full">
                <option value="replace">替换（清空后导入）</option>
                <option value="append">追加</option>
              </select>
            </div>
          </div>
          <textarea v-model="importText" rows="10" placeholder="在此粘贴考纲文本：\n【计算机基础】\n1. 了解计算机的发展、特点、分类及应用领域\n2. 了解计算机的工作原理，熟悉计算机系统的组成\n..." class="w-full px-3 py-2 rounded border border-gray-300 bg-white text-sm"></textarea>
          <div class="mt-3 flex items-center gap-2">
            <button class="h-9 px-4 rounded bg-primary text-white text-xs" :disabled="!state.province||!state.major||!importText" @click="submitImport">提交</button>
            <span v-if="importMsg" :class="importOk ? 'text-emerald-600' : 'text-red-600'" class="text-xs">{{ importMsg }}</span>
          </div>
          <div class="mt-2 text-[11px] text-gray-500">说明：文本需使用【大类】作为分段标题；条目以“序号+句点/顿号+空格+内容”的样式，如“1. 内容”或“1、 内容”。</div>
        </div>
      </div>

      <section class="mt-4 rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-4 shadow-sm">
        <div class="flex flex-wrap items-center gap-2 text-sm">
          <button class="h-9 px-3 rounded bg-white border" :disabled="!state.province||!state.major" @click="exportExcel">导出 Excel</button>
          <button class="h-9 px-3 rounded bg-white border" :disabled="!state.province||!state.major" @click="exportMarkdown">导出 Markdown</button>
          <button class="h-9 px-3 rounded bg-white border" @click="downloadTemplate">下载导入模板（MD）</button>
          <button class="h-9 px-3 rounded bg-white border" @click="downloadExcelTemplate">下载 Excel 模板</button>
          <span class="mx-2 h-6 w-px bg-gray-200"></span>
          <label class="flex items-center gap-2">
            <span class="text-gray-600">导入模式</span>
            <select v-model="importMode" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm">
              <option value="replace">替换（清空后导入）</option>
              <option value="append">追加</option>
            </select>
          </label>
          <button class="h-9 px-3 rounded bg-white border" :disabled="!state.province||!state.major" @click="triggerExcel">导入 Excel...</button>
          <input ref="excelInput" type="file" accept=".xlsx,.xls" class="hidden" @change="onExcelChange" />
          <span v-if="opMsg" class="text-xs" :class="opOk ? 'text-emerald-600':'text-red-600'">{{ opMsg }}</span>
        </div>
        <div class="mt-3 grid md:grid-cols-4 gap-3 items-end">
          <div class="col-span-2 flex items-center gap-2">
            <label class="text-sm text-gray-700">重命名大类</label>
            <input v-model.trim="renameFrom" placeholder="原大类名" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm w-full"/>
            <span class="text-gray-400">→</span>
            <input v-model.trim="renameTo" placeholder="新大类名" class="h-9 px-2 rounded border border-gray-300 bg-white text-sm w-full"/>
          </div>
          <div class="flex items-center gap-2">
            <button class="h-9 px-3 rounded bg-white border" :disabled="!canRename" @click="renameKp">执行重命名</button>
            <span v-if="renameMsg" class="text-xs" :class="renameOk ? 'text-emerald-600':'text-red-600'">{{ renameMsg }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { apiSyllabusPresets, apiManageSyllabusList, apiManageSyllabusSave, apiManageSyllabusDelete, apiManageSyllabusClear, apiManageSyllabusImportText, apiManageSyllabusExport, apiManageSyllabusTemplate, apiManageSyllabusDedupe, apiManageSyllabusRenameKp, apiManageSyllabusTemplateExcel, apiManageSyllabusImportExcel } from '../../api/index'

const provinces = ref([])
const majorsByProvince = ref({})
const state = reactive({ province: '', major: '', page: 1, pageSize: 20 })
const filters = reactive({ kp: '', keyword: '' })
const kpList = ref([])
const kpCounts = reactive({})
const items = ref([])
const total = ref(0)

const createForm = reactive({ kp: '', primary: '' })
const canCreate = computed(() => !!(state.province && state.major && createForm.kp && createForm.primary))

const showImport = ref(false)
const importMode = ref('replace')
const importText = ref('')
const importMsg = ref('')
const importOk = ref(false)

const opMsg = ref('')
const opOk = ref(false)
const renameFrom = ref('')
const renameTo = ref('')
const renameMsg = ref('')
const renameOk = ref(false)
const canRename = computed(() => !!(state.province && state.major && renameFrom.value && renameTo.value && renameFrom.value !== renameTo.value))

const majorOptions = computed(() => {
  const arr = majorsByProvince.value[state.province] || []
  return Array.isArray(arr) ? arr : []
})

function setKP(k){ filters.kp = k; state.page = 1; loadList() }
function openImport(){ showImport.value = true; importMsg.value = '' }

async function submitImport(){
  importMsg.value = ''
  try{
    const { data } = await apiManageSyllabusImportText({ province: state.province, major: state.major, text: importText.value, mode: importMode.value })
    if (data?.success){ importOk.value = true; importMsg.value = `导入成功：新增 ${data.created} 条，大类 ${data.kp_sections} 个。`; loadMeta(); loadList() }
    else { importOk.value = false; importMsg.value = data?.error_msg || '导入失败' }
  }catch{ importOk.value = false; importMsg.value = '导入异常' }
}

async function clearAll(){
  if (!state.province || !state.major) return
  try{ await apiManageSyllabusClear({ province: state.province, major: state.major }); await loadList() }catch{}
}
async function clearByKP(kp){
  try{ await apiManageSyllabusClear({ province: state.province, major: state.major, kp }); await loadList() }catch{}
}
async function createItem(){
  if (!canCreate.value) return
  try{
    await apiManageSyllabusSave({ province: state.province, major: state.major, kp: createForm.kp, primary: createForm.primary })
    createForm.kp = ''; createForm.primary = ''; await loadList()
  }catch{}
}
async function saveItem(it){
  try{ await apiManageSyllabusSave({ id: it.id, province: state.province, major: state.major, kp: it.kp, primary: it.primary }); await loadList() }catch{}
}
async function deleteItem(it){
  try{ await apiManageSyllabusDelete({ id: it.id }); await loadList() }catch{}
}

async function loadMeta(){
  try{
    const { data } = await apiSyllabusPresets()
    if (data?.success){ provinces.value = data.provinces || []; majorsByProvince.value = data.majors_by_province || {} }
    if (!state.province && provinces.value.length) state.province = provinces.value[0]
    if (!state.major && majorsByProvince.value[state.province] && majorsByProvince.value[state.province].length){ state.major = majorsByProvince.value[state.province][0] }
  }catch{}
}

async function loadList(){
  if (!state.province || !state.major){ items.value = []; total.value = 0; kpList.value = []; return }
  try{
    const { data } = await apiManageSyllabusList({ province: state.province, major: state.major, kp: filters.kp || undefined, q: filters.keyword || undefined, page: state.page, page_size: state.pageSize })
    if (data?.success){ items.value = data.items || []; total.value = data.total || 0; kpList.value = data.kp_list || []; Object.assign(kpCounts, data.kp_counts || {}) }
  }catch{ items.value = []; total.value = 0 }
}

watch(() => state.province, () => { state.major = ''; state.page = 1; loadMeta(); loadList() })
watch(() => state.major, () => { state.page = 1; loadList() })
watch(() => state.pageSize, () => { state.page = 1; loadList() })

onMounted(async () => { await loadMeta(); await loadList() })

function downloadBlob(blob, filename){
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

async function exportExcel(){
  opMsg.value = ''
  try{
    const { data } = await apiManageSyllabusExport({ province: state.province, major: state.major, fmt: 'excel', kp: filters.kp || undefined })
    downloadBlob(data, `syllabus_${state.province}_${state.major}.xlsx`)
    opOk.value = true; opMsg.value = '已导出 Excel'
  }catch{ opOk.value = false; opMsg.value = '导出失败' }
}
async function exportMarkdown(){
  opMsg.value = ''
  try{
    const { data } = await apiManageSyllabusExport({ province: state.province, major: state.major, fmt: 'md', kp: filters.kp || undefined })
    downloadBlob(data, `syllabus_${state.province}_${state.major}.md`)
    opOk.value = true; opMsg.value = '已导出 Markdown'
  }catch{ opOk.value = false; opMsg.value = '导出失败' }
}
async function downloadTemplate(){
  try{ const { data } = await apiManageSyllabusTemplate(); downloadBlob(data, 'syllabus_template.md') }catch{}
}
async function dedupeDry(){
  opMsg.value = ''
  try{ const { data } = await apiManageSyllabusDedupe({ province: state.province, major: state.major, dry: 1 }); opOk.value = true; opMsg.value = `试运行：发现重复 ${data.duplicates||0} 条，不做删除。` }catch{ opOk.value = false; opMsg.value = '去重试运行失败' }
}
async function dedupeRun(){
  opMsg.value = ''
  try{ const { data } = await apiManageSyllabusDedupe({ province: state.province, major: state.major, dry: 0 }); opOk.value = true; opMsg.value = `已删除重复 ${data.deleted||0} 条。`; await loadList() }catch{ opOk.value = false; opMsg.value = '去重执行失败' }
}
async function renameKp(){
  renameMsg.value = ''
  try{
    const { data } = await apiManageSyllabusRenameKp({ province: state.province, major: state.major, from_kp: renameFrom.value, to_kp: renameTo.value })
    if (data?.success){ renameOk.value = true; renameMsg.value = `已更新 ${data.updated||0} 条，合并 ${data.merged||0} 条。`; renameFrom.value=''; renameTo.value=''; await loadList(); await loadMeta() }
    else { renameOk.value = false; renameMsg.value = data?.error_msg || '重命名失败' }
  }catch{ renameOk.value = false; renameMsg.value = '重命名异常' }
}

const excelInput = ref(null)

function triggerExcel(){ excelInput.value && excelInput.value.click() }
async function onExcelChange(e){
  opMsg.value = ''
  const f = e?.target?.files?.[0]
  if (!f) return
  try{
    const fd = new FormData()
    fd.append('file', f)
    fd.append('mode', importMode.value)
    fd.append('province', state.province)
    fd.append('major', state.major)
    const { data } = await apiManageSyllabusImportExcel(fd)
    if (data?.success){
      opOk.value = true
      opMsg.value = `Excel 导入完成：新增 ${data.created||0}，跳过 ${data.skipped||0}，错误 ${data.errors||0}`
      await loadMeta(); await loadList()
    } else {
      opOk.value = false
      opMsg.value = data?.error_msg || 'Excel 导入失败'
    }
  } catch {
    opOk.value = false
    opMsg.value = 'Excel 导入异常'
  } finally {
    if (excelInput.value) excelInput.value.value = ''
  }
}

async function downloadExcelTemplate(){
  try{ const { data } = await apiManageSyllabusTemplateExcel(); downloadBlob(data, 'syllabus_import_template.xlsx') }catch{}
}
</script>

<style scoped>
/* use global .text-primary/.bg-primary from tokens.css */
</style>
