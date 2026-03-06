<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { apiLogout, apiManageStudentList, apiManageScoreList, apiManageFaceOverview, apiManageFaceSetting, apiManageFaceSettingSave, apiManageFaceExpiring } from '../api/index'
// 新增：审查统计与阈值
import { apiManageReviewQueue, apiManageReviewConsensus } from '../api/index'
import { useUserStore } from '../stores/user'
import { useUiStore } from '../stores/ui'
import { useSyllabusStore } from '../stores/syllabus'
import SyllabusPicker from '../components/SyllabusPicker.vue'

const router = useRouter()
const userStore = useUserStore()
const ui = useUiStore()
const s = useSyllabusStore()
const avatarUrl = computed(() => userStore.avatarUrl)
const username = computed(() => userStore.username || '用户')
const role = computed(() => userStore.role || '管理员')

// 人员与数据指标
const studentCount = ref(0)
const teacherCount = ref(0)
const adminCount = ref(0)
const totalUsers = computed(() => studentCount.value + teacherCount.value + adminCount.value)
const avgScore = ref(0)
const scoreTotal = ref(0)

// 最近成绩
const recentRecords = ref([])

// VIP 与人脸统计
const vipCount = ref(0)
const vipExpiring3d = ref(0)
const faceTotal = ref(0)
const faceValid = ref(0)
const faceExpiring3d = ref(0)
const faceExpired = ref(0)
const faceMissing = ref(0)
const faceRequired = ref(false)
const faceOverviewLoading = ref(false)
const faceToggleLoading = ref(false)
const faceToggleMsg = ref('')

// 新增：关注总数
const attentionTotal = ref(0)

// 图表实例
let chartBar, chartPieRole, chartFaceStatus
const showStatsPanels = ref(true)
const truncatedRecords = computed(() => recentRecords.value.slice(0, 5))

// 新增：审查队列汇总 & 共识阈值（全局）
const reviewStats = ref({ total: 0, missing_kp: 0, missing_primary: 0, missing_analysis: 0, unreviewed: 0 })
const reviewThreshold = ref(null)

async function fetchSummary() {
  try {
    const [stuRes, tchRes, admRes, scoreRes] = await Promise.all([
      apiManageStudentList({ role: '学生', page_size: 1 }),
      apiManageStudentList({ role: '老师', page_size: 1 }),
      apiManageStudentList({ role: '管理员', page_size: 1 }),
      apiManageScoreList({ page_size: 10 })
    ])
    if (stuRes?.data?.success) studentCount.value = stuRes.data.total || 0
    if (tchRes?.data?.success) teacherCount.value = tchRes.data.total || 0
    if (admRes?.data?.success) adminCount.value = admRes.data.total || 0
    if (scoreRes?.data?.success) {
      avgScore.value = scoreRes.data.avg || 0
      scoreTotal.value = scoreRes.data.total || 0
      recentRecords.value = scoreRes.data.records || []
      drawCharts(scoreRes.data.score_bins || [], scoreRes.data.score_counts || [])
    } else {
      drawCharts(['60分以下','60-70分','70-80分','80-90分','90分以上'], [0,0,0,0,0])
    }
  } catch {
    drawCharts(['60分以下','60-70分','70-80分','80-90分','90分以上'], [0,0,0,0,0])
  }
}

function drawCharts(bins, counts) {
  // 仅保留柱状图与人员结构图
  const elBar = document.getElementById('adminScoreBar')
  if (elBar) {
    chartBar = chartBar || echarts.init(elBar)
    chartBar.setOption({ animation:false, tooltip:{trigger:'axis'}, grid:{left:'3%',right:'4%',bottom:'3%',containLabel:true}, xAxis:{type:'category',data:bins}, yAxis:{type:'value'}, series:[{ name:'人数', type:'bar', barWidth:'55%', data:counts, itemStyle:{ color:'#2563eb'} }] })
  }
  const elPieRole = document.getElementById('adminRolePie')
  if (elPieRole) {
    chartPieRole = chartPieRole || echarts.init(elPieRole)
    const roleData = [ {name:'学生', value:studentCount.value}, {name:'老师', value:teacherCount.value}, {name:'管理员', value:adminCount.value} ]
    chartPieRole.setOption({ animation:false, tooltip:{trigger:'item'}, legend:{bottom:0}, series:[{ type:'pie', radius:['42%','70%'], label:{show:false}, data:roleData }] })
  }
  window.addEventListener('resize', () => { chartBar && chartBar.resize(); chartPieRole && chartPieRole.resize(); chartFaceStatus && chartFaceStatus.resize() })
}

