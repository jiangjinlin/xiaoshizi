<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiLogout, apiSubmitExam, apiFaceStatus, apiScoreQuery } from '../api/index'
import { useExamStore } from '../stores/exam'
import { useSyllabusStore } from '../stores/syllabus'
import AppLogo from '../components/AppLogo.vue'

const examStore = useExamStore()
const s = useSyllabusStore()
const filterType = ref('all')
const totalVisible = ref(0)
const router = useRouter()
const route = useRoute()
const isScrolled = ref(false)

// 已提交考试映射：exam_id -> true
const submittedMap = ref({})

// 当前场次（从路由或会话中恢复）
const selectedExamId = ref('')

const filterBtns = [
  { label: '全部', type: 'all' },
  { label: '单选题', type: '单选' },
  { label: '多选题', type: '多选' },
  { label: '判断题', type: '判断' },
  { label: '操作题', type: '操作' }
]

const filteredExams = computed(() => {
  const id = selectedExamId.value
  if (!id) return []
  return (examStore.exams || []).filter(ex => String(ex.exam_id || ex.id) === String(id))
})

function computeTotalVisible() {
  let total = 0
  filteredExams.value.forEach(exam => {
    total += filterType.value === 'all' ? exam.questions.length : exam.questions.filter(q => q.type === filterType.value).length
  })
  totalVisible.value = total
}

function onFilter(type) {
  filterType.value = type
  computeTotalVisible()
  window.scrollTo({ top:0, behavior:'smooth' })
}

async function ensureSignedIn(examId) {
  try {
    const { data } = await apiFaceStatus({ exam_id: examId })
    if (!data?.signed_in) {
      router.push({ path:'/signin', query:{ exam_id: String(examId) } })
      return false
    }
    return true
  } catch {
    router.push({ path:'/signin', query:{ exam_id: String(examId) } })
    return false
  }
}

async function submitExam(exam) {
  const eid = Number(exam.exam_id || exam.id)
  if (!eid || String(eid) !== String(selectedExamId.value)) {
    alert('当前页面与考试场次不一致，请返回重试')
    router.replace('/exam_select')
    return
  }
  if (submittedMap.value[eid]) {
    alert('该考试已参加，不能再次进入考试')
    return
  }
  const ok = await ensureSignedIn(eid)
  if (!ok) return
  const form = new FormData()
  form.append('exam_id', eid)
  const answers = {}
  ;(exam.questions || []).forEach(q => {
    if (q.type === '单选' || q.type === '判断') {
      const el = document.querySelector(`input[name='answer_${exam.exam_id}_${q.id}']:checked`)
      answers[q.id] = el ? el.value : ''
    } else if (q.type === '多选') {
      const els = document.querySelectorAll(`input[name='answer_${exam.exam_id}_${q.id}']:checked`)
      answers[q.id] = Array.from(els).map(i => i.value)
    } else if (q.type === '操作') {
      const fileInput = document.querySelector(`input[type='file'][name='answer_${exam.exam_id}_${q.id}']`)
      const file = fileInput?.files?.[0]
      if (file) form.append(String(q.id), file)
    }
  })
  form.append('answers', JSON.stringify(answers))
  try {
    await apiSubmitExam(form)
    await loadSubmitted()
    router.push({ name:'studentHome' })
  } catch (e) {
    alert('提交失败，请重试')
  }
}

async function loadSubmitted(){
  try{
    const { data } = await apiScoreQuery()
    const map = {}
    if (data?.success && Array.isArray(data.score_list)){
      data.score_list.forEach(r => { if (r && (r.exam_id!=null)) map[Number(r.exam_id)] = true })
    }
    submittedMap.value = map
  }catch{ submittedMap.value = {} }
}

function extractFirstUrl(text) {
  if (!text) return ''
  const m = String(text).match(/https?:\/\/[^\s)\]}]+/i)
  return m ? m[0] : ''
}
function detectOfficeType(urlOrContentUrl = '') {
  const u = String(urlOrContentUrl || '').toLowerCase()
  if (u.endsWith('.doc') || u.endsWith('.docx')) return 'word'
  if (u.endsWith('.xls') || u.endsWith('.xlsx')) return 'excel'
  if (u.endsWith('.ppt') || u.endsWith('.pptx')) return 'ppt'
  return 'word'
}
function getOfficeAppName(question) {
  const url = question.template_url || extractFirstUrl(question.content)
  const t = detectOfficeType(url)
  return t === 'excel' ? 'Excel' : (t === 'ppt' ? 'PPT' : 'Word')
}
function openOfficeForQuestion(question) {
  const url = question.template_url || extractFirstUrl(question.content)
  if (!url) { alert('未配置可用的模板地址'); return }
  const t = detectOfficeType(url)
  const scheme = t === 'excel' ? 'ms-excel' : (t === 'ppt' ? 'ms-powerpoint' : 'ms-word')
  const msUri = `${scheme}:ofe|u|${encodeURI(url)}`
  try { window.location.href = msUri } catch { window.open(msUri, '_blank') }
}

