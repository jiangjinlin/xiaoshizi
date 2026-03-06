<template>
  <div class="min-h-screen flex flex-col bg-gray-50 font-sans">
    <!-- 顶部导航 -->
    <nav class="sticky top-0 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="h-16 flex items-center justify-between gap-6 md:gap-8">
          <div class="flex items-center gap-6 md:gap-10">
            <AppLogo :height="40" class="cursor-pointer" @click="$router.push('/')" />
            <ul class="hidden md:flex items-center gap-4 xl:gap-8 text-sm font-medium">
              <li v-for="l in navLinks" :key="l.label">
                <a :href="l.href" @click.prevent="l.to && $router.push(l.to)" class="group relative inline-flex items-center px-1.5 py-1 text-gray-700 hover:text-primary transition-colors">
                  <span>{{ l.label }}</span>
                  <span class="pointer-events-none absolute left-0 -bottom-0.5 h-0.5 w-0 bg-primary transition-all duration-300 group-hover:w-full"></span>
                </a>
              </li>
            </ul>
          </div>
          <!-- 右侧按钮：登录 + 网络设置 -->
          <div class="flex items-center gap-3">
            <button class="rounded-button bg-primary text-white px-4 md:px-5 py-2 text-sm font-medium hover:bg-primary/90 active:scale-[.97] transition" @click="$router.push('/login')">登录系统</button>
            <button class="rounded-button bg-white text-gray-700 px-3 md:px-4 py-2 text-sm border border-gray-200 hover:bg-gray-50 active:scale-[.98] transition flex items-center gap-2" @click="openLan">
              <i class="fas fa-network-wired text-primary"></i><span>网络设置</span>
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 网络设置弹窗（新版：移到首页） -->
    <div v-if="showLan" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="w-[92%] max-w-md rounded-xl border border-gray-200 bg-white shadow-lg p-5" @click.stop>
        <div class="text-base font-semibold text-gray-800 mb-4">网络设置</div>
        <div class="space-y-5 text-sm">
          <div>
            <div class="text-[13px] font-medium text-gray-800 mb-2">后端 API 地址（局域网）</div>
            <label class="flex items-center gap-2 mb-2">
              <input type="checkbox" v-model="lanEnabled" @change="computePreview" /> 启用局域网 IP
            </label>
            <div>
              <div class="text-xs text-gray-500 mb-1">服务器 IP 或主机:端口（留空默认 8000）</div>
              <input v-model.trim="lanHost" @input="computePreview" placeholder="如 192.168.1.88 或 192.168.1.88:8000"
                     class="w-full h-10 px-3 rounded border border-gray-300 bg-white/70 focus:bg-white outline-none focus:ring-2 focus:ring-primary/30" />
            </div>
            <div class="mt-2 text-xs text-gray-500">API 将使用：<span class="text-gray-800 font-mono">{{ lanPreview }}</span></div>
          </div>
        </div>
        <div class="mt-5 flex items-center justify-end gap-2">
          <button class="h-9 px-4 rounded border text-sm" @click="showLan=false">取消</button>
          <button class="h-9 px-4 rounded bg-primary text-white text-sm" @click="saveLan">保存</button>
        </div>
      </div>
    </div>

    <!-- Hero 区 -->
    <section class="relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-primary/10 via-indigo-100 to-white"></div>
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 py-16 md:py-24 lg:py-28 grid md:grid-cols-2 gap-12 lg:gap-14 items-center">
        <div class="space-y-6 md:space-y-8">
          <!-- 新增：LOGO + 标题 并排布局（移动端堆叠，桌面端200px高） -->
          <div class="flex flex-col md:flex-row items-start md:items-center gap-4 md:gap-6">
            <!-- 移动端较小LOGO -->
            <AppLogo :height="120" alt="系统Logo" class="block md:hidden flex-shrink-0" />
            <!-- 桌面端 200px 高LOGO -->
            <AppLogo :height="180" alt="系统Logo" class="hidden md:block flex-shrink-0" />
            <h1 class="text-3xl md:text-3xl font-bold leading-tight text-gray-900 md:flex-1 min-w-0">基于人脸识别与 Office 智能评分的无纸化考试系统</h1>
          </div>
          <p class="text-base md:text-lg lg:text-xl text-gray-600 leading-relaxed">集成人脸身份核验与 Office（Word/Excel/PPT）自动评分，为院校提供标准化、可追溯、可分析的全流程考试平台。</p>
          <div class="flex flex-wrap gap-3 md:gap-4">
            <button class="rounded-button bg-primary text-white px-6 md:px-7 py-2.5 md:py-3 text-base font-medium shadow-sm hover:shadow-md hover:bg-primary/90 transition" @click="$router.push('/login')">开始使用</button>
            <button class="rounded-button bg-white text-primary px-6 md:px-7 py-2.5 md:py-3 text-base font-medium border border-primary/60 hover:bg-primary/5 transition" @click="scrollToAnchor('#features')">了解更多</button>
          </div>
          <div class="flex flex-wrap gap-x-6 gap-y-3 pt-2 md:pt-4 text-xs md:text-sm text-gray-500">
            <div class="flex items-center gap-2"><i class="fas fa-user-shield text-primary"></i><span>人脸识别防替考</span></div>
            <div class="flex items-center gap-2"><i class="fas fa-file-word text-primary"></i><span>Office 智能评分</span></div>
            <div class="flex items-center gap-2"><i class="fas fa-route text-primary"></i><span>过程可追踪</span></div>
          </div>
        </div>
        <div class="relative">
          <div class="absolute -inset-6 bg-gradient-to-tr from-primary/20 via-indigo-200/30 to-white rounded-3xl blur-2xl"></div>
          <div class="relative rounded-2xl border border-gray-200 bg-white/60 backdrop-blur p-5 md:p-6 shadow-sm hover:shadow-md transition">
            <div class="grid grid-cols-2 gap-4 md:gap-6">
              <div v-for="feat in heroStats" :key="feat.label" class="rounded-xl bg-gradient-to-br from-white to-gray-50 border border-gray-100 p-3 md:p-4 flex flex-col gap-1.5 md:gap-2">
                <div class="flex items-center gap-2 text-xs md:text-sm font-medium text-gray-500"><i :class="feat.icon + ' text-primary'" /> {{ feat.label }}</div>
                <div class="text-xl md:text-2xl font-semibold text-gray-900 leading-snug">{{ feat.value }}</div>
              </div>
            </div>
            <div class="mt-4 md:mt-6 text-[10px] md:text-xs text-gray-500">数据实时来源：{{ examTitle || '暂无考试' }} <span v-if="lastUpdated" class="ml-2">更新: {{ formatTime(lastUpdated) }}</span></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 核心功能 -->
    <section id="features" class="py-16 md:py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="flex items-end justify-between flex-wrap gap-4 mb-10 md:mb-14">
          <div>
            <h2 class="text-2xl md:text-3xl font-bold text-gray-900">核心功能特点</h2>
            <p class="text-gray-500 mt-2 text-xs md:text-sm">围绕考试全流程的安全、标准化与分析能力建设</p>
          </div>
        </div>
        <div class="grid gap-6 md:gap-8 md:grid-cols-3">
          <div v-for="f in features" :key="f.title" class="group rounded-2xl bg-gray-50/60 border border-gray-100 p-6 md:p-8 flex flex-col hover:bg-white hover:shadow-lg hover:-translate-y-1 transition">
            <div class="w-12 h-12 md:w-14 md:h-14 rounded-xl flex items-center justify-center mb-5 md:mb-6 bg-gradient-to-br from-primary/10 to-indigo-100 text-primary">
              <i :class="f.icon + ' text-xl md:text-2xl'" />
            </div>
            <h3 class="text-base md:text-lg font-semibold mb-2 md:mb-3 text-gray-900">{{ f.title }}</h3>
            <p class="text-gray-600 text-xs md:text-sm leading-relaxed flex-1">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 数据概览 -->
    <section id="overview" class="py-16 md:py-20 bg-gray-50/60">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="flex items-center justify-between flex-wrap gap-4 mb-8 md:mb-10">
          <div>
            <h2 class="text-2xl md:text-3xl font-bold text-gray-900">系统数据概览</h2>
            <p class="text-gray-600 text-xs md:text-sm mt-2">数据来源：{{ examTitle || '暂无可用考试' }} <span v-if="avgScore!==null" class="ml-2">平均分：{{ avgScore }} | 通过率：{{ passRate }}%</span></p>
          </div>
        </div>
        <div class="grid gap-6 md:gap-8 lg:grid-cols-2">
          <div class="bg-white rounded-2xl border border-gray-100 p-5 md:p-8 shadow-sm hover:shadow-md transition">
            <div class="flex items-center justify-between mb-4 md:mb-6">
              <h3 class="text-base md:text-lg font-semibold text-gray-900">考试成绩分布</h3>
              <i class="fas fa-chart-column text-primary"></i>
            </div>
            <div id="scoreChart" class="w-full h-72 md:h-80"></div>
          </div>
          <div class="bg-white rounded-2xl border border-gray-100 p-5 md:p-8 shadow-sm hover:shadow-md transition">
            <div class="flex items-center justify-between mb-4 md:mb-6">
              <h3 class="text-base md:text-lg font-semibold text-gray-900">题型正确率分析</h3>
              <i class="fas fa-percentage text-primary"></i>
            </div>
            <div id="accuracyChart" class="w-full h-72 md:h-80"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能对比 -->
    <section class="py-16 md:py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="flex items-end justify-between flex-wrap gap-4 mb-8 md:mb-10">
          <div>
            <h2 class="text-2xl md:text-3xl font-bold text-gray-900">方案对比</h2>
            <p class="text-gray-500 mt-2 text-xs md:text-sm">传统线下 / 传统网考 / 本系统</p>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-[880px] w-full text-sm">
            <thead>
              <tr class="bg-primary/5 text-gray-700">
                <th class="py-3 px-3 text-left font-semibold">能力点</th>
                <th class="py-3 px-3 text-left font-semibold">传统线下</th>
                <th class="py-3 px-3 text-left font-semibold">传统网考</th>
                <th class="py-3 px-3 text-left font-semibold">本系统</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="row in compareRows" :key="row.name" class="hover:bg-primary/5">
                <td class="py-2.5 px-3 text-gray-800">{{ row.name }}</td>
                <td class="py-2.5 px-3"> <i :class="row.offline ? 'fas fa-check text-emerald-600' : 'fas fa-xmark text-red-500'"/> <span class="ml-2 text-gray-700">{{ row.offlineText }}</span></td>
                <td class="py-2.5 px-3"> <i :class="row.online ? 'fas fa-check text-emerald-600' : 'fas fa-xmark text-red-500'"/> <span class="ml-2 text-gray-700">{{ row.onlineText }}</span></td>
                <td class="py-2.5 px-3"> <i class="fas fa-check text-emerald-600"/> <span class="ml-2 text-gray-800 font-medium">{{ row.oursText }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- 使用流程 -->
    <section id="flow" class="py-16 md:py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="flex items-end justify-between flex-wrap gap-4 mb-10 md:mb-14">
          <div>
            <h2 class="text-2xl md:text-3xl font-bold text-gray-900">使用流程</h2>
            <p class="text-gray-500 text-xs md:text-sm mt-2">四步完成完整考试闭环</p>
          </div>
        </div>
        <div class="grid gap-6 md:gap-8 md:grid-cols-4">
          <div v-for="(s,i) in steps" :key="s.title" class="relative text-center px-2 group">
            <div class="w-16 h-16 md:w-20 md:h-20 mx-auto rounded-full bg-gradient-to-br from-primary/10 to-indigo-100 flex items-center justify-center mb-4 md:mb-5 ring-1 ring-primary/10 group-hover:scale-105 transition">
              <i :class="s.icon + ' text-xl md:text-2xl text-primary'" />
            </div>
            <h3 class="text-sm md:text-base font-semibold mb-1.5 md:mb-2 text-gray-900">{{ i+1 }}. {{ s.title }}</h3>
            <p class="text-gray-600 text-xs md:text-sm">{{ s.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer id="footer" class="bg-gray-900 text-gray-300 pt-14 md:pt-16 pb-8 md:pb-10 mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="grid gap-10 md:gap-12 md:grid-cols-4">
          <div class="space-y-4">
            <p class="text-xs md:text-sm leading-relaxed text-gray-400">智能无纸化考试系统，集成人脸识别与 Office 自动评分，专注可信身份、过程追踪与结果分析。</p>
          </div>
          <div>
            <h4 class="text-xs md:text-sm font-semibold tracking-wider text-white mb-3 md:mb-4">快速链接</h4>
            <ul class="space-y-1.5 md:space-y-2 text-xs md:text-sm">
              <li v-for="q in quickLinks" :key="q.label"><a :href="q.href" class="hover:text-white transition">{{ q.label }}</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-xs md:text-sm font-semibold tracking-wider text-white mb-3 md:mb-4">联系我们</h4>
            <ul class="space-y-1.5 md:space-y-2 text-xs md:text-sm text-gray-400">
              <li>电话：19961148075</li>
              <li>邮箱：2300035250@qq.com</li>
              <li>地址：海科路皇家女子学院</li>
            </ul>
          </div>
          <div>
            <h4 class="text-xs md:text-sm font-semibold tracking-wider text-white mb-3 md:mb-4">关注我们</h4>
            <div class="flex gap-3 md:gap-4">
              <a v-for="s in socials" :key="s.icon" href="#" class="w-9 h-9 md:w-10 md:h-10 rounded-lg flex items-center justify-center bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition">
                <i :class="s.icon + ' text-lg md:text-xl'" />
              </a>
            </div>
          </div>
        </div>
        <div class="mt-10 md:mt-14 pt-5 md:pt-6 border-t border-white/10 text-center text-[10px] md:text-xs text-gray-500">© 2024 中职计算机专业无纸化考试系统. All rights reserved.</div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { apiOverview } from '../api/index'
import { getLanConfig, setLanEnabled, setLanHost, getDefaultBaseURL } from '../api/http'
import AppLogo from '../components/AppLogo.vue'

// 新增：网络设置状态与方法
const showLan = ref(false)
const lanEnabled = ref(getLanConfig().enabled)
const lanHost = ref((typeof window !== 'undefined' ? localStorage.getItem('lan_host') : '') || '')
const lanPreview = ref(getLanConfig().baseURL)
function openLan() {
  const cfg = getLanConfig()
  lanEnabled.value = cfg.enabled
  lanHost.value = (typeof window !== 'undefined' ? localStorage.getItem('lan_host') : '') || ''
  lanPreview.value = cfg.baseURL
  showLan.value = true
}
function computePreview() {
  if (!lanEnabled.value) {
    lanPreview.value = getDefaultBaseURL()
  } else {
    try {
      let h = (lanHost.value || '').trim()
      if (!h) {
        lanPreview.value = getDefaultBaseURL()
      } else {
        if (!/^https?:\/\//i.test(h)) {
          if (!/:\d+$/.test(h) && !/]$/.test(h)) h = h + ':8000'
          h = 'http://' + h
        }
        lanPreview.value = h
      }
    } catch {
      lanPreview.value = getDefaultBaseURL()
    }
  }
}
function saveLan() {
  setLanHost(lanHost.value || '')
  setLanEnabled(!!lanEnabled.value)
  lanPreview.value = getLanConfig().baseURL
  showLan.value = false
}

// 原有：导航配置等
const navLinks = [
  { label: '首页', to: '/', href: '#' },
  { label: '系统介绍', href: '#features' },
  { label: '功能特点', href: '#features' },
  { label: '数据概览', href: '#overview' },
  { label: '使用流程', href: '#flow' },
  { label: '联系我们', to: '/contact', href: '#' }
]

// Hero 右侧实时统计
const heroStats = ref([
  { key: 'examTitle', label: '当前考试', value: '--', icon: 'fas fa-file-lines' },
  { key: 'avgScore', label: '平均分', value: '--', icon: 'fas fa-chart-line' },
  { key: 'passRate', label: '通过率', value: '--', icon: 'fas fa-check-circle' },
  { key: 'participants', label: '参与考生', value: '--', icon: 'fas fa-user-graduate' }
])

// 功能列表
const features = [
  { icon: 'fas fa-user-check', title: '人脸身份认证', desc: '接入本地/云端人脸识别，支持考前与过程随机核验，严防替考。' },
  { icon: 'fas fa-file-word', title: 'Office 智能评分', desc: 'Word/Excel/PPT 自动评分，细化命中项与扣分项，支持人工复核与回放。' },
  { icon: 'fas fa-bullseye', title: '考纲练习与分析', desc: '基于考纲/知识点的专项练习与补弱，实时可视化统计薄弱点。' }
]

// 使用流程
const steps = [
  { icon: 'fas fa-user-plus', title: '注册绑定', desc: '上传人脸并绑定账号。' },
  { icon: 'fas fa-user-shield', title: '身份核验', desc: '考前/考中进行人脸核验，确保本人参考。' },
  { icon: 'fas fa-edit', title: '在线答题', desc: '统一作答，多题型覆盖；Office 作业上传后自动评分。' },
  { icon: 'fas fa-chart-bar', title: '成绩分析', desc: '生成可视化报表，支持考纲维度统计与对比。' }
]

// 页脚链接
const quickLinks = [
  { label: '系统介绍', href: '#features' },
  { label: '功能特点', href: '#features' },
  { label: '技术支持', href: '#footer' }
]

const socials = [
  { icon: 'fab fa-weixin' },
  { icon: 'fab fa-weibo' }
]

// 原有图表数据
const examTitle = ref('')
const avgScore = ref(null)
const passRate = ref(null)
const scoreBins = ref(['60分以下', '60-70分', '70-80分', '80-90分', '90分以上'])
const scoreCounts = ref([0, 0, 0, 0, 0])
const accuracyData = ref([
  { value: 0, name: '选择题' },
  { value: 0, name: '多选题' },
  { value: 0, name: '判断题' }
])
const lastUpdated = ref(null)

// 图表实例 & 监听
let scoreChartInstance = null
let accuracyChartInstance = null
let resizeHandler = null

function ensureCharts() {
  if (!window.echarts) return
  if (!scoreChartInstance) {
    scoreChartInstance = window.echarts.init(document.getElementById('scoreChart'))
  }
  if (!accuracyChartInstance) {
    accuracyChartInstance = window.echarts.init(document.getElementById('accuracyChart'))
  }
}

function refreshCharts() {
  if (!window.echarts) return
  ensureCharts()
  if (!scoreChartInstance || !accuracyChartInstance) return
  scoreChartInstance.setOption({
    animation: false,
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 12, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: scoreBins.value, axisTick: { alignWithLabel: true } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ data: scoreCounts.value, type: 'bar', barMaxWidth: 40, itemStyle: { color: '#2563eb', borderRadius: [4,4,0,0] } }]
  }, true)
  accuracyChartInstance.setOption({
    animation: false,
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    series: [{
      type: 'pie',
      radius: ['42%','70%'],
      data: accuracyData.value,
      itemStyle: {
        color: function (params) {
          const colors = ['#2563eb', '#4f46e5', '#6366f1', '#818cf8']
          return colors[params.dataIndex]
        }
      },
      label: { formatter: '{b}\n{c}%' }
    }]
  }, true)
}

