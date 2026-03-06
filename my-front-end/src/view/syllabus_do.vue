<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <AppLogo :height="36" class="cursor-pointer" @click="goBack" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">知识点练习 - 答题</span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <button class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition" @click="goBack">返回设置</button>
        </div>
      </div>
    </nav>

    <div class="max-w-7xl mx-auto pt-24 pb-20 px-4">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200 flex flex-col sm:flex-row gap-4 sm:items-center sm:justify-between">
          <div>
            <h2 class="text-base font-semibold text-gray-800">练习题目（{{ questions.length }}）
              <span v-if="filters && filters.level" class="ml-2 inline-flex items-center text-[10px] font-medium px-2 py-0.5 rounded-full" :class="filters.level==='primary'?'bg-amber-100 text-amber-700':'bg-indigo-100 text-indigo-700'">{{ filters.level==='primary'?'一级':'考纲' }}</span>
              <span v-if="questions.length" class="ml-2 text-xs text-gray-500">当前：{{ currentIndex + 1 }} / {{ questions.length }}</span>
            </h2>
            <p v-if="filtersInfo" class="mt-1 text-xs text-gray-500">条件：{{ filtersInfo }}</p>
          </div>
          <div class="flex flex-wrap gap-3">
            <button class="h-10 px-4 rounded-lg bg-white/70 border border-gray-300 text-gray-700 text-xs font-medium hover:bg-white transition" @click="clearCurrent">清空当前</button>
            <button class="h-10 px-4 rounded-lg bg-primary text-white text-xs font-medium shadow-sm hover:bg-primary/90 transition" @click="submitCurrent" :disabled="submitting || !currentQuestion">{{ submitting? '判题中...':'提交当前' }}</button>
            <button class="h-10 px-4 rounded-lg bg-gray-100 text-gray-700 text-xs font-medium border border-gray-300 hover:bg-gray-200 transition" @click="prev" :disabled="!hasPrev">上一题</button>
            <button class="h-10 px-4 rounded-lg bg-gray-100 text-gray-700 text-xs font-medium border border-gray-300 hover:bg-gray-200 transition" @click="next" :disabled="!hasNext">下一题</button>
            <button class="h-10 px-4 rounded-lg bg-white/70 text-gray-700 text-xs font-medium border border-gray-300 hover:bg-white transition" @click="skip" :disabled="!hasNext">跳过</button>
            <button class="h-10 px-4 rounded-lg bg-white/70 text-gray-700 text-xs font-medium border border-gray-300 hover:bg-white transition" @click="reGenerate">重新出题</button>
          </div>
        </div>

        <div v-if="!questions.length && !loading" class="p-16 text-center text-gray-400 text-sm">暂无题目，请返回设置页重新生成。</div>
        <div v-if="loading" class="p-16 text-center text-gray-500 text-sm">加载中...</div>

        <div v-else class="p-6">
          <!-- 进度条 + 题卡切换 -->
          <div v-if="questions.length" class="mb-4">
            <div class="text-xs text-gray-600 mb-2">进度：已答 {{ answeredCount }} / {{ questions.length }} · 判题 {{ judgedCount }} · 正确 {{ correctCount }}</div>
            <div class="w-full h-2 bg-gray-100 rounded overflow-hidden">
              <div class="h-full bg-primary" :style="{ width: progressPercent + '%' }"></div>
            </div>
            <div class="mt-3 flex items-center gap-3">
              <button class="h-8 px-3 rounded bg-white/70 border border-gray-300 text-xs text-gray-700 hover:bg-white" @click="showCard = !showCard">{{ showCard ? '收起题卡' : '展开题卡' }}</button>
              <div class="text-[10px] text-gray-500 flex items-center gap-2">
                <span class="inline-flex items-center px-1.5 py-0.5 rounded bg-white/70 border border-gray-300">未答</span>
                <span class="inline-flex items-center px-1.5 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-700">已答</span>
                <span class="inline-flex items-center px-1.5 py-0.5 rounded bg-green-100 border border-green-200 text-green-700">正确</span>
                <span class="inline-flex items-center px-1.5 py-0.5 rounded bg-red-100 border border-red-200 text-red-700">错误</span>
                <span class="inline-flex items-center px-1.5 py-0.5 rounded bg-primary text-white">当前</span>
              </div>
            </div>
            <div v-if="showCard" class="mt-3 rounded-lg border border-gray-200 bg-white/60 p-3">
              <div class="overflow-x-auto">
                <div class="flex gap-2 min-w-max">
                  <button v-for="(q,idx) in questions" :key="q.id" @click="jumpTo(idx)"
                          :class="['h-8 w-8 rounded text-[11px] font-medium border transition shrink-0', cardClass(idx)]">
                    {{ idx + 1 }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 当前题目 -->
          <div v-if="currentQuestion" class="hover:bg-white/60 transition">
            <div class="flex items-start gap-4">
              <div class="w-6 text-xs font-semibold text-gray-400 pt-1 select-none">{{ currentIndex + 1 }}</div>
              <div class="flex-1 min-w-0">
                <div class="mb-3">
                  <span class="inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-full bg-primary/10 text-primary mr-2">{{ currentQuestion.type }}</span>
                  <span v-if="currentQuestion.knowledge_points" class="inline-flex items-center text-[10px] font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 mr-2">考纲: {{ currentQuestion.knowledge_points }}</span>
                  <span v-if="currentQuestion.primary_knowledge" class="inline-flex items-center text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 mr-2">一级: {{ currentQuestion.primary_knowledge }}</span><br>
                  <span class="text-gray-800 leading-relaxed break-words">{{ currentQuestion.content }}</span>
                </div>

                <!-- 单选 -->
                <div v-if="currentQuestion.type==='单选'" class="space-y-1">
                  <template v-if="!hasInlineChoices(currentQuestion.content)">
                    <label v-for="opt in currentQuestion.options" :key="opt.key" class="flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-primary/5 cursor-pointer text-sm">
                      <input type="radio" :name="'q_'+currentQuestion.id" :value="opt.key" v-model="answers[currentQuestion.id]" class="mt-0.5" />
                      <span class="flex-1 break-words">{{ formatLabel(opt.label) }}</span>
                    </label>
                  </template>
                  <template v-else>
                    <div class="flex flex-wrap gap-2">
                      <label v-for="k in ['A','B','C','D']" :key="k" class="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white/70 hover:bg-primary/5 cursor-pointer text-sm">
                        <input type="radio" :name="'q_'+currentQuestion.id" :value="k" v-model="answers[currentQuestion.id]" />
                        <span class="font-mono">{{ k }}</span>
                      </label>
                    </div>
                  </template>
                </div>
                <!-- 多选 -->
                <div v-else-if="currentQuestion.type==='多选'" class="space-y-1">
                  <template v-if="!hasInlineChoices(currentQuestion.content)">
                    <label v-for="opt in currentQuestion.options" :key="opt.key" class="flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-primary/5 cursor-pointer text-sm">
                      <input type="checkbox" :value="opt.key" v-model="answersMulti[currentQuestion.id]" class="mt-0.5" />
                      <span class="flex-1 break-words">{{ formatLabel(opt.label) }}</span>
                    </label>
                  </template>
                  <template v-else>
                    <div class="flex flex-wrap gap-2">
                      <label v-for="k in ['A','B','C','D']" :key="k" class="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white/70 hover:bg-primary/5 cursor-pointer text-sm">
                        <input type="checkbox" :value="k" v-model="answersMulti[currentQuestion.id]" />
                        <span class="font-mono">{{ k }}</span>
                      </label>
                    </div>
                  </template>
                </div>
                <!-- 判断 -->
                <div v-else-if="currentQuestion.type==='判断'" class="space-y-1">
                  <label v-for="opt in currentQuestion.options" :key="opt.key" class="flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-primary/5 cursor-pointer text-sm">
                    <input type="radio" :name="'q_'+currentQuestion.id" :value="opt.label" v-model="answers[currentQuestion.id]" class="mt-0.5" />
                    <span>{{ opt.label }}</span>
                  </label>
                </div>
                <!-- 操作题提示 -->
                <div v-else class="text-xs text-gray-500">操作题不参与自动判题。</div>

                <!-- 判题结果（当前题） -->
                <div v-if="resultById[currentQuestion.id]" class="mt-3 text-xs">
                  <div class="flex items-center gap-3">
                    <span :class="resultById[currentQuestion.id].is_correct ? 'text-green-600' : 'text-red-600'" class="font-medium">
                      <i :class="resultById[currentQuestion.id].is_correct ? 'fas fa-check-circle' : 'fas fa-times-circle'"></i>
                      <span class="ml-1">{{ resultById[currentQuestion.id].is_correct ? '正确' : '错误' }}</span>
                    </span>
                    <span class="text-gray-500">正确答案：{{ resultById[currentQuestion.id].correct_answer }}</span>
                  </div>
                  <div v-if="resultById[currentQuestion.id].analysis" class="mt-2 text-gray-700 whitespace-pre-wrap break-words">
                    <span class="text-gray-500">解析：</span>{{ resultById[currentQuestion.id].analysis }}
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>

        <!-- 题目评论（提交后可见） -->
        <div v-if="currentQuestion" class="p-6 border-t border-gray-200 bg-white/60">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-gray-800">题目评论</h3>
            <div class="text-[11px] text-gray-500" v-if="!canShowComments">提交当前题目后可查看与发表本题评论</div>
          </div>
          <div v-if="canShowComments">
            <div class="mt-3">
              <textarea v-model="qCommentText" rows="3" placeholder="写下你的理解、易错点或疑问，与同学交流～"
                        class="w-full text-sm p-3 rounded-lg border border-gray-300 bg-white/70 focus:bg-white outline-none focus:ring-2 focus:ring-primary/30"></textarea>
              <div class="mt-2 flex items-center justify-end">
                <button class="h-9 px-4 rounded bg-primary text-white text-xs font-medium shadow-sm hover:bg-primary/90 disabled:opacity-60"
                        :disabled="qCommentPosting || !qCommentText.trim().length || postCooldownLeft>0" @click="postQComment">
                  <template v-if="postCooldownLeft>0">请稍后 {{ postCooldownLeft }}s</template>
                  <template v-else>{{ qCommentPosting ? '发送中...' : '发布' }}</template>
                </button>
              </div>
            </div>
            <div class="mt-4">
              <div v-if="qCommentsLoading" class="text-xs text-gray-500">加载评论中...</div>
              <div v-else-if="!qComments.length" class="text-xs text-gray-400">还没有评论，快来抢沙发～</div>
              <ul v-else class="space-y-3">
                <li v-for="c in qComments" :key="c.id" class="p-3 rounded-lg border border-gray-200 bg-white/70">
                  <div class="flex items-center justify-between">
                    <div class="text-[11px] text-gray-500">{{ c.username }} · {{ c.created_at }}</div>
                    <div class="flex items-center gap-2">
                      <button class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border border-gray-200 bg-white/70 hover:bg-primary/5"
                              :disabled="likePending[c.id]" @click="toggleLike(c)">
                        <i :class="c.liked_by_me ? 'fas fa-heart text-red-500' : 'far fa-heart text-gray-500'"></i>
                        <span class="min-w-[1.5rem] text-gray-700">{{ c.likes || 0 }}</span>
                      </button>
                      <button v-if="canDelete(c) || c.can_delete" @click="deleteQComment(c)" class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border border-red-200 text-red-600 bg-red-50 hover:bg-red-100">
                        <i class="fas fa-trash-alt"></i>
                        <span>删除</span>
                      </button>
                    </div>
                  </div>
                  <div class="mt-1 text-sm text-gray-800 whitespace-pre-wrap break-words">{{ c.content }}</div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiPracticeCheck, apiQComments, apiQCommentsCreate, apiQCommentsDelete, apiQCommentLike, apiQCommentUnlike } from '../api/index'
