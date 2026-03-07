<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <!-- 顶部导航 -->
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/60 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="backPrev" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">专项练习 - 出题设置</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <!-- 全局考纲选择（从顶部导航统一设置）提示 -->
          <div class="text-[11px] text-gray-500 hidden sm:block">考纲：{{ syllabusLabel }}</div>
          <button class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition" @click="backPrev">返回</button>
        </div>
      </div>
    </nav>

    <div class="max-w-5xl mx-auto pt-24 pb-24 px-4 lg:px-6">
      <!-- 设置卡片 -->
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur shadow-sm p-8 mb-10">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <h1 class="text-xl font-semibold text-gray-800">生成练习题</h1>
          <div class="flex flex-wrap gap-3">
            <button v-if="hasLast" class="h-10 px-4 rounded-lg bg-white/70 border border-primary/40 text-primary text-xs font-medium hover:bg-primary/5 transition" @click="applyLast">使用上次配置</button>
            <button class="h-10 px-4 rounded-lg bg-gray-100 text-gray-700 text-xs font-medium border border-gray-300 hover:bg-gray-200 transition" @click="resetForm">重置</button>
            <button type="button" class="h-10 px-4 rounded-lg bg-white/70 border border-gray-300 text-gray-600 text-xs font-medium hover:bg-white transition" @click="goStats">练习统计</button>
            <button type="button" class="h-10 px-4 rounded-lg bg-white/70 border border-gray-300 text-gray-600 text-xs font-medium hover:bg-white transition" @click="goMistakes">错题本</button>
            <button type="button" class="h-10 px-4 rounded-lg bg-white/70 border border-indigo-300 text-indigo-600 text-xs font-medium hover:bg-indigo-50 transition" @click="goSyllabus">知识点练习</button>
          </div>
        </div>

        <form @submit.prevent="generate" class="grid gap-6 md:grid-cols-2">
          <!-- 题型（多选） -->
          <div class="space-y-2 md:col-span-2">
            <label class="text-xs font-medium text-gray-600 tracking-wide">题型（多选）</label>
            <div class="flex flex-wrap gap-2">
              <label v-for="t in options.types" :key="t" class="flex items-center gap-2 px-2 py-1 rounded border text-xs bg-white/70">
                <input type="checkbox" :value="t" v-model="form.types" class="scale-90" /> {{ t }}
              </label>
              <span v-if="!options.types.length" class="text-xs text-gray-400">加载中...</span>
            </div>
          </div>
          <!-- 数量 -->
          <div class="space-y-2">
            <label class="text-xs font-medium text-gray-600 tracking-wide">题目数量</label>
            <input v-model.number="form.limit" type="number" min="1" max="100" class="h-11 w-full px-3 rounded-lg border border-gray-300/80 bg-white/70 text-sm" />
            <p class="text-[11px] text-gray-400">1 - 100，超出自动截断</p>
          </div>
          <!-- 难度区间 -->
          <div class="space-y-2">
            <label class="text-xs font-medium text-gray-600 tracking-wide">难度（最低分）</label>
            <input v-model.number="form.score_min" type="number" min="0" class="h-11 w-full px-3 rounded-lg border border-gray-300/80 bg-white/70 text-sm" />
          </div>
          <div class="space-y-2">
            <label class="text-xs font-medium text-gray-600 tracking-wide">难度（最高分）</label>
            <input v-model.number="form.score_max" type="number" min="0" class="h-11 w-full px-3 rounded-lg border border-gray-300/80 bg-white/70 text-sm" />
          </div>
          <!-- 乱序 -->
          <div class="space-y-2">
            <label class="text-xs font-medium text-gray-600 tracking-wide">乱序</label>
            <div class="h-11 flex items-center gap-3 px-3 rounded-lg border border-gray-300/80 bg-white/70">
              <input id="shuffle" type="checkbox" v-model="form.shuffle" class="h-4 w-4 rounded border-gray-300" />
              <label for="shuffle" class="text-sm text-gray-700 select-none">随机打乱题目顺序</label>
            </div>
          </div>
          <!-- 类型统计 -->
          <div class="md:col-span-2 pt-2">
            <p class="text-[11px] text-gray-500 leading-relaxed">题库统计（仅已审核）：
              <template v-if="Object.keys(options.counts_by_type).length">
                <span v-for="(c,t) in options.counts_by_type" :key="t" class="mr-4">{{ t }}：{{ c }}</span>
              </template>
              <span v-else>加载中...</span>
            </p>
          </div>
          <!-- 提交按钮 -->
          <div class="md:col-span-2 flex flex-wrap gap-4 pt-4">
            <button type="submit" :disabled="loading" class="h-11 px-8 rounded-lg bg-primary text-black text-sm font-medium shadow-sm hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition flex items-center gap-2">
              <span v-if="!loading">生成题目</span>
              <span v-else class="flex items-center gap-2"><svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/><path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" stroke-width="4" stroke-linecap="round" class="opacity-90"/></svg>生成中...</span>
            </button>
            <div v-if="errorMsg" class="min-h-11 px-4 py-2 text-xs rounded-lg bg-red-50 text-red-600 border border-red-200 flex items-center gap-2">{{ errorMsg }}</div>
            <div v-if="successMsg" class="min-h-11 px-4 py-2 text-xs rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center gap-2">{{ successMsg }}</div>
          </div>
        </form>
      </div>

      <!-- 最近一次（本地记忆）展示 -->
      <div v-if="hasLast" class="rounded-2xl border border-dashed border-gray-300 bg-white/40 backdrop-blur p-6 text-xs text-gray-600">
        上次配置：{{ lastReadable }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiPracticeOptions, apiPracticeQuestions } from '../api/index'