// 轻量节流更新
let chartUpdateRaf = null
function scheduleChartUpdate() {
  if (chartUpdateRaf) cancelAnimationFrame(chartUpdateRaf)
  chartUpdateRaf = requestAnimationFrame(() => {
    refreshCharts()
    chartUpdateRaf = null
  })
}

function updateHeroStats() {
  const participants = scoreCounts.value.reduce((a, b) => a + b, 0)
  const map = {
    examTitle: examTitle.value || '--',
    avgScore: avgScore.value === null ? '--' : avgScore.value,
    passRate: passRate.value === null ? '--' : passRate.value + '%',
    participants: participants || '--'
  }
  heroStats.value = heroStats.value.map(item => ({ ...item, value: map[item.key] }))
  lastUpdated.value = Date.now()
}

function formatTime(t) { return new Date(t).toLocaleTimeString('zh-CN', { hour12: false }) }

// 分布计算回退: 若后端给 raw_scores
function computeFromRaw(scores = []) {
  if (!Array.isArray(scores) || !scores.length) return
  const bins = [0,0,0,0,0]
  let sum = 0
  let pass = 0
  scores.forEach(s => {
    if (typeof s !== 'number') return
    sum += s
    if (s >= 60) pass++
    if (s < 60) bins[0]++
    else if (s < 70) bins[1]++
    else if (s < 80) bins[2]++
    else if (s < 90) bins[3]++
    else bins[4]++
  })
  scoreCounts.value = bins
  avgScore.value = +(sum / scores.length).toFixed(1)
  passRate.value = +((pass / scores.length) * 100).toFixed(1)
}