import { useUserStore } from '../stores/user'
import AppLogo from '../components/AppLogo.vue'

const router = useRouter()
const userStore = useUserStore()
userStore.loadProfile().catch(()=>{})

const loading = ref(true)
const submitting = ref(false)
const questions = ref([])
const filters = ref(null)
// 单题模式
const currentIndex = ref(0)
const currentQuestion = computed(()=>questions.value[currentIndex.value] || null)
const hasPrev = computed(()=>currentIndex.value>0)
const hasNext = computed(()=>currentIndex.value<questions.value.length-1)

// 答案模型
const answers = reactive({})
const answersMulti = reactive({})

// 判题结果
const resultDetails = ref([])
const resultById = computed(()=>{ const m={}; resultDetails.value.forEach(d=>m[d.id]=d); return m })
const canShowComments = computed(()=>{ const q=currentQuestion.value; if(!q) return false; return !!resultById.value[q.id] })

const filtersInfo = computed(()=>{ if(!filters.value) return ''; const f=filters.value; const ps=[]; ps.push('层级:'+(f.level==='primary'?'一级':'考纲')); ps.push('模式:'+f.mode); if(f.type) ps.push('题型:'+f.type); if(f.difficulty) ps.push('难度:'+f.difficulty); if(f.mode==='normal'&&f.knowledge) ps.push('关键字:'+f.knowledge); if(f.mode==='cover') ps.push('覆盖/每个:'+f.per_kp); ps.push('数量上限:'+f.limit); return ps.join(' / ') })

