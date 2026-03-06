<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiScoreDetail } from '../api/index';

const route = useRoute();
const router = useRouter();
const recordId = route.params.id;

const loading = ref(false);
const errorMsg = ref('');
const examTitle = ref('');
const score = ref(0);
const fullScore = ref(0);
const submitTime = ref('');
const details = ref([]);

const fetchDetail = async () => {
  loading.value = true;
  errorMsg.value = '';
  try {
    const res = await apiScoreDetail(recordId);
    if (res.data && res.data.success) {
      examTitle.value = res.data.exam_title || '';
      score.value = res.data.score || 0;
      fullScore.value = res.data.full_score || 0;
      submitTime.value = res.data.submit_time || '';
      details.value = Array.isArray(res.data.details) ? res.data.details : [];
    } else {
      errorMsg.value = res.data.error_msg || '获取详情失败';
    }
  } catch (e) {
    errorMsg.value = '网络错误，无法获取详情';
  } finally {
    loading.value = false;
  }
};

onMounted(fetchDetail);

function goBack() {
  router.back();
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-10">
    <div class="max-w-7xl mx-auto px-6">
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
        <div class="flex items-start justify-between gap-4 mb-6">
          <div>
            <h2 class="text-2xl md:text-3xl font-bold text-gray-900">考试详情</h2>
            <p class="text-sm text-gray-500 mt-1">查看该次考试的题目作答与评分说明</p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button class="px-4 py-2 rounded-md border border-gray-200 text-gray-700 hover:bg-gray-50 active:scale-95 transition text-sm" @click="goBack">返回</button>
            <button class="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 active:scale-95 transition text-sm" @click="fetchDetail" :disabled="loading">
              <span v-if="!loading">刷新</span>
              <span v-else>刷新中...</span>
            </button>
          </div>
        </div>

        <div v-if="examTitle" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 text-sm">
          <div class="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <div class="text-gray-500">考试</div>
            <div class="mt-1 font-medium text-gray-900">{{ examTitle }}</div>
          </div>
          <div class="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <div class="text-gray-500">得分</div>
            <div class="mt-1 font-semibold text-green-600">{{ score }}<span class="text-gray-400 font-normal"> / {{ fullScore }}</span></div>
          </div>
          <div class="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <div class="text-gray-500">提交时间</div>
            <div class="mt-1 font-medium text-gray-900">{{ submitTime }}</div>
          </div>
        </div>

        <div v-if="errorMsg" class="mb-4 rounded-md border border-red-200 bg-red-50 text-red-700 px-4 py-2 text-sm">{{ errorMsg }}</div>

        <div class="overflow-x-auto -mx-4 md:mx-0">
          <table class="min-w-full divide-y divide-gray-100 text-sm mx-4 md:mx-0">
            <thead class="bg-gray-50 text-gray-600">
              <tr>
                <th class="px-3 py-3 text-left font-medium">题目ID</th>
                <th class="px-3 py-3 text-left font-medium">类型</th>
                <th class="px-3 py-3 text-left font-medium">状态/得分</th>
                <th class="px-3 py-3 text-left font-medium">你的答案</th>
                <th class="px-3 py-3 text-left font-medium">正确答案</th>
                <th class="px-3 py-3 text-left font-medium">错误原因/评分说明</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-if="loading">
                <td colspan="6" class="px-4 py-6 text-center text-gray-500">加载中...</td>
              </tr>
              <tr v-for="it in details" :key="`${it.type}_${it.question_id}`" class="hover:bg-gray-50">
                <td class="px-3 py-3 text-gray-900">{{ it.question_id }}</td>
                <td class="px-3 py-3">{{ it.type === '操作' ? '操作题' : it.type }}</td>
                <td class="px-3 py-3">
                  <template v-if="it.type !== '操作'">
                    <span :class="it.is_correct ? 'text-green-600' : 'text-rose-600'">{{ it.is_correct ? '正确' : '错误' }}</span>
                    <span v-if="it.q_total != null" class="ml-2 text-blue-600">{{ it.q_score != null ? it.q_score : 0 }}/{{ it.q_total }}</span>
                  </template>
                  <template v-else>
                    <span class="text-blue-600">{{ it.op_score != null ? it.op_score : '-' }}/{{ it.op_total != null ? it.op_total : '-' }}</span>
                    <span v-if="it.file_name" class="ml-2 text-gray-400 text-xs">({{ it.file_name }})</span>
                  </template>
                </td>
                <td class="px-3 py-3 whitespace-pre-wrap break-words">{{ it.user_answer }}</td>
                <td class="px-3 py-3 whitespace-pre-wrap break-words">{{ it.correct_answer }}</td>
                <td class="px-3 py-3 whitespace-pre-wrap break-words text-left">
                  <template v-if="it.type === '操作'">
                    <div v-if="it.op_msg">{{ it.op_msg }}</div>
                    <div v-else class="text-gray-400">无</div>
                    <div v-if="it.template_url" class="mt-1">
                      <a :href="it.template_url" target="_blank" class="text-indigo-600 hover:underline">下载模板</a>
                    </div>
                    <div v-if="it.analysis" class="mt-1 text-gray-700 whitespace-pre-wrap break-words">
                      <span class="text-gray-500">解析：</span>{{ it.analysis }}
                    </div>
                  </template>
                  <template v-else>
                    <div class="text-gray-400">—</div>
                    <div v-if="it.analysis" class="mt-1 text-gray-700 whitespace-pre-wrap break-words">
                      <span class="text-gray-500">解析：</span>{{ it.analysis }}
                    </div>
                  </template>
                </td>
              </tr>
              <tr v-if="!details.length && !loading">
                <td colspan="6" class="px-4 py-10 text-center text-gray-400">暂无题目详情</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