async function loadOverview() {
  try {
    const { data } = await apiOverview()
    if (data?.success) {
      examTitle.value = data.exam_title || ''
      // 若后端直接给平均与通过率使用, 否则计算
      if (typeof data.avg_score === 'number') avgScore.value = +data.avg_score.toFixed?.(1) || data.avg_score
      if (typeof data.pass_rate === 'number') passRate.value = +data.pass_rate.toFixed?.(1) || data.pass_rate
      if (Array.isArray(data.score_bins) && Array.isArray(data.score_counts)) {
        scoreBins.value = data.score_bins
        scoreCounts.value = data.score_counts
      } else if (Array.isArray(data.raw_scores)) {
        computeFromRaw(data.raw_scores)
      }
      if (Array.isArray(data.accuracy)) accuracyData.value = data.accuracy.map(i => ({ ...i, value: Number(i.value) || 0 }))
      // 如果仍缺少平均/通过率尝试本地再推导
      if (avgScore.value === null || passRate.value === null) {
        const total = scoreCounts.value.reduce((a,b)=>a+b,0)
        // 尝试从分布估计 (加权取区间均值)
        if (total > 0) {
          const midValues = [50, 65, 75, 85, 95]
          const sum = scoreCounts.value.reduce((acc,c,i)=> acc + c * midValues[i], 0)
          if (avgScore.value === null) avgScore.value = +(sum / total).toFixed(1)
          if (passRate.value === null) {
            const pass = total - scoreCounts.value[0]
            passRate.value = +((pass / total) * 100).toFixed(1)
          }
        }
      }
    }
  } catch (e) {
    // ignore
  } finally {
    updateHeroStats()
    await nextTick()
    scheduleChartUpdate()
  }
}