async function fetchFaceOverview(){
  faceOverviewLoading.value = true
  try{
    const { data } = await apiManageFaceOverview()
    if(data?.success){
      vipCount.value = data.vip_count || 0
      vipExpiring3d.value = data.vip_expiring_3d || 0
      faceTotal.value = data.face_total || 0
      faceValid.value = data.face_valid || 0
      faceExpiring3d.value = data.face_expiring_3d || 0
      faceExpired.value = data.face_expired || 0
      faceMissing.value = data.face_missing || 0
      attentionTotal.value = data.attention_total || 0
      faceRequired.value = !!data.face_required
      drawFaceStatusChart()
    }
  }catch{} finally{ faceOverviewLoading.value=false }
}
function drawFaceStatusChart(){
  const el = document.getElementById('adminFaceStatusPie')
  if(!el) return
  chartFaceStatus = chartFaceStatus || echarts.init(el)
  chartFaceStatus.setOption({
    animation:false,
    tooltip:{ trigger:'item' },
    legend:{ bottom:0 },
    series:[{ type:'pie', radius:['40%','70%'], label:{show:false}, data:[
      {value: faceValid.value, name:'有效'},
      {value: faceExpiring3d.value, name:'即将到期'},
      {value: faceExpired.value, name:'已过期'},
      {value: faceMissing.value, name:'未提交'}
    ]}]
  })
}
function refreshOverview(){ fetchFaceOverview() }
async function toggleFaceRequired(){
  if(faceToggleLoading.value) return
  faceToggleLoading.value = true
  faceToggleMsg.value=''
  try{
    const { data } = await apiManageFaceSettingSave(!faceRequired.value)
    if(data?.success){
      faceRequired.value = !!data.face_required
      faceToggleMsg.value = '已保存'
      setTimeout(()=> faceToggleMsg.value='', 1500)
    }else{
      faceToggleMsg.value = data?.error_msg || '保存失败'
    }
  }catch{ faceToggleMsg.value='保存失败' } finally { faceToggleLoading.value=false }
}
function goVipExpiring(){ router.push('/manage/students?vip_status=expiring') }
function goFaceExpired(){ router.push('/manage/students?face_status=expired') }
function goFaceExpiring(){ router.push('/manage/students?face_status=expiring') }

async function onLogout() {
  try { await apiLogout() } catch {}
  localStorage.removeItem('user_id')
  localStorage.removeItem('role')
  userStore.clear()
  s.clear()
  router.push('/login')
}

// 主题切换
function updateChartsTheme(){
  const dark = ui.theme==='dark'
  const textColor = dark ? '#e5e7eb' : '#374151'
  const axisLine = dark ? '#4b5563' : '#d1d5db'
  if(chartBar){
    chartBar.setOption({
      textStyle:{ color:textColor },
      xAxis:{ axisLabel:{color:textColor}, axisLine:{lineStyle:{color:axisLine}}},
      yAxis:{ axisLabel:{color:textColor}, axisLine:{lineStyle:{color:axisLine}}, splitLine:{lineStyle:{color: dark?'#334155':'#e5e7eb'}} }
    })
  }
  if(chartPieRole){ chartPieRole.setOption({ textStyle:{color:textColor}, legend:{ textStyle:{color:textColor} } }) }
  if(chartFaceStatus){ chartFaceStatus.setOption({ textStyle:{color:textColor}, legend:{ textStyle:{color:textColor} } }) }
}
watch(()=>ui.theme, ()=> updateChartsTheme())

