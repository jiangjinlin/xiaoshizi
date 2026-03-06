<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiManageQuestionDetail, apiManageQuestionSave } from '../../api/index'

const router = useRouter()
const route = useRoute()
const id = computed(() => route.params.id)
const isEdit = computed(() => !!id.value)

const form = ref({
  question_type: '单选',
  score: 1,
  content: '',
  A_answer: '',
  B_answer: '',
  C_answer: '',
  D_answer: '',
  answer: '',
  batch: '',
  analysis: '',
  knowledge_points: '', // 逗号分隔
  primary_knowledge: ''
})

const message = ref('')
const messageType = ref('')

async function loadDetail() {
  if (!isEdit.value) return
  try {
    const { data } = await apiManageQuestionDetail(id.value)
    if (data?.success && data.question) {
      const q = data.question
      form.value = {
        question_type: q.question_type || '单选',
        score: q.score ?? 1,
        content: q.content || '',
        A_answer: q.A_answer || '',
        B_answer: q.B_answer || '',
        C_answer: q.C_answer || '',
        D_answer: q.D_answer || '',
        answer: q.answer || '',
        batch: q.batch ?? '',
        analysis: q.analysis || '',
        knowledge_points: q.knowledge_points || '',
        primary_knowledge: q.primary_knowledge || ''
      }
    } else {
      message.value = data?.error_msg || '加载失败'
      messageType.value = 'error'
    }
  } catch {
    message.value = '网络错误'
    messageType.value = 'error'
  }
}

async function onSubmit() {
  message.value = ''
  messageType.value = ''
  const p = form.value
  if (!p.question_type || !p.content || !p.answer || !p.batch || p.score === '' || p.score === null) {
    message.value = '请完善必填项'
    messageType.value = 'error'
    return
  }
  try {
    const payload = { id: id.value, ...p }
    const { data } = await apiManageQuestionSave(payload)
    if (data?.success) {
      router.push('/manage/questions')
    } else {
      message.value = data?.error_msg || '保存失败'
      messageType.value = 'error'
    }
  } catch {
    message.value = '网络错误，保存失败'
    messageType.value = 'error'
  }
}

function cancel() { router.push('/manage/questions') }

onMounted(loadDetail)
</script>

<template>
  <div class="max-w-2xl mx-auto py-10 px-6">
    <div class="bg-white shadow rounded p-6">
      <h2 class="text-2xl font-semibold mb-6 text-blue-600">{{ isEdit ? '编辑题目' : '新增题目' }}</h2>
      <div v-if="message" :class="['mb-4 p-3 rounded', messageType==='error' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600']">{{ message }}</div>
      <form @submit.prevent="onSubmit" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block mb-1 text-gray-700">题型</label>
            <select v-model="form.question_type" required class="w-full border rounded px-3 py-2">
              <option value="单选">单选</option>
              <option value="多选">多选</option>
              <option value="判断">判断</option>
              <option value="操作">操作</option>
              <option value="Office操作">Office操作</option>
            </select>
          </div>
          <div>
            <label class="block mb-1 text-gray-700">分数</label>
            <input v-model.number="form.score" type="number" min="1" class="w-full border rounded px-3 py-2" />
          </div>
        </div>

        <div>
          <label class="block mb-1 text-gray-700">题目内容</label>
          <textarea v-model="form.content" required class="w-full border rounded px-3 py-2 h-24"></textarea>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block mb-1 text-gray-700">选项A</label>
            <input v-model="form.A_answer" type="text" class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block mb-1 text-gray-700">选项B</label>
            <input v-model="form.B_answer" type="text" class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block mb-1 text-gray-700">选项C</label>
            <input v-model="form.C_answer" type="text" class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block mb-1 text-gray-700">选项D</label>
            <input v-model="form.D_answer" type="text" class="w-full border rounded px-3 py-2" />
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block mb-1 text-gray-700">答案</label>
            <input v-model="form.answer" type="text" required class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block mb-1 text-gray-700">批次</label>
            <input v-model.number="form.batch" type="number" required class="w-full border rounded px-3 py-2" />
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block mb-1 text-gray-700">考纲大类/知识点(逗号分隔)</label>
            <input v-model="form.knowledge_points" type="text" class="w-full border rounded px-3 py-2" placeholder="操作系统,进程管理" />
          </div>
          <div>
            <label class="block mb-1 text-gray-700">一级知识点</label>
            <input v-model="form.primary_knowledge" type="text" class="w-full border rounded px-3 py-2" placeholder="操作系统" />
          </div>
        </div>

        <div>
          <label class="block mb-1 text-gray-700">解析</label>
          <textarea v-model="form.analysis" class="w-full border rounded px-3 py-2 h-24" placeholder="可选，填写题目解析/思路"></textarea>
        </div>

        <div class="flex justify-between mt-4">
          <button type="button" class="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400" @click="cancel">取消</button>
          <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"><i class="fas fa-save mr-2"></i>保存</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
</style>
