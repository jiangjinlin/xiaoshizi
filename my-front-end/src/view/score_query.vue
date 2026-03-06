<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { apiScoreQuery } from '../api/index';

const scores = ref([]);
const loading = ref(false);
const errorMsg = ref('');
const router = useRouter();

// 查询成绩
const fetchScores = async () => {
  loading.value = true;
  errorMsg.value = '';
  try {
    const res = await apiScoreQuery({});
    if (res.data && res.data.success) {
      // 兼容后端返回 score_list 或 scores 字段
      scores.value = res.data.scores || res.data.score_list || [];
    } else {
      errorMsg.value = res.data.error_msg || '查询失败';
    }
  } catch (e) {
    errorMsg.value = '网络错误，无法获取成绩';
  } finally {
    loading.value = false;
  }
};

onMounted(fetchScores);

// 删除单条成绩
async function deleteScore(record_id) {
  if (!confirm('确定要删除该成绩记录吗？')) return;
  try {
    const res = await apiScoreQuery({ delete_id: record_id });
    if (res.data && res.data.success) {
      fetchScores();
    } else {
      alert(res.data.error_msg || '删除失败');
    }
  } catch {
    alert('网络错误，删除失败');
  }
}

// 清空所有成绩
async function deleteAll() {
  if (!confirm('确定要清空所有成绩吗？')) return;
  try {
    const res = await apiScoreQuery({ delete_all: 1 });
    if (res.data && res.data.success) {
      fetchScores();
    } else {
      alert(res.data.error_msg || '清空失败');
    }
  } catch {
    alert('网络错误，清空失败');
  }
}

function goBack() {
  router.push('/student');
}

function viewDetail(record_id) {
  if (!record_id) return;
  router.push(`/score_detail/${record_id}`);
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 py-10">
    <div class="max-w-7xl mx-auto px-6">
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
        <div class="flex items-start justify-between gap-4 mb-6">
          <div>
            <h2 class="text-2xl md:text-3xl font-bold text-gray-900">我的考试成绩</h2>
            <p class="text-gray-500 text-sm mt-1">查看历史考试记录与成绩明细</p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button class="px-4 py-2 rounded-md border border-gray-200 text-gray-700 hover:bg-gray-50 active:scale-95 transition text-sm" @click="goBack">返回学生主页</button>
            <button class="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 active:scale-95 transition text-sm" @click="fetchScores" :disabled="loading">
              <span v-if="!loading">刷新</span>
              <span v-else>刷新中...</span>
            </button>
            <button class="px-4 py-2 rounded-md bg-rose-500 text-white hover:bg-rose-600 active:scale-95 transition text-sm" @click="deleteAll">清空所有成绩</button>
          </div>
        </div>

        <div v-if="errorMsg" class="mb-4 rounded-md border border-red-200 bg-red-50 text-red-700 px-4 py-2 text-sm">{{ errorMsg }}</div>

        <div class="overflow-x-auto -mx-4 md:mx-0">
          <table class="min-w-full divide-y divide-gray-100 text-sm mx-4 md:mx-0">
            <thead class="bg-gray-50 text-gray-600">
              <tr>
                <th class="px-4 py-3 text-left font-medium">考试名称</th>
                <th class="px-4 py-3 text-left font-medium">得分</th>
                <th class="px-4 py-3 text-left font-medium">总分</th>
                <th class="px-4 py-3 text-left font-medium">开始时间</th>
                <th class="px-4 py-3 text-left font-medium">结束时间</th>
                <th class="px-4 py-3 text-left font-medium">提交时间</th>
                <th class="px-4 py-3 text-left font-medium">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-if="loading">
                <td colspan="7" class="px-4 py-6 text-center text-gray-500">加载中...</td>
              </tr>
              <tr v-for="score in scores" :key="score.record_id" class="hover:bg-gray-50">
                <td class="px-4 py-3 text-gray-900">{{ score.exam_title }}</td>
                <td class="px-4 py-3">{{ score.score }}</td>
                <td class="px-4 py-3">{{ score.full_score }}</td>
                <td class="px-4 py-3">{{ score.start_time }}</td>
                <td class="px-4 py-3">{{ score.end_time }}</td>
                <td class="px-4 py-3">{{ score.submit_time }}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <button class="px-3 py-1.5 rounded-md bg-blue-600 text-white hover:bg-blue-700 text-xs font-medium" @click="viewDetail(score.record_id)">详情</button>
                    <button class="px-3 py-1.5 rounded-md bg-rose-500 text-white hover:bg-rose-600 text-xs font-medium" @click="deleteScore(score.record_id)">删除</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!scores.length && !loading">
                <td colspan="7" class="px-4 py-10 text-center text-gray-400">暂无成绩记录</td>
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