<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { apiLogout, apiManageExamList, apiManageExamSignins, apiManageStudentList, apiManageScoreList, apiManageFaceSetting, apiManageFaceSettingSave } from '../api/index'
import { apiManageReviewQueue, apiManageReviewConsensus } from '../api/index'
import { useUserStore } from '../stores/user'
import { useUiStore } from '../stores/ui'
import { useSyllabusStore } from '../stores/syllabus'
import ThemeToggle from '../components/ThemeToggle.vue'
import AppLogo from '../components/AppLogo.vue'

const router = useRouter()
const userStore = useUserStore()
const ui = useUiStore()
const s = useSyllabusStore()
const avatarUrl = computed(() => userStore.avatarUrl)
const username = computed(() => userStore.username || '用户')
const role = computed(() => userStore.role || '老师')

// 顶部统计（全部真实数据）
const questionCount = ref(0)
const examCount = ref(0)
const studentCount = ref(0)
const avgScore = ref(0)

// 最近考试（来自 manage exams）
const recentRecords = ref([])

// 成绩分布图
let scoreChart

// 签到情况（显示汇总并跳转独立页）
const manageExams = ref([])
const selectedExamId = ref('')
const classFilter = ref('')
const signCounts = ref({ signed_in:0, failed:0, not_signed:0, total:0 })
const signLoading = ref(false)

// 人脸验证设置
const faceRequired = ref(false)
const faceSettingLoading = ref(false)
const faceSettingMsg = ref('')

// 待审核题目统计
const reviewQueueStats = ref({ total: 0, missing_kp: 0, missing_primary: 0, missing_analysis: 0, unreviewed: 0 })
// 新增：审查共识阈值
const reviewConsensus = ref(null)

function safeParseDate(str) {
  if (!str) return null
  // 后端格式: YYYY-MM-DD HH:mm:ss (无时区) 当作本地时间处理
  // Safari 兼容: 替换为空格为 'T'
  const norm = str.replace(' ', 'T')
  const d = new Date(norm)
  return isNaN(d.getTime()) ? null : d
}