onMounted(async () => {
  await userStore.loadProfile(true)
  if (!userStore.userId) { router.push('/login'); return }
  await fetchSummary()
  await fetchFaceOverview()
  // 新增：加载审查统计与阈值
  await Promise.all([fetchReviewSummary(), fetchReviewThreshold()])
  window.addEventListener('resize', () => { chartFaceStatus && chartFaceStatus.resize() })
})
</script>

<template>
  <!-- 修改整体容器与导航样式，动态背景 -->
  <div class="min-h-screen flex font-sans" :class="ui.theme==='dark' ? 'bg-[#111827]' : 'bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white'">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
        <div class="flex items-center gap-6">
          <span class="text-[24px] font-['Pacifico'] text-primary select-none relative">
            logo
            <span v-if="faceRequired" class="absolute -top-1 -right-2 w-3 h-3 rounded-full bg-red-500 animate-pulse" title="人脸访问开启"></span>
          </span>
          <span class="text-lg font-semibold text-gray-700 hidden sm:inline flex items-center gap-2">
            管理员后台
            <span v-if="attentionTotal>0" class="inline-flex items-center gap-1 px-2 h-5 rounded-full bg-red-100 text-red-600 text-[11px] font-medium" title="需关注：VIP & 人脸即将到期 / 已过期">{{ attentionTotal }}</span>
          </span>
          <button class="text-xs px-2 py-1 rounded bg-white/60 border border-gray-300 hover:bg-white" @click="()=>router.push('/manage/students?role=VIP')">只看VIP</button>
        </div>
        <div class="flex items-center gap-4 text-sm">
          <SyllabusPicker />
          <button @click="ui.toggleTheme()" class="px-3 h-10 rounded-lg bg-white/60 border border-gray-200 hover:bg-white transition text-gray-600 flex items-center gap-1 text-xs">
            <i :class="ui.theme==='dark' ? 'fas fa-sun' : 'fas fa-moon'" class="text-primary"></i>
            <span>{{ ui.theme==='dark' ? '亮色' : '夜间' }}</span>
          </button>
          <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/60 border border-gray-200 text-gray-600">
            <div class="w-7 h-7 rounded-full overflow-hidden bg-gray-100">
              <img v-if="avatarUrl" :src="avatarUrl" alt="avatar" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-400"><i class="fas fa-user-shield"></i></div>
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
        <router-link to="/manage/students" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-users"></i><span>学生/教师管理</span>
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
        <!-- 新增：人脸到期管理入口 -->
        <router-link to="/manage/face-expiring" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-clock text-amber-500"></i><span>人脸到期管理</span>
          <span v-if="attentionTotal>0" class="ml-auto inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full bg-red-100 text-red-600 text-[10px] font-medium">{{ attentionTotal }}</span>
        </router-link>
        <!-- 题目审查统计 -->
        <router-link to="/manage/review-stats" class="group flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-primary/5 hover:text-primary transition">
          <i class="fas fa-list-check"></i><span>题目审查统计</span>
        </router-link>
      </nav>
      <div class="mt-auto pt-6 text-[10px] text-gray-400 tracking-wide">© 2024 考试系统</div>
    </aside>

    <!-- 主体内容 -->
    <main class="flex-1 pt-20 pb-10 px-6 lg:px-8 ml-60">
      <!-- 指标卡（精简样式） -->
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4 mb-6">
        <div class="rounded-xl border border-gray-200 bg-white p-4">
          <div class="flex items-start justify-between mb-2"><h3 class="text-[11px] font-medium tracking-wide text-gray-500">总用户</h3><i class="fas fa-users text-primary/70"></i></div>
          <div class="text-xl font-semibold text-gray-800">{{ totalUsers }}</div>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4">
          <div class="flex items-start justify-between mb-2"><h3 class="text-[11px] font-medium tracking-wide text-gray-500">学生</h3><i class="fas fa-user-graduate text-primary/70"></i></div>
          <div class="text-xl font-semibold text-gray-800">{{ studentCount }}</div>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4">
          <div class="flex items-start justify-between mb-2"><h3 class="text-[11px] font-medium tracking-wide text-gray-500">教师</h3><i class="fas fa-chalkboard-teacher text-primary/70"></i></div>
          <div class="text-xl font-semibold text-gray-800">{{ teacherCount }}</div>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4">
          <div class="flex items-start justify-between mb-2"><h3 class="text-[11px] font-medium tracking-wide text-gray-500">管理员</h3><i class="fas fa-user-shield text-primary/70"></i></div>
          <div class="text-xl font-semibold text-gray-800">{{ adminCount }}</div>
        </div>
      </div>

      <!-- 合并：VIP + 人脸 状态卡 -->
      <div class="grid gap-4 lg:grid-cols-3 mb-6">
        <div class="rounded-xl border border-gray-200 bg-white p-5 flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-gray-800 flex items-center gap-2"> 用户附加状态 <span v-if="attentionTotal>0" class="px-1.5 py-0.5 rounded bg-red-50 text-red-600 text-[10px] border border-red-200 cursor-pointer" @click="router.push('/manage/face-expiring')">需关注 {{ attentionTotal }}</span></h3>
            <div class="flex gap-2 text-gray-400">
              <i class="fas fa-crown text-amber-500"></i>
              <i class="fas fa-user-circle text-primary"></i>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4 text-[11px] text-gray-600">
            <div>
              <div class="text-xs font-medium text-gray-500 mb-1">VIP</div>
              <div class="space-y-1">
                <div>有效：<span class="font-semibold text-gray-800">{{ vipCount }}</span></div>
                <div>3日内到期：<button class="text-amber-600 hover:underline" @click="goVipExpiring">{{ vipExpiring3d }}</button></div>
              </div>
            </div>
            <div>
              <div class="text-xs font-medium text-gray-500 mb-1">人脸识别</div>
              <div class="space-y-1">
                <div>有效：<span class="font-semibold text-gray-800">{{ faceValid }}</span></div>
                <div>3日内到期：<button class="text-amber-600 hover:underline" @click="goFaceExpiring">{{ faceExpiring3d }}</button></div>
                <div>已过期：<button class="text-red-600 hover:underline" @click="goFaceExpired">{{ faceExpired }}</button></div>
              </div>
            </div>
          </div>
          <div class="mt-4 flex items-center gap-3">
            <button @click="toggleFaceRequired" :disabled="faceToggleLoading" class="h-8 px-3 rounded text-xs font-medium border transition" :class="faceRequired ? 'bg-primary text-black border-primary hover:bg-primary/90' : 'bg-gray-100 text-gray-700 border-gray-700 hover:bg-gray-200'">{{ faceRequired ? '人脸已开启' : '人脸已关闭' }}</button>
            <button @click="router.push('/manage/face-expiring')" class="h-8 px-3 rounded text-xs font-medium border bg-white hover:bg-gray-50">人脸到期管理</button>
          </div>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-5 lg:col-span-2">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-gray-800">人脸状态分布</h3>
            <button class="text-xs text-gray-500 hover:text-gray-700" @click="refreshOverview">刷新</button>
          </div>
          <div id="adminFaceStatusPie" class="h-[220px]"></div>
        </div>
      </div>

      <!-- 新增：题目审查（全局） 小卡片 -->
      <div class="rounded-xl border border-gray-200 bg-white p-5 mb-6">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-gray-800">题目审查（全局）</h3>
          <div class="text-[11px] text-gray-500">共识阈值：<span class="font-semibold text-gray-800">{{ reviewThreshold ?? '-' }}</span> 人</div>
        </div>
        <div class="flex flex-wrap items-center gap-3 text-[12px]">
          <span class="px-2 py-1 rounded bg-amber-50 text-amber-700 border border-amber-200">待处理：{{ reviewStats.total }}</span>
          <span class="px-2 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200">考纲空：{{ reviewStats.missing_kp }}</span>
          <span class="px-2 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">一级空：{{ reviewStats.missing_primary }}</span>
          <span class="px-2 py-1 rounded bg-teal-50 text-teal-700 border border-teal-200">解析空：{{ reviewStats.missing_analysis }}</span>
          <span class="px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200">未审：{{ reviewStats.unreviewed }}</span>
          <div class="ml-auto flex items-center gap-2">
            <router-link to="/manage/review-queue" class="px-3 h-8 rounded bg-primary/90 text-white text-xs flex items-center">待审核列表</router-link>
            <router-link to="/manage/review-stats" class="px-3 h-8 rounded border text-xs bg-white hover:bg-gray-50">审查统计</router-link>
          </div>
        </div>
      </div>

      <!-- 可折叠：成绩 & 结构 面板 -->
      <div class="rounded-xl border border-gray-200 bg-white mb-6">
        <button class="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50" @click="showStatsPanels=!showStatsPanels">
          <span class="flex items-center gap-2"><i class="fas fa-chart-bar text-primary"></i>成绩与结构</span>
          <i :class="showStatsPanels ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="text-gray-400"></i>
        </button>
        <transition name="fade">
          <div v-if="showStatsPanels" class="p-4 border-t">
            <div class="grid lg:grid-cols-2 gap-4">
              <div class="rounded-lg border border-gray-100 p-4">
                <div class="flex items-center justify-between mb-3"><h3 class="text-xs font-semibold text-gray-600">成绩分布（人数）</h3><i class="fas fa-chart-column text-primary/70"></i></div>
                <div id="adminScoreBar" class="h-[260px]"></div>
              </div>
              <div class="rounded-lg border border-gray-100 p-4 flex flex-col">
                <div class="flex items-center justify-between mb-3"><h3 class="text-xs font-semibold text-gray-600">人员结构</h3><i class="fas fa-people-group text-primary/70"></i></div>
                <div id="adminRolePie" class="h-[260px]"></div>
                <div class="mt-auto grid grid-cols-3 text-[11px] text-gray-600 gap-2 pt-2 border-t">
                  <div class="flex flex-col"><span class="text-gray-400">学生</span><span class="font-semibold text-gray-800">{{ studentCount }}</span></div>
                  <div class="flex flex-col"><span class="text-gray-400">教师</span><span class="font-semibold text-gray-800">{{ teacherCount }}</span></div>
                  <div class="flex flex-col"><span class="text-gray-400">管理员</span><span class="font-semibold text-gray-800">{{ adminCount }}</span></div>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- 最近成绩记录（压缩，仅显示前5条） -->
      <div class="rounded-xl border border-gray-200 bg-white p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-gray-800">最近成绩（前5条）</h3>
          <router-link to="/manage/scores" class="text-primary text-xs hover:underline">查看全部</router-link>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-[760px] w-full text-xs">
            <thead>
              <tr class="bg-gray-50 text-gray-600 text-left">
                <th class="py-2 px-3 font-medium">学生</th>
                <th class="py-2 px-3 font-medium">班级</th>
                <th class="py-2 px-3 font-medium">考试</th>
                <th class="py-2 px-3 font-medium">得分/总分</th>
                <th class="py-2 px-3 font-medium">提交时间</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="r in truncatedRecords" :key="r.record_id" class="hover:bg-gray-50">
                <td class="py-2 px-3">{{ r.username }}</td>
                <td class="py-2 px-3">{{ r.classroom }}</td>
                <td class="py-2 px-3">{{ r.exam_title }}</td>
                <td class="py-2 px-3">{{ r.score }} / {{ r.full_score }}</td>
                <td class="py-2 px-3">{{ r.submit_time }}</td>
              </tr>
              <tr v-if="!truncatedRecords.length">
                <td colspan="5" class="py-6 text-center text-gray-400">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* 简化视觉层次 */
.fade-enter-active,.fade-leave-active{ transition: all .18s ease }
.fade-enter-from,.fade-leave-to{ opacity:0; transform: translateY(-4px) }
</style>