function scrollToAnchor(hash) {
  const el = document.querySelector(hash)
  if (!el) return
  window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 70, behavior: 'smooth' })
}

// 移除：统计数字动画（无后端数据则取消）
// const statsRef = ref(null)
// const kpis = ref([...])
// let statsObs = null
// function animateCount(...) { ... }
// function observeStats(){ ... }
// function tryFillKPIsFromOverview(){ ... }

onMounted(() => {
  if (!window.echarts) {
    setTimeout(() => { loadOverview() }, 200)
  } else {
    loadOverview()
  }
  resizeHandler = () => scheduleChartUpdate()
  window.addEventListener('resize', resizeHandler)
  // 不再调用 observeStats 或 tryFillKPIsFromOverview
})

onBeforeUnmount(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  if (scoreChartInstance) { scoreChartInstance.dispose(); scoreChartInstance = null }
  if (accuracyChartInstance) { accuracyChartInstance.dispose(); accuracyChartInstance = null }
  // 已移除 statsObs
})

// 功能对比表格数据（补齐更全面的能力点）
const compareRows = ref([
  { name: '身份核验防替考', offline: false, online: false, offlineText: '人工核验，易替考', onlineText: '账号密码，易代考', oursText: '人脸识别 + 考中随机核验' },
  { name: '监考方式与规范', offline: true,  online: true,  offlineText: '现场监考，人工记录', onlineText: '在线监考（基础）', oursText: '人脸 + 日志留痕 + 异常告警' },
  { name: 'Office 自动评分', offline: false, online: false, offlineText: '人工批改，效率低', onlineText: '难以覆盖 Office 操作', oursText: 'Word/Excel/PPT 自动评分' },
  { name: '题目类型覆盖', offline: true,  online: true,  offlineText: '纸笔/上机手动批改', onlineText: '客观题为主', oursText: '客观题 + Office 操作题' },
  { name: '过程留痕与回放', offline: false, online: true,  offlineText: '痕迹少，难复盘', onlineText: '有限日志', oursText: '过程日志 + 文件留存 + 可回放' },
  { name: '题库与考纲管理', offline: false, online: true,  offlineText: '人工维护，难共享', onlineText: '基础管理', oursText: '按考纲/知识点结构化管理' },
  { name: '统计分析可视化', offline: false, online: true,  offlineText: '统计困难', onlineText: '基础统计', oursText: '题型/知识点/学生多维分析' },
  { name: '异常恢复（断网/中断）', offline: true,  online: false, offlineText: '可人工处理', onlineText: '中断易丢失', oursText: '断线续作 + 提交校验' },
  { name: '安全与防舞弊', offline: false, online: false, offlineText: '易替考/作弊', onlineText: '账号代考/屏幕外作弊', oursText: '人脸 + 时序校验 + 异常告警' },
  { name: '隐私与合规', offline: true,  online: false, offlineText: '纸质保管', onlineText: '数据外泄风险', oursText: '可私有化部署/权限可控' },
  { name: '部署与运维成本', offline: true,  online: false, offlineText: '低（无系统）', onlineText: '中（依赖多）', oursText: '中（校内私有化部署）' },
  { name: '易用性与门槛', offline: true,  online: true,  offlineText: '几乎无学习成本', onlineText: '基础操作', oursText: '教师/学生端简洁易用' },
])
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
/* use global .text-primary/.bg-primary/.rounded-button from tokens.css */
</style>
