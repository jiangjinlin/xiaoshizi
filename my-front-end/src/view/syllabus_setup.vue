<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/70 backdrop-blur border-b border-gray-200 px-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <AppLogo :height="34" class="cursor-pointer" @click="goBack" />
        <span class="hidden sm:inline text-lg font-semibold text-gray-700">知识点练习 - 出题设置</span>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <button class="px-4 h-10 rounded-lg bg-white/70 border border-gray-200 text-gray-600 hover:bg-white" @click="gotoStats">掌握统计</button>
        <button class="px-4 h-10 rounded-lg bg-white/70 border border-gray-200 text-gray-600 hover:bg-white" @click="goBack">返回</button>
      </div>
    </nav>

    <div class="max-w-5xl mx-auto pt-24 pb-24 px-4 lg:px-6">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur shadow-sm p-8 mb-10">
        <div class="flex flex-col gap-5">
          <!-- 新增：层级切换 -->
          <div class="flex flex-wrap gap-3 items-center">
            <label class="text-xs font-medium text-gray-600">层级</label>
            <div class="flex gap-2">
              <button @click="form.level='knowledge'" :class="['h-9 px-3 rounded-lg text-xs font-medium border', form.level==='knowledge'?'bg-indigo-600 text-white border-indigo-600':'bg-white/70 text-gray-600 border-gray-300 hover:bg-white']">考纲大类</button>
              <button @click="form.level='primary'" :class="['h-9 px-3 rounded-lg text-xs font-medium border', form.level==='primary'?'bg-indigo-600 text-white border-indigo-600':'bg-white/70 text-gray-600 border-gray-300 hover:bg-white']">一级知识点</button>
            </div>
          </div>
          <!-- 原模式选择 -->
          <div class="flex flex-wrap gap-3 items-center">
            <label class="text-xs font-medium text-gray-600">模式</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="m in modes" :key="m.value" @click="form.mode=m.value" :class="['h-9 px-3 rounded-lg text-xs font-medium border', form.mode===m.value? 'bg-primary text-black border-primary':'bg-white/70 text-gray-600 border-gray-300 hover:bg-white']">{{ m.label }}</button>
            </div>
          </div>
          <div class="grid md:grid-cols-3 gap-6">
            <div class="space-y-2">
              <label class="text-xs font-medium text-gray-600">题型</label>
              <select v-model="form.type" class="h-10 w-full px-3 rounded-lg border border-gray-300 bg-white/70 text-sm">
                <option value="">全部</option>
                <option v-for="t in options.types" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-xs font-medium text-gray-600">难度(分值)</label>
              <select v-model="form.difficulty" class="h-10 w-full px-3 rounded-lg border border-gray-300 bg-white/70 text-sm">
                <option value="">全部</option>
                <option v-for="d in options.difficulties" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
            <div v-if="form.mode==='normal'" class="space-y-2" :class="{'md:col-span-1':true}">
              <label class="text-xs font-medium text-gray-600">{{ form.level==='knowledge' ? '单知识点包含' : '一级知识点包含' }}</label>
              <input v-model="form.knowledge" :placeholder="form.level==='knowledge' ? '输入考纲大类关键词' : '输入一级知识点关键词'" class="h-10 w-full px-3 rounded-lg border border-gray-300 bg-white/70 text-sm" />
            </div>
            <div v-if="form.mode==='cover'" class="space-y-2 md:col-span-2">
              <label class="text-xs font-medium text-gray-600">{{ form.level==='knowledge' ? '知识点集合(多选)' : '一级知识点集合(多选)' }}</label>
              <div class="flex flex-wrap gap-2 max-h-40 overflow-auto p-2 rounded-lg border border-gray-300 bg-white/60">
                <label v-for="kp in (form.level==='knowledge'? options.knowledge_points : options.primary_points)" :key="kp" class="text-[11px] px-2 py-1 rounded border cursor-pointer" :class="form.kp_list.includes(kp)?'bg-primary text-black border-primary':'bg-white text-gray-600 border-gray-300 hover:bg-primary/5'">
                  <input type="checkbox" class="hidden" :value="kp" @change="toggleKp(kp)"/>{{ kp }}
                </label>
              </div>
              <p class="text-[10px] text-gray-400">未选择则覆盖全部{{ form.level==='knowledge' ? '知识点' : '一级知识点' }}。</p>
            </div>
            <div v-if="form.mode==='cover'" class="space-y-2">
              <label class="text-xs font-medium text-gray-600">每知识点题数</label>
              <input type="number" v-model.number="form.per_kp" min="1" max="20" class="h-10 w-full px-3 rounded-lg border border-gray-300 bg-white/70 text-sm" />
            </div>
            <div class="space-y-2">
              <label class="text-xs font-medium text-gray-600">题目数量上限</label>
              <input type="number" v-model.number="form.limit" min="1" max="300" class="h-10 w-full px-3 rounded-lg border border-gray-300 bg-white/70 text-sm" />
              <p class="text-[10px] text-gray-400">超出自动截断。</p>
            </div>
            <div class="space-y-2">
              <label class="text-xs font-medium text-gray-600">乱序</label>
              <div class="h-10 flex items-center gap-2 px-3 rounded-lg border border-gray-300 bg-white/70">
                <input type="checkbox" v-model="form.shuffle" class="h-4 w-4" />
                <span class="text-xs text-gray-600 select-none">随机打乱</span>
              </div>
            </div>
          </div>
          <div class="pt-2 text-[11px] text-gray-500 leading-relaxed space-y-1">
            <p><b>模式说明：</b></p>
            <p><b>normal</b>：按条件随机抽题；可指定题型/难度/单知识点关键字。</p>
            <p><b>weak</b>：自动优先抽取你准确率低的知识点题目（忽略 knowledge 关键字）。</p>
            <p><b>cover</b>：按知识点集合全覆盖抽题，每个知识点抽 per_kp 道题。</p>
          </div>
          <div class="flex flex-wrap gap-4 pt-2">
            <button @click="generate" :disabled="loading" class="h-11 px-8 rounded-lg bg-primary text-black text-sm font-medium shadow-sm hover:bg-primary/90 disabled:opacity-60">{{ loading? '生成中...':'生成题目' }}</button>
            <div v-if="errorMsg" class="px-4 py-2 text-xs rounded-lg bg-red-50 text-red-600 border border-red-200">{{ errorMsg }}</div>
            <div v-if="successMsg" class="px-4 py-2 text-xs rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200">{{ successMsg }}</div>
          </div>
        </div>
      </div>
      <div class="rounded-2xl border border-dashed border-gray-300 bg-white/40 backdrop-blur p-6 text-xs text-gray-600" v-if="(form.level==='knowledge'?options.knowledge_points:options.primary_points).length">
        共 {{ (form.level==='knowledge'?options.knowledge_points:options.primary_points).length }} 个{{ form.level==='knowledge'?'知识点':'一级知识点' }}。
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiSyllabusOptions, apiSyllabusQuestions } from '../api/index'
import AppLogo from '../components/AppLogo.vue'
const router = useRouter()
const route = useRoute()
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const options = reactive({ types:[], difficulties:[], knowledge_points:[], primary_points:[] })
const modes = [ {label:'普通', value:'normal'}, {label:'补弱', value:'weak'}, {label:'全覆盖', value:'cover'} ]
const form = reactive({ level:'knowledge', mode:'normal', type:'', difficulty:'', knowledge:'', kp_list:[], per_kp:1, limit:50, shuffle:true })
function toggleKp(k){ const i=form.kp_list.indexOf(k); if(i>=0) form.kp_list.splice(i,1); else form.kp_list.push(k) }
function validate(){ if(!form.limit||form.limit<1){ errorMsg.value='题目数量至少 1'; return false } if(form.limit>300) form.limit=300; if(form.mode==='cover' && (!form.per_kp||form.per_kp<1)){ errorMsg.value='每知识点题数至少 1'; return false } return true }
async function generate(){ errorMsg.value=''; successMsg.value=''; if(!validate()) return; loading.value=true; try{ const params={ mode:form.mode, limit:form.limit, shuffle:form.shuffle?1:0, level: form.level }; if(form.type) params.type=form.type; if(form.difficulty) params.difficulty=form.difficulty; if(form.mode==='normal' && form.knowledge) params.knowledge=form.knowledge; if(form.mode==='cover'){ params.per_kp=form.per_kp; if(form.kp_list.length) params.kp_list=form.kp_list.join(',') } const { data } = await apiSyllabusQuestions(params); if(data?.success){ const list=data.questions||[]; if(!list.length){ errorMsg.value='没有得到题目，请调整条件'; return } sessionStorage.setItem('syllabus_questions', JSON.stringify(list)); sessionStorage.setItem('syllabus_filters', JSON.stringify({...form})); successMsg.value='生成成功，进入答题...'; setTimeout(()=> router.push('/syllabus/do'), 400) } else { errorMsg.value=data?.error_msg||'生成失败' } } catch{ errorMsg.value='网络错误' } finally { loading.value=false } }
async function load(){ try{ const { data } = await apiSyllabusOptions(); if(data?.success){ options.types=data.types||[]; options.difficulties=data.difficulties||[]; options.knowledge_points=data.knowledge_points||[]; options.primary_points=data.primary_points||[] } }catch{} }
function goBack(){ router.push('/practice/setup') }
function gotoStats(){ router.push('/syllabus/stats') }
onMounted(()=>{ load(); const q=route.query; if(q.level){ const lv = String(q.level).toLowerCase(); if(lv.startsWith('p')) form.level='primary'; else form.level='knowledge'; } if(q.mode){ const md=String(q.mode).toLowerCase(); if(['normal','weak','cover'].includes(md)) form.mode=md } })
</script>
<style scoped>
/* use global .text-primary from tokens.css */
</style>