import { useSyllabusStore } from '../stores/syllabus'
import AppLogo from '../components/AppLogo.vue'

const router = useRouter()
const s = useSyllabusStore()
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const options = reactive({ types: [], batches: [], counts_by_type: {}, score_range:{min:0,max:0} })
const form = reactive({ types: [], batch: '', limit: 20, shuffle: true, score_min: '', score_max: '' })

const syllabusLabel = computed(()=>{
  if(!s.province) return '未选择'
  return s.province + (s.major? ' / ' + s.major : '')
})

const currentFiltersReadable = computed(() => {
  const seg = []
  if (form.types?.length) seg.push('题型:' + form.types.join(','))
  if (form.score_min !== '' && form.score_min !== null && form.score_min !== undefined) seg.push('最低分:' + form.score_min)
  if (form.score_max !== '' && form.score_max !== null && form.score_max !== undefined) seg.push('最高分:' + form.score_max)
  seg.push('数量:' + form.limit)
  if (form.shuffle) seg.push('乱序')
  if (s.province) seg.push('考纲:' + syllabusLabel.value)
  return seg.join(' / ')
})

// 本地记忆
const LAST_KEY = 'practice_last_filters'
const hasLast = computed(() => !!localStorage.getItem(LAST_KEY))
const lastReadable = computed(() => {
  try {
    const raw = JSON.parse(localStorage.getItem(LAST_KEY)||'null')
    if(!raw) return ''
    const seg = []
    if(raw.types && raw.types.length) seg.push('题型:'+raw.types.join(','))
    // 批次不再纳入展示
    if(raw.score_min) seg.push('低分:'+raw.score_min)
    if(raw.score_max) seg.push('高分:'+raw.score_max)
    seg.push('数量:'+raw.limit)
    if(raw.shuffle) seg.push('乱序')
    return seg.join(' / ')
  } catch { return '' }
})

function applyLast(){
  try {
    const raw = JSON.parse(localStorage.getItem(LAST_KEY)||'null')
    if(!raw) return
    Object.assign(form, raw)
    successMsg.value = '已填入上次配置'
    setTimeout(()=> successMsg.value='',1500)
  } catch{}
}

function resetForm(){
  form.types=[];form.batch='';form.limit=20;form.shuffle=true;form.score_min='';form.score_max=''
  errorMsg.value='';successMsg.value=''
  loadOptions()
}

async function loadOptions(){
  try {
    const params = {}
    if (s.province) params.province = s.province
    if (s.major) params.major = s.major
    const { data } = await apiPracticeOptions(params)
    if(data?.success){
      options.types = data.types || []
      options.batches = data.batches || []
      options.counts_by_type = data.counts_by_type || {}
      options.score_range = data.score_range || {min:0,max:0}
      return
    }
    errorMsg.value = data?.error_msg || '加载题型失败'
  } catch(e){
    errorMsg.value = e?._friendly || '加载题型失败'
  }
}

watch(()=>[s.province, s.major], ()=> loadOptions(), { deep: true })

function validate(){
  if(!form.limit || form.limit<1) { errorMsg.value='题目数量至少为 1'; return false }
  if(form.limit>100) form.limit=100
  if (form.score_min && form.score_max && Number(form.score_max) < Number(form.score_min)){
    const t = form.score_min; form.score_min = form.score_max; form.score_max = t
  }
  return true
}

async function generate(){
  errorMsg.value=''; successMsg.value=''
  if(!validate()) return
  loading.value=true
  try {
    const params = { limit: form.limit }
    if(form.types?.length) params.types = form.types.join(',')
    // 不再考虑批次：不发送 batch 参数
    if(form.score_min!=='') params.score_min = form.score_min
    if(form.score_max!=='') params.score_max = form.score_max
    params.shuffle = form.shuffle?1:0
    if(s.province) params.province = s.province
    if(s.major) params.major = s.major
    const { data } = await apiPracticeQuestions(params)
    if(data?.success){
      const list = data.questions || []
      if(!list.length){
        sessionStorage.removeItem('practice_questions')
        sessionStorage.removeItem('practice_filters')
        errorMsg.value = data?.message || `没有得到题目，请调整筛选条件${currentFiltersReadable.value ? '（当前：' + currentFiltersReadable.value + '）' : ''}`
        return
      }
      sessionStorage.setItem('practice_questions', JSON.stringify(list))
      sessionStorage.setItem('practice_filters', JSON.stringify({...form}))
      localStorage.setItem(LAST_KEY, JSON.stringify({...form}))
      successMsg.value = `生成成功，共 ${list.length} 题，正在进入答题…`
      setTimeout(()=> router.push('/practice/do'), 300)
    } else {
      errorMsg.value = data?.error_msg || '生成失败'
    }
  } catch(e){
    errorMsg.value = e?._friendly || '网络错误，生成失败'
  } finally {
    loading.value=false
  }
}

function backPrev(){ router.push('/student') }
function goStats(){ router.push('/practice/stats') }
function goMistakes(){ router.push('/practice/mistakes') }
function goSyllabus(){ router.push('/syllabus/setup') }

onMounted(()=>{ loadOptions() })
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
/* use global .text-primary from tokens.css */
</style>