function goStudent() { router.push({ name:'studentHome' }) }
async function handleLogout() {
  try { await apiLogout() } catch {}
  localStorage.removeItem('user_id')
  s.clear()
  router.push({ name:'login' })
}
function handleScroll(){ isScrolled.value = window.scrollY > 8 }

function ensureExamIdFromRoute(){
  let id = route?.query?.exam_id ? String(route.query.exam_id) : ''
  if (!id){
    try{ id = sessionStorage.getItem('last_exam_id') || '' }catch{}
  }
  if (!id){ router.replace('/exam_select'); return false }
  selectedExamId.value = id
  try{ sessionStorage.setItem('last_exam_id', String(id)) }catch{}
  return true
}

onMounted(async () => {
  if (!ensureExamIdFromRoute()) return
  handleScroll()
  window.addEventListener('scroll', handleScroll, { passive:true })
  await loadSubmitted()
  await examStore.fetchExams()
  // 若未找到对应考试，跳转选择页
  if (!filteredExams.value.length){ router.replace('/exam_select'); return }
  computeTotalVisible()
})
onUnmounted(() => window.removeEventListener('scroll', handleScroll))

function hasInlineChoices(text){
  const t = String(text||'')
  // 检测类似 "A.", "A、", "A．", "A:" 等
  return /(^|[\n\r])\s*[A-D]\s*[。.、．:：]/.test(t)
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <!-- 顶部导航：默认透明，滚动后出现背景与描边 -->
    <nav :class="['fixed top-0 left-0 right-0 h-16 z-50 transition-all duration-300', isScrolled ? 'bg-white/80 backdrop-blur border-b border-gray-200 shadow-sm' : 'bg-transparent']">
      <div class="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="goStudent" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">考试作答</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <button class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition" @click="handleLogout">退出</button>
        </div>
      </div>
    </nav>

    <!-- 主体 -->
    <div class="max-w-5xl mx-auto pt-24 pb-20 px-4 lg:px-6">
      <!-- 顶部题型筛选条 -->
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur p-5 mb-6 shadow-sm">
        <div class="flex flex-wrap gap-3 items-center justify-center">
          <button v-for="btn in filterBtns" :key="btn.type" @click="onFilter(btn.type)"
            :class="['px-4 h-10 rounded-lg text-sm font-medium transition border', filterType===btn.type ? 'bg-primary text-white border-primary shadow-sm' : 'bg-white/60 border-gray-300 text-gray-600 hover:bg-white hover:border-primary/50 hover:text-primary']">
            {{ btn.label }}
          </button>
        </div>
        <div class="mt-4 text-center text-xs text-gray-500 tracking-wide">当前共 <span class="text-primary font-semibold">{{ totalVisible }}</span> 道题</div>
      </div>

      <!-- 考试与题目列表 -->
      <div v-for="exam in filteredExams" :key="exam.exam_id" class="mb-10 rounded-2xl border border-gray-200 bg-white/70 backdrop-blur shadow-sm overflow-hidden hover:shadow-md transition">
        <!-- 头部（改为浅色半透明，避免与背景冲突） -->
        <div class="px-6 py-5 bg-white/90 backdrop-blur-sm border-b border-gray-200 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div class="min-w-0">
            <h2 class="text-lg font-semibold leading-tight truncate text-gray-900">{{ exam.title }}</h2>
            <p class="text-xs text-gray-500 mt-1">⏰ {{ exam.start_time }} - {{ exam.end_time }}（{{ exam.duration }} 分钟）</p>
          </div>
          <div class="flex items-center gap-3 flex-wrap text-sm">
            <span v-if="submittedMap[Number(exam.exam_id||exam.id)]" class="px-3 py-1 rounded-full bg-gray-100 text-gray-600 border border-gray-200">已参加</span>
            <button @click.prevent="submitExam(exam)" :disabled="submittedMap[Number(exam.exam_id||exam.id)]" :class="['h-10 px-5 rounded-lg font-medium shadow-sm active:scale-[.97] transition', submittedMap[Number(exam.exam_id||exam.id)] ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-primary text-white hover:bg-primary/90']">提交试卷</button>
            <button @click="goStudent" class="h-10 px-5 rounded-lg bg-gray-100 text-gray-700 font-medium border border-gray-200 hover:bg-gray-200 active:scale-[.97] transition">返回学生页</button>
          </div>
        </div>
        <!-- 题目块 -->
        <div class="px-6 py-6">
          <div class="space-y-6">
            <div
              v-for="(question, idx) in exam.questions"
              :key="question.id"
              :data-qtype="question.type"
              :id="`q_${exam.exam_id}_${question.id}`"
              v-show="filterType==='all' || question.type===filterType"
              class="rounded-xl border border-gray-200 bg-white/80 p-5 shadow-sm transition hover:shadow group"
            >
              <div class="flex items-start gap-3">
                <div class="w-8 text-xs font-semibold text-gray-500 mt-0.5 select-none">{{ idx + 1 }}</div>
                <div class="flex-1 min-w-0">
                  <div class="mb-3">
                    <span class="inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-full bg-primary/10 text-primary mr-2">{{ question.type }}</span>
                    <!-- 题干：保留换行并强制长词折行 -->
                    <span class="text-gray-800 font-medium leading-relaxed whitespace-pre-line break-words break-all">{{ question.content }}</span>
                  </div>
                  <div v-if="question.type === '单选'" class="space-y-1">
                    <template v-if="!hasInlineChoices(question.content)">
                      <label v-for="option in question.options" :key="option.key" class="flex items-start gap-2 px-3 py-2 rounded-lg border border-transparent hover:bg-primary/5 cursor-pointer text-sm transition">
                        <input type="radio" :name="`answer_${exam.exam_id}_${question.id}`" :value="option.key" class="mt-0.5" />
                        <span class="flex-1 whitespace-pre-line break-words break-all">{{ option.label }}</span>
                      </label>
                    </template>
                    <template v-else>
                      <div class="flex flex-wrap gap-2">
                        <label v-for="k in ['A','B','C','D']" :key="k" class="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white/70 hover:bg-primary/5 cursor-pointer text-sm">
                          <input type="radio" :name="`answer_${exam.exam_id}_${question.id}`" :value="k" />
                          <span class="font-mono">{{ k }}</span>
                        </label>
                      </div>
                    </template>
                  </div>
                  <div v-else-if="question.type === '多选'" class="space-y-1">
                    <template v-if="!hasInlineChoices(question.content)">
                      <label v-for="option in question.options" :key="option.key" class="flex items-start gap-2 px-3 py-2 rounded-lg border border-transparent hover:bg-primary/5 cursor-pointer text-sm transition">
                        <input type="checkbox" :name="`answer_${exam.exam_id}_${question.id}`" :value="option.key" class="mt-0.5" />
                        <span class="flex-1 whitespace-pre-line break-words break-all">{{ option.label }}</span>
                      </label>
                    </template>
                    <template v-else>
                      <div class="flex flex-wrap gap-2">
                        <label v-for="k in ['A','B','C','D']" :key="k" class="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white/70 hover:bg-primary/5 cursor-pointer text-sm">
                          <input type="checkbox" :name="`answer_${exam.exam_id}_${question.id}`" :value="k" />
                          <span class="font-mono">{{ k }}</span>
                        </label>
                      </div>
                    </template>
                  </div>
                  <div v-else-if="question.type === '判断'" class="space-y-1">
                    <label class="flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-primary/5 cursor-pointer text-sm transition">
                      <input type="radio" :name="`answer_${exam.exam_id}_${question.id}`" value="A" class="mt-0.5" />
                      <span>正确</span>
                    </label>
                    <label class="flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-primary/5 cursor-pointer text-sm transition">
                      <input type="radio" :name="`answer_${exam.exam_id}_${question.id}`" value="B" class="mt-0.5" />
                      <span>错误</span>
                    </label>
                  </div>
                  <div v-else-if="question.type === '操作'" class="space-y-3">
                    <p class="text-xs text-amber-600 bg-amber-50/70 border border-amber-200 rounded px-3 py-2 leading-relaxed">请按要求完成操作并上传文件（支持 .docx/.xlsx/.pptx）。</p>
                    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
                      <input type="file" :name="`answer_${exam.exam_id}_${question.id}`" accept=".docx,.xlsx,.pptx" class="text-xs" />
                      <button type="button" class="h-10 px-4 rounded-lg bg-primary text-white text-xs font-medium shadow-sm hover:bg-primary/90 transition" @click="openOfficeForQuestion(question)">打开{{ getOfficeAppName(question) }}</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!examStore.loading && !filteredExams.length" class="text-center text-gray-400 py-16 text-sm">未找到该考试或已失效，请返回选择页</div>
      <div v-if="examStore.loading" class="text-center text-gray-400 py-16 text-sm">加载中...</div>
    </div>
  </div>
</template>

<style scoped>
/* use global .text-primary from tokens.css */
/* 题目锚点滚动时避免被固定导航遮挡 */
[data-qtype] { scroll-margin-top: 88px; }
</style>