function restore(){
  try{
    const qs=JSON.parse(sessionStorage.getItem('syllabus_questions')||'[]')
    const fs=JSON.parse(sessionStorage.getItem('syllabus_filters')||'null')
    questions.value=Array.isArray(qs)?qs:[]
    filters.value=fs
    currentIndex.value = 0
  }catch{
    questions.value=[]
  }finally{
    loading.value=false
    if(!questions.value.length) router.replace('/syllabus/setup')
  }
}

function clearCurrent(){
  const q = currentQuestion.value
  if(!q) return
  delete answers[q.id]
  delete answersMulti[q.id]
}

function prev(){ if(hasPrev.value) currentIndex.value -= 1 }
function next(){ if(hasNext.value) currentIndex.value += 1 }
function skip(){ next() }

async function submitCurrent(){
  const q = currentQuestion.value
  if(!q || submitting.value) return
  submitting.value = true
  try{
    const payload={ answers:{}, question_ids:[q.id] }
    if(q.type==='多选') payload.answers[q.id]=(answersMulti[q.id]||[]).slice()
    else if(q.type==='判断'||q.type==='单选') payload.answers[q.id]=answers[q.id]||''
    const { data } = await apiPracticeCheck(payload)
    if(data?.success && Array.isArray(data.details)){
      const detail = data.details.find(d=>d.id===q.id) || null
      if(detail){
        const idx = resultDetails.value.findIndex(d=>d.id===q.id)
        if(idx>=0) resultDetails.value.splice(idx,1,detail)
        else resultDetails.value.push(detail)
        await loadQComments()
        if(detail.is_correct && hasNext.value) currentIndex.value += 1
      }
    }
  }finally{ submitting.value = false }
}
function reGenerate(){ router.replace('/syllabus/setup') }
function goBack(){ router.push('/syllabus/setup') }
function hasInlineChoices(text){ const t=String(text||''); return /(^|[\n\r])\s*[A-D]\s*[。.、．:：]/.test(t) }
function formatLabel(label){ const s=String(label||''); return s.replace(/^\s*[A-D]\s*[。.、．:：]\s*/u,'') }

