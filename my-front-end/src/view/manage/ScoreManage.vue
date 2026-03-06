<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { apiManageScoreList, apiManageScoreDelete } from '../../api/index'

const loading = ref(false)
const errorMsg = ref('')

// 过滤与数据
const exams = ref([])
const filter = ref({ exam_id: '', username: '', classroom: '' })
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const avg = ref(0)
const records = ref([])

// 图表
let chart
const scoreBins = ref([])
const scoreCounts = ref([])

function toBeijing(s) {
  if (!s) return ''
  try {
    const d = new Date(String(s).replace(' ', 'T'))
    const parts = new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).formatToParts(d)
    const m = Object.fromEntries(parts.map(p => [p.type, p.value]))
    return `${m.year}-${m.month}-${m.day} ${m.hour}:${m.minute}:${m.second}`
  } catch { return s }
}

async function fetchScores() {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = { ...filter.value, page: page.value, page_size: pageSize.value }
    const { data } = await apiManageScoreList(params)
    if (data?.success) {
      exams.value = data.exams || []
      total.value = data.total || 0
      avg.value = data.avg || 0
      scoreBins.value = data.score_bins || []
      scoreCounts.value = data.score_counts || []
      records.value = (data.records || []).map(r => ({ ...r, start_time: toBeijing(r.start_time), end_time: toBeijing(r.end_time), submit_time: toBeijing(r.submit_time) }))
      drawChart()
    } else {
      errorMsg.value = data?.error_msg || '加载失败'
      records.value = []
    }
  } catch (e) {
    errorMsg.value = '网络错误'
    records.value = []
  } finally {
    loading.value = false
  }
}

function drawChart() {
  const el = document.getElementById('scoreDistributionManage')
  if (!el) return
  if (!chart) chart = echarts.init(el)
  chart.setOption({
    animation: false,
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: scoreBins.value },
    yAxis: { type: 'value' },
    series: [{ name: '人数', type: 'bar', barWidth: '60%', data: scoreCounts.value, itemStyle: { color: '#2563eb' } }]
  })
  window.addEventListener('resize', () => chart && chart.resize())
}

function onSearch() {
  page.value = 1
  fetchScores()
}

function resetFilters() {
  filter.value = { exam_id: '', username: '', classroom: '' }
  onSearch()
}

function nextPage() {
  if (page.value * pageSize.value < total.value) { page.value++; fetchScores() }
}
function prevPage() {
  if (page.value > 1) { page.value--; fetchScores() }
}

async function removeRecord(id) {
  if (!confirm('确定删除该成绩记录吗？')) return
  try {
    const { data } = await apiManageScoreDelete(id)
    if (data?.success) fetchScores()
    else alert(data?.error_msg || '删除失败')
  } catch { alert('网络错误，删除失败') }
}

const role = ref(localStorage.getItem('role') || '')
const roleHome = computed(() => role.value === '管理员' ? '/admin' : role.value === '老师' ? '/teacher' : (role.value === '学生' || role.value === 'VIP') ? '/student' : '/')

onMounted(fetchScores)
watch(pageSize, () => { page.value = 1; fetchScores() })
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">成绩统计</h1>
      <button class="bg-gray-600 text-white px-4 py-2 rounded" @click="$router.push(roleHome)">返回</button>
    </div>

    <div class="bg-white rounded shadow p-4 mb-4">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-gray-600 mb-1">考试</label>
          <select v-model="filter.exam_id" class="w-full border rounded px-3 py-2">
            <option value="">全部考试</option>
            <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.title }}</option>
          </select>
        </div>
        <div>
          <label class="block text-gray-600 mb-1">学生姓名</label>
          <input v-model="filter.username" type="text" class="w-full border rounded px-3 py-2" placeholder="模糊匹配" />
        </div>
        <div>
          <label class="block text-gray-600 mb-1">班级</label>
          <input v-model="filter.classroom" type="text" class="w-full border rounded px-3 py-2" placeholder="模糊匹配" />
        </div>
        <div class="flex items-end gap-2">
          <button class="bg-blue-600 text-white px-4 py-2 rounded" @click="onSearch">查询</button>
          <button class="bg-gray-300 text-gray-700 px-4 py-2 rounded" @click="resetFilters">重置</button>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <div class="bg-white p-6 rounded shadow lg:col-span-1 flex items-center justify-between">
        <div>
          <div class="text-gray-500">平均分</div>
          <div class="text-3xl font-bold">{{ avg }}</div>
        </div>
        <div>
          <div class="text-gray-500">记录数</div>
          <div class="text-3xl font-bold">{{ total }}</div>
        </div>
      </div>
      <div class="bg-white p-6 rounded shadow lg:col-span-2">
        <h3 class="text-lg font-semibold mb-2">成绩分布</h3>
        <div id="scoreDistributionManage" style="height:260px"></div>
      </div>
    </div>

    <div v-if="errorMsg" class="mb-4 text-red-600">{{ errorMsg }}</div>

    <div class="overflow-x-auto bg-white rounded shadow">
      <table class="min-w-[1000px] w-full text-sm">
        <thead>
          <tr class="bg-blue-50 text-blue-700 text-left">
            <th class="py-3 px-4">学生</th>
            <th class="py-3 px-4">班级</th>
            <th class="py-3 px-4">考试名称</th>
            <th class="py-3 px-4">得分/总分</th>
            <th class="py-3 px-4">开始时间</th>
            <th class="py-3 px-4">结束时间</th>
            <th class="py-3 px-4">提交时间</th>
            <th class="py-3 px-4 text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in records" :key="r.record_id" class="border-t hover:bg-gray-50">
            <td class="py-3 px-4">{{ r.username }}</td>
            <td class="py-3 px-4">{{ r.classroom }}</td>
            <td class="py-3 px-4">{{ r.exam_title }}</td>
            <td class="py-3 px-4">{{ r.score }} / {{ r.full_score }}</td>
            <td class="py-3 px-4">{{ r.start_time }}</td>
            <td class="py-3 px-4">{{ r.end_time }}</td>
            <td class="py-3 px-4">{{ r.submit_time }}</td>
            <td class="py-3 px-4">
              <div class="flex justify-center">
                <button class="text-red-600" @click="removeRecord(r.record_id)"><i class="fas fa-trash"></i> 删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="!records.length && !loading"><td colspan="8" class="py-6 text-center text-gray-400">暂无数据</td></tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between mt-4">
      <div class="text-gray-500">共 {{ total }} 条，每页
        <select v-model.number="pageSize" class="border rounded px-2 py-1">
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
        条
      </div>
      <div class="flex items-center gap-2">
        <button class="px-3 py-1 border rounded" :disabled="page===1" @click="prevPage">上一页</button>
        <span>第 {{ page }} 页</span>
        <button class="px-3 py-1 border rounded" :disabled="page*pageSize>=total" @click="nextPage">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