function toBeijing(iso) {
  if (!iso) return ''
  try {
    const d = safeParseDate(iso) || new Date(iso)
    const parts = new Intl.DateTimeFormat('zh-CN', {
      timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    }).formatToParts(d)
    const map = Object.fromEntries(parts.map(p => [p.type, p.value]))
    return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}:${map.second}`
  } catch { return iso }
}

function examRuntimeStatus(e) {
  const st = safeParseDate(e.start_time)
  const et = safeParseDate(e.end_time)
  if (!st || !et) return '未知'
  const now = Date.now()
  if (now < st.getTime()) return '计划中'
  if (now > et.getTime()) return '已结束'
  return '进行中'
}

function updateScoreChartTheme(){
  if(!scoreChart) return
  const dark = ui.theme==='dark'
  const textColor = dark ? '#e5e7eb' : '#374151'
  const axisLine = dark ? '#4b5563' : '#d1d5db'
  scoreChart.setOption({
    textStyle:{ color:textColor },
    xAxis:{ axisLabel:{color:textColor}, axisLine:{ lineStyle:{ color:axisLine } } },
    yAxis:{ axisLabel:{color:textColor}, axisLine:{ lineStyle:{ color:axisLine } }, splitLine:{ lineStyle:{ color: dark?'#334155':'#e5e7eb' } } },
    tooltip:{ textStyle:{ color:textColor } }
  })
}

function drawScoreChart(bins = [], counts = []) {
  const el = document.getElementById('scoreDistribution')
  if (!el) return
  if (!scoreChart) scoreChart = echarts.init(el)
  scoreChart.setOption({
    animation: false,
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: bins },
    yAxis: { type: 'value' },
    series: [{ name: '学生人数', type: 'bar', barWidth: '60%', data: counts, itemStyle: { color: '#2563eb' } }]
  })
  updateScoreChartTheme()
  window.addEventListener('resize', () => scoreChart && scoreChart.resize())
}

async function fetchDistribution() {
  try {
    if (!selectedExamId.value) { return }
    const { data } = await apiManageScoreList({ exam_id: selectedExamId.value, page_size: 1 })
    if (data?.success) {
      const bins = data.score_bins || ['60分以下','60-70分','70-80分','80-90分','90分以上']
      const counts = data.score_counts || [0,0,0,0,0]
      avgScore.value = data.avg || 0
      drawScoreChart(bins, counts)
      return
    }
  } catch {}
  drawScoreChart(['60分以下','60-70分','70-80分','80-90分','90分以上'], [0,0,0,0,0])
}

async function loadHeaderAndRecent() {
  const tasks = [
    apiManageExamList(),
    apiManageStudentList({ role: '学生', page_size: 1 }),
    apiManageScoreList({ page_size: 1 }) // 全局平均分备选
  ]
  try {
    const [examsRes, stuRes, scoreRes] = await Promise.all(tasks)
    if (examsRes?.data?.success) {
      const ex = examsRes.data
      manageExams.value = ex.exams || []
      examCount.value = manageExams.value.length
      questionCount.value = Number(ex.question_count || 0)
      recentRecords.value = manageExams.value.slice(0, 6).map(e => ({
        title: e.title,
        class: '-',
        time: `${toBeijing(e.start_time)} ~ ${toBeijing(e.end_time)}`,
        count: e.count ?? '-',
        avg: typeof e.avg==='number'? e.avg : '-',
        status: examRuntimeStatus(e)
      }))
      if (!selectedExamId.value && manageExams.value.length) {
        selectedExamId.value = String(manageExams.value[0].id)
      }
    }
    if (stuRes?.data?.success) { studentCount.value = stuRes.data.total || 0 }
    if (scoreRes?.data?.success && !avgScore.value) { // 若后续考试分布未覆盖，使用全局
      avgScore.value = scoreRes.data.avg || 0
      const bins = scoreRes.data.score_bins || ['60分以下','60-70分','70-80分','80-90分','90分以上']
      const counts = scoreRes.data.score_counts || [0,0,0,0,0]
      drawScoreChart(bins, counts)
    }
  } catch {
    drawScoreChart(['60分以下','60-70分','70-80分','80-90分','90分以上'], [0,0,0,0,0])
  }
}

async function fetchSignins() {
  if (!selectedExamId.value) { signCounts.value = { signed_in:0, failed:0, not_signed:0, total:0 }; return }
  signLoading.value = true
  try {
    const { data } = await apiManageExamSignins({ exam_id: selectedExamId.value, classroom: classFilter.value || undefined, page_size: 1 })
    if (data?.success) {
      signCounts.value = data.counts || { signed_in:0, failed:0, not_signed:0, total:0 }
    } else {
      signCounts.value = { signed_in:0, failed:0, not_signed:0, total:0 }
    }
  } catch {
    signCounts.value = { signed_in:0, failed:0, not_signed:0, total:0 }
  } finally {
    signLoading.value = false
  }
  await fetchDistribution()
}

async function loadFaceSetting(){
  faceSettingLoading.value = true
  faceSettingMsg.value=''
  try{ const { data } = await apiManageFaceSetting(); if(data?.success){ faceRequired.value = !!data.face_required } else { faceSettingMsg.value = data?.error_msg || '获取失败' } }catch{ faceSettingMsg.value='获取失败'} finally{ faceSettingLoading.value=false }
}
async function toggleFaceSetting(){
  if(faceSettingLoading.value) return
  faceSettingLoading.value = true
  faceSettingMsg.value=''
  try{ const { data } = await apiManageFaceSettingSave(!faceRequired.value); if(data?.success){ faceRequired.value = !!data.face_required; faceSettingMsg.value = '已保存'; setTimeout(()=> faceSettingMsg.value='', 1500)} else { faceSettingMsg.value = data?.error_msg || '保存失败' }}catch{ faceSettingMsg.value='保存失败' } finally { faceSettingLoading.value=false }
}

async function fetchReviewQueueStats(){
  try{ const { data } = await apiManageReviewQueue({ limit: 1, missing_only: 1 }); if(data?.success){ reviewQueueStats.value = data.stats || reviewQueueStats.value } }catch{}
}
async function fetchReviewConsensus(){
  try{ const { data } = await apiManageReviewConsensus(); if(data?.success){ reviewConsensus.value = Number(data.threshold) } }catch{}
}

async function onLogout() {
  try { await apiLogout() } catch {}
  localStorage.removeItem('user_id')
  localStorage.removeItem('role')
  userStore.clear()
  s.clear()
  router.push('/login')
}

function goProfile() { router.push('/profile') }
function goSignins() { router.push('/manage/signins') }

watch(selectedExamId, () => {
  // 统一响应考试切换
  fetchSignins()
})
watch(()=>ui.theme, ()=> updateScoreChartTheme())

onMounted(async () => {
  await userStore.loadProfile(true)
  if (!userStore.userId) { router.push('/login'); return }
  await loadFaceSetting()
  await loadHeaderAndRecent()
  await fetchSignins()
  await fetchReviewQueueStats()
  await fetchReviewConsensus()
})
</script>

<template>
  <div class="min-h-screen flex bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <!-- 顶部导航 -->
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="$router.push('/')" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">教师管理后台</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <ThemeToggle />
          <button class="px-4 h-10 rounded-lg text-gray-700 bg-white/60 border border-gray-200 hover:bg-white transition flex items-center gap-2" @click="goProfile">
            <i class="fas fa-id-card"></i><span>个人主页</span>
          </button>
          <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/60 border border-gray-200 text-gray-600">
            <div class="w-7 h-7 rounded-full overflow-hidden bg-gray-100">
              <img v-if="avatarUrl" :src="avatarUrl" alt="avatar" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-400"><i class="fas fa-user"></i></div>
            </div>
            <span class="max-w-[90px] truncate" :title="username">{{ username }}</span>
            <span class="px-1.5 py-0.5 text-[10px] rounded bg-primary/10 text-primary">{{ role }}</span>
          </div>
          <button class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition flex items-center gap-2" @click="onLogout">
            <i class="fas fa-sign-out-alt"></i><span>退出</span>
          </button>
        </div>
      </div>
    </nav>

    <!-- 侧边栏 -->
    <aside class="fixed top-16 left-0 h-[calc(100vh-64px)] w-60 bg-white/70 backdrop-blur border-r border-gray-200/80 px-3 py-5 flex flex-col">
      <nav class="space-y-1 text-sm">
        <div class="flex items-center gap-3 px-4 py-3 rounded-xl bg-primary/5 text-primary font-medium">
          <i class="fas fa-home"></i><span>数据概览</span>
        </div>
        <router-link to="/manage/exams" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-edit"></i><span>考试与题库管理</span>
        </router-link>
        <router-link to="/manage/review-queue" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-clipboard-check"></i><span>待审核题目</span>
        </router-link>
        <router-link to="/manage/students" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-users"></i><span>学生管理</span>
        </router-link>
        <router-link to="/manage/scores" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-chart-bar"></i><span>成绩统计</span>
        </router-link>
        <router-link to="/manage/signins" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-user-check"></i><span>签到情况</span>
        </router-link>
        <router-link to="/manage/face-supplements" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-id-card"></i><span>人脸补充审核</span>
        </router-link>
        <router-link to="/manage/q-comments" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-comments"></i><span>评论管理</span>
        </router-link>
        <!-- 新增：考纲管理入口 -->
        <router-link to="/manage/syllabus" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-list-ul"></i><span>考纲管理</span>
        </router-link>
      </nav>
      <div class="mt-auto pt-6 text-[10px] text-gray-400 tracking-wide">© 2024 考试系统</div>
    </aside>

    <!-- 主内容 -->
    <main class="flex-1 pt-20 pb-10 px-6 lg:px-8 ml-60">
      <!-- 顶部统计卡 -->
      <div class="grid gap-6 md:grid-cols-2 xl:grid-cols-5 mb-8">
        <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 shadow-sm hover:shadow-md transition">
          <div class="flex items-start justify-between mb-4"><h3 class="text-xs font-medium tracking-wide text-gray-500">题库总量</h3><span class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center"><i class="fas fa-book text-primary"></i></span></div>
          <div class="text-2xl font-semibold text-gray-800">{{ questionCount }}</div>
        </div>
        <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 shadow-sm hover:shadow-md transition">
          <div class="flex items-start justify-between mb-4"><h3 class="text-xs font-medium tracking-wide text-gray-500">考试场次</h3><span class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center"><i class="fas fa-edit text-primary"></i></span></div>
          <div class="text-2xl font-semibold text-gray-800">{{ examCount }}</div>
        </div>
        <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 shadow-sm hover:shadow-md transition">
          <div class="flex items-start justify-between mb-4"><h3 class="text-xs font-medium tracking-wide text-gray-500">学生人数</h3><span class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center"><i class="fas fa-users text-primary"></i></span></div>
          <div class="text-2xl font-semibold text-gray-800">{{ studentCount }}</div>
        </div>
        <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 shadow-sm hover:shadow-md transition">
          <div class="flex items-start justify-between mb-4"><h3 class="text-xs font-medium tracking-wide text-gray-500">平均分</h3><span class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center"><i class="fas fa-chart-line text-primary"></i></span></div>
          <div class="text-2xl font-semibold text-gray-800">{{ avgScore }}</div>
        </div>
        <!-- 全局人脸开关 -->
        <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 shadow-sm flex flex-col justify-between">
          <div class="flex items-start justify-between mb-3">
            <h3 class="text-xs font-medium tracking-wide text-gray-500">访问人脸验证</h3>
            <span class="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center"><i class="fas fa-user-shield text-primary text-sm"></i></span>
          </div>
          <div class="flex items-center gap-3">
            <button @click="toggleFaceSetting" :disabled="faceSettingLoading" class="h-9 px-4 rounded-md text-xs font-medium shadow-sm transition disabled:opacity-50" :class="faceRequired ? 'bg-primary text-white hover:bg-primary/90' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'">
              <span v-if="!faceSettingLoading">{{ faceRequired ? '开启' : '关闭' }}</span>
              <span v-else>处理中...</span>
            </button>
            <div class="text-[11px] text-gray-500 leading-relaxed">
              <span v-if="faceRequired">学生/VIP 练习与知识点访问需 120 分钟内人脸签到</span>
              <span v-else>关闭后练习及知识点访问无需人脸验证</span>
            </div>
          </div>
          <div v-if="faceSettingMsg" class="mt-2 text-[11px] text-emerald-600">{{ faceSettingMsg }}</div>
        </div>
      </div>

      <!-- 新增：待审核题目卡片 -->
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-6 shadow-sm hover:shadow-md transition mb-8">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-gray-800">待审核题目</h3>
          <router-link to="/manage/review-queue" class="text-xs text-primary hover:underline">查看全部</router-link>
        </div>
        <div class="flex flex-wrap items-center gap-3 text-xs">
          <span class="px-2 py-1 rounded bg-amber-50 text-amber-700 border border-amber-200">总计：{{ reviewQueueStats.total }}</span>
          <span class="px-2 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200">考纲空：{{ reviewQueueStats.missing_kp }}</span>
          <span class="px-2 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">一级空：{{ reviewQueueStats.missing_primary }}</span>
          <span class="px-2 py-1 rounded bg-teal-50 text-teal-700 border border-teal-200">解析空：{{ reviewQueueStats.missing_analysis }}</span>
          <span class="px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200">未审：{{ reviewQueueStats.unreviewed }}</span>
          <span class="px-2 py-1 rounded bg-gray-100 text-gray-600 border border-gray-200" title="达成该人数共识即自动入库">阈值：{{ reviewConsensus ?? '-' }} 人</span>
          <router-link to="/manage/review-queue" class="ml-auto h-9 px-4 rounded bg-primary text-white text-xs flex items-center">前往处理</router-link>
        </div>
      </div>

      <!-- 考试计划 & 成绩分布 -->
      <div class="grid gap-6 lg:grid-cols-2 mb-8">
        <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-6 shadow-sm hover:shadow-md transition">
          <div class="flex items-center justify-between mb-4"><h3 class="text-sm font-semibold text-gray-800">考试计划</h3><span class="text-[11px] text-gray-400">最近 6 条</span></div>
          <div class="space-y-4" v-if="recentRecords.length">
            <div v-for="(exam,idx) in recentRecords" :key="idx" class="p-4 rounded-xl bg-white/60 border border-gray-200 hover:shadow-sm transition flex items-center justify-between">
              <div class="min-w-0 pr-4">
                <h4 class="font-medium text-gray-800 truncate">{{ exam.title }}</h4>
                <p class="text-xs text-gray-500 whitespace-pre-wrap break-words break-all leading-relaxed">{{ exam.time }}</p>
              </div>
              <span class="px-2.5 py-1 text-xs rounded-full font-medium" :class="exam.status==='已结束' ? 'bg-gray-100 text-gray-600' : (exam.status==='进行中' ? 'bg-blue-100 text-blue-600' : 'bg-amber-100 text-amber-700')">{{ exam.status }}</span>
            </div>
          </div>
          <div v-else class="text-center py-10 text-gray-400 text-sm">暂无考试计划</div>
        </div>
        <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-6 shadow-sm hover:shadow-md transition">
          <div class="flex items-center justify-between mb-4"><h3 class="text-sm font-semibold text-gray-800">成绩分布</h3><i class="fas fa-chart-column text-primary"></i></div>
          <div id="scoreDistribution" class="h-[300px]"></div>
        </div>
      </div>

      <!-- 签到情况跳转卡片（汇总数据） -->
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-6 shadow-sm hover:shadow-md transition">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div class="flex items-center gap-2 flex-wrap">
            <label class="text-sm text-gray-700">考试</label>
            <select v-model="selectedExamId" @change="fetchSignins" class="h-9 border border-gray-300 rounded px-3 text-sm bg-white">
              <option v-for="e in manageExams" :key="e.id" :value="String(e.id)">{{ e.title }}</option>
            </select>
            <label class="ml-3 text-sm text-gray-700">班级</label>
            <input v-model="classFilter" @keyup.enter="fetchSignins" placeholder="如 计科2301" class="h-9 border border-gray-300 rounded px-3 text-sm bg-white"/>
            <button class="btn-secondary h-9 px-3" @click="fetchSignins">刷新</button>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <span class="px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">已签到：{{ signCounts.signed_in }}</span>
            <span class="px-2 py-1 rounded-full bg-red-50 text-red-600 border border-red-200">失败：{{ signCounts.failed }}</span>
            <span class="px-2 py-1 rounded-full bg-gray-100 text-gray-600 border border-gray-200">未签到：{{ signCounts.not_signed }}</span>
            <span class="px-2 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">合计：{{ signCounts.total }}</span>
          </div>
        </div>
        <div class="mt-4 flex items-center gap-3 justify-center">
          <button class="btn-secondary h-9 px-4" @click="goSignins">前往签到情况页面</button>
          <span v-if="signLoading" class="text-xs text-gray-500">加载中...</span>
        </div>
      </div>

      <!-- 最近考试记录表 -->
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-6 shadow-sm hover:shadow-md transition mt-8">
        <div class="flex items-center justify-between mb-5"><h3 class="text-sm font-semibold text-gray-800">最近考试记录</h3><button class="px-4 h-9 text-xs rounded-lg bg-white/60 border border-gray-200 hover:bg-white transition">查看全部</button></div>
        <div class="overflow-x-auto">
          <table class="min-w-[880px] w-full text-xs">
            <thead>
              <tr class="bg-primary/5 text-gray-600 text-left">
                <th class="py-2.5 px-3 font-medium">考试名称</th>
                <th class="py-2.5 px-3 font-medium">班级</th>
                <th class="py-2.5 px-3 font-medium">考试时间</th>
                <th class="py-2.5 px-3 font-medium">参考人数</th>
                <th class="py-2.5 px-3 font-medium">平均分</th>
                <th class="py-2.5 px-3 font-medium">状态</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 text-gray-700">
              <tr v-for="(exam,idx) in recentRecords" :key="idx" class="hover:bg-primary/5">
                <td class="py-2.5 px-3 whitespace-pre-wrap break-words">{{ exam.title }}</td>
                <td class="py-2.5 px-3">{{ exam.class }}</td>
                <td class="py-2.5 px-3">{{ exam.time }}</td>
                <td class="py-2.5 px-3">{{ exam.count }}</td>
                <td class="py-2.5 px-3">{{ exam.avg }}</td>
                <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="exam.status==='已结束' ? 'bg-gray-100 text-gray-600' : (exam.status==='进行中' ? 'bg-blue-100 text-blue-600' : 'bg-amber-100 text-amber-700')">{{ exam.status }}</span></td>
              </tr>
              <tr v-if="!recentRecords.length"><td colspan="6" class="py-8 text-center text-gray-400">暂无数据</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
</style>