// 题卡与进度
const showCard = ref(false)
const answeredCount = computed(()=>{ let c=0; for(const q of questions.value){ const a=answers[q.id]; const m=answersMulti[q.id]; if((Array.isArray(m)&&m.length)||(a!==undefined&&a!==null&&String(a).length)) c++ } return c })
const judgedCount = computed(()=>Object.keys(resultById.value).length)
const correctCount = computed(()=>Object.values(resultById.value).filter(d=>d && d.is_correct).length)
const progressPercent = computed(()=>{ const total=questions.value.length||1; return Math.min(100, Math.round(100*answeredCount.value/total)) })
function isAnswered(idx){ const q=questions.value[idx]; if(!q) return false; const a=answers[q.id]; const m=answersMulti[q.id]; return (Array.isArray(m)&&m.length)||(a!==undefined&&a!==null&&String(a).length) }
function isCorrect(idx){ const q=questions.value[idx]; const d=q?resultById.value[q.id]:null; return !!(d&&d.is_correct) }
function isWrong(idx){ const q=questions.value[idx]; const d=q?resultById.value[q.id]:null; return !!(d&&d.is_correct===false) }
function cardClass(idx){ if(idx===currentIndex.value) return 'bg-primary text-white border-primary'; if(isCorrect(idx)) return 'bg-green-100 text-green-700 border-green-200 hover:bg-green-200'; if(isWrong(idx)) return 'bg-red-100 text-red-700 border-red-200 hover:bg-red-200'; if(isAnswered(idx)) return 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'; return 'bg-white/70 text-gray-700 border-gray-300 hover:bg-white' }
function jumpTo(idx){ if(idx>=0 && idx<questions.value.length){ currentIndex.value=idx; window.scrollTo({top:0,behavior:'smooth'}) } }

// ===== 评论（提交后可见） =====
const qComments = ref([])
const qCommentsLoading = ref(false)
const qCommentText = ref('')
const qCommentPosting = ref(false)
// 点赞中的状态
const likePending = reactive({})
// 发布冷却（用 ref + interval 持续更新剩余秒数）
const postCooldownLeft = ref(0)
let postCooldownTimer = null
function startCooldown(ms=8000){
  if (postCooldownTimer) { clearInterval(postCooldownTimer); postCooldownTimer = null }
  const end = Date.now() + ms
  const tick = () => {
    const left = Math.max(0, Math.ceil((end - Date.now())/1000))
    postCooldownLeft.value = left
    if (left <= 0) { clearInterval(postCooldownTimer); postCooldownTimer = null }
  }
  tick()
  postCooldownTimer = setInterval(tick, 250)
}
onUnmounted(()=>{ if (postCooldownTimer) { clearInterval(postCooldownTimer); postCooldownTimer = null }})

async function loadQComments(){
  const q=currentQuestion.value
  if(!q || !canShowComments.value){ qComments.value=[]; return }
  qCommentsLoading.value = true
  try{
    const { data } = await apiQComments(q.id)
    let items = data?.items || []
    // 按点赞数高->低、时间新->旧（后端已排，这里兜底）
    items.sort((a,b)=>{ const la=(a.likes||0), lb=(b.likes||0); if(lb!==la) return lb-la; return (b.id||0)-(a.id||0) })
    qComments.value = items
  }catch(e){ console.warn('加载题目评论失败', e?._friendly||e?.message) }
  finally{ qCommentsLoading.value = false }
}
async function postQComment(){
  const q = currentQuestion.value
  if(!q || !canShowComments.value || postCooldownLeft.value>0) return
  const txt = qCommentText.value.trim()
  if(!txt) return
  qCommentPosting.value = true
  try{
    await apiQCommentsCreate({ question_id: q.id, content: txt })
    qCommentText.value = ''
    startCooldown(8000)
    await loadQComments()
  }catch(e){ alert(e?._friendly||'发布失败，请稍后再试') }
  finally{ qCommentPosting.value = false }
}
async function toggleLike(c){
  if (!c || likePending[c.id]) return
  likePending[c.id] = true
  try{
    const api = c.liked_by_me ? apiQCommentUnlike : apiQCommentLike
    const { data } = await api(c.id)
    if (data?.success){
      c.liked_by_me = !!data.liked
      c.likes = data.likes ?? (c.likes||0) + (c.liked_by_me ? 1 : -1)
      // 排序刷新
      qComments.value = [...qComments.value].sort((a,b)=>{ const la=(a.likes||0), lb=(b.likes||0); if(lb!==la) return lb-la; return (b.id||0)-(a.id||0) })
    }
  }catch(e){ alert(e?._friendly||'操作失败，请稍后再试') }
  finally{ likePending[c.id] = false }
}
function canDelete(c){
  const uid = userStore.userId
  const role = userStore.role
  return (c.user_id && uid && Number(c.user_id)===Number(uid)) || (role==='老师' || role==='管理员')
}
async function deleteQComment(c){
  if(!canDelete(c) && !c.can_delete) return
  if(!confirm('确定删除该评论吗？')) return
  try{ await apiQCommentsDelete(c.id); await loadQComments() }catch(e){ alert(e?._friendly||'删除失败，请稍后再试') }
}

watch([currentQuestion, canShowComments], ()=>{ loadQComments() })

onMounted(restore)
</script>
<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
/* use global .text-primary/.bg-primary from tokens.css */
</style>
