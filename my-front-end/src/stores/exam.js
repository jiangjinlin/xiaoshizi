import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiExamList } from '../api/index'

const TYPE_ORDER = { '单选':1, '多选':2, '判断':3, '操作':4 }

export const useExamStore = defineStore('exam', () => {
  const exams = ref([])
  const loading = ref(false)
  const error = ref('')

  function sortQuestions(list=[]) {
    return [...list].sort((a,b)=>{
      const oa = TYPE_ORDER[a.type] ?? 99
      const ob = TYPE_ORDER[b.type] ?? 99
      if (oa!==ob) return oa-ob
      return (a.id||0)-(b.id||0)
    })
  }

  async function fetchExams() {
    if (loading.value) return
    loading.value = true
    error.value = ''
    try {
      const res = await apiExamList()
      if (res.data?.success) {
        exams.value = (res.data.exams||[]).map(e => ({
          ...e,
          exam_id: e.id,
          questions: sortQuestions(e.questions||[])
        }))
      } else {
        exams.value = []
        error.value = res.data?.error_msg || '获取考试失败'
      }
    } catch (e) {
      error.value = '网络错误'
      exams.value = []
      throw e
    } finally {
      loading.value = false
    }
  }

  return { exams, loading, error, fetchExams }
})

