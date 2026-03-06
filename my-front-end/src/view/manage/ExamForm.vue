<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiManageBatchList, apiManageExamDetail, apiManageExamSave } from '../../api/index'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id)
const isEdit = computed(() => !!id.value)

const form = ref({ title: '', start_time: '', end_time: '', duration: '', batches: [] })
const batches = ref([])
const message = ref('')
const messageType = ref('')
const autoDuration = ref(false)

async function loadBatches() {
  try {
    const { data } = await apiManageBatchList()
    if (data?.success) batches.value = data.batches || []
  } catch {}
}

async function loadDetail() {
  if (!isEdit.value) return
  try {
    const { data } = await apiManageExamDetail(id.value)
    if (data?.success && data.exam) {
      const e = data.exam
      const toLocal = (s) => s ? s.replace(' ', 'T') : ''
      form.value = {
        title: e.title,
        start_time: toLocal(e.start_time),
        end_time: toLocal(e.end_time),
        duration: String(e.duration || ''),
        batches: e.batches || []
      }
      autoDuration.value = false // 编辑时默认不自动
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
  if (!form.value.title || !form.value.start_time || !form.value.end_time) {
    message.value = '请完善必填项'
    messageType.value = 'error'
    return
  }
  // 批次至少一项
  if (!form.value.batches || !form.value.batches.length) {
    message.value = '请至少选择一个批次'
    messageType.value = 'error'
    return
  }
  const payload = {
    id: id.value,
    title: form.value.title,
    start_time: form.value.start_time,
    end_time: form.value.end_time,
    duration: autoDuration.value ? '' : form.value.duration, // 留空触发后端自动时长
    batches: form.value.batches,
  }
  try {
    const { data } = await apiManageExamSave(payload)
    if (data?.success) {
      if (data.auto_duration) {
        alert(`保存成功，系统自动计算考试时长为 ${data.duration} 分钟`)
      }
      router.push('/manage/exams')
    } else {
      message.value = data?.error_msg || '保存失败'
      messageType.value = 'error'
    }
  } catch {
    message.value = '网络错误，保存失败'
    messageType.value = 'error'
  }
}

function cancel() { router.push('/manage/exams') }

onMounted(async () => {
  await loadBatches()
  await loadDetail()
})
</script>

<template>
  <div class="max-w-2xl mx-auto py-10 px-6">
    <div class="bg-white shadow rounded p-6">
      <h2 class="text-2xl font-semibold mb-6 text-blue-600">{{ isEdit ? '编辑考试' : '新建考试' }}</h2>
      <div v-if="message" :class="['mb-4 p-3 rounded', messageType==='error' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600']">{{ message }}</div>
      <form @submit.prevent="onSubmit" class="space-y-6">
        <div>
          <label class="block mb-1 text-gray-700 font-medium">考试名称</label>
          <input v-model="form.title" type="text" required class="w-full border rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block mb-1 text-gray-700 font-medium">开始时间</label>
            <input v-model="form.start_time" type="datetime-local" required class="w-full border rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="block mb-1 text-gray-700 font-medium">结束时间</label>
            <input v-model="form.end_time" type="datetime-local" required class="w-full border rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>
        <div>
          <label class="block mb-1 text-gray-700 font-medium">考试时长（分钟）</label>
          <div class="flex items-center gap-3">
            <input :disabled="autoDuration" v-model="form.duration" type="number" min="1" class="w-40 border rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100" placeholder="留空自动" />
            <label class="flex items-center gap-1 text-sm text-gray-600 select-none">
              <input type="checkbox" v-model="autoDuration" /> 自动按开始结束时间计算
            </label>
          </div>
          <p class="mt-1 text-xs text-gray-500">若勾选自动或留空，则后端按(结束-开始)分钟数自动设定。</p>
        </div>
        <div>
          <label class="block mb-2 text-gray-700 font-medium">选择题目批次（可多选，至少1个）</label>
          <select v-model="form.batches" multiple class="w-full border rounded px-4 py-2 h-32 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option v-for="b in batches" :key="b" :value="b">{{ b }}</option>
          </select>
        </div>
        <div class="flex justify-between items-center pt-2">
          <button type="button" class="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400" @click="cancel">取消</button>
          <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"><i class="fas fa-save mr-2"></i>保存</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
</style>
