import { ref, computed, watch } from 'vue'
import { apiManageQuestionList } from '../api/index'

// 本地缓存键
const CACHE_KEY = 'question_adv_filters_v1'

export function useQuestionBank({ enableFilterCache = false } = {}) {
  const loading = ref(false)
  const errorMsg = ref('')
  const questions = ref([])          // 原始（已过滤服务器条件后的）
  const questionCount = ref(0)
  const typeCounts = ref({})
  const knowledgeOptions = ref([])
  const primaryOptions = ref([])
  const pendingCount = ref(0)

  // 过滤条件（给高级页使用）
  const filter = ref({ types: [], batch: '', knowledge: '', primary: '', keyword: '', unreviewedOnly: false })

  // 分页（前端分页）
  const page = ref(1)
  const pageSize = ref(20)

  const total = computed(() => questions.value.length)
  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
  const pageData = computed(() => {
    const start = (page.value - 1) * pageSize.value
    return questions.value.slice(start, start + pageSize.value)
  })

  function loadCache() {
    if (!enableFilterCache) return
    try {
      const raw = localStorage.getItem(CACHE_KEY)
      if (raw) {
        const obj = JSON.parse(raw)
        if (obj && typeof obj === 'object') {
          filter.value = { types: obj.types || [], batch: obj.batch||'', knowledge: obj.knowledge||'', primary: obj.primary||'', keyword: obj.keyword||'', unreviewedOnly: !!obj.unreviewedOnly }
          page.value = obj.page || 1
          pageSize.value = obj.pageSize || 20
        }
      }
    } catch {}
  }
  function saveCache() {
    if (!enableFilterCache) return
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ ...filter.value, page: page.value, pageSize: pageSize.value }))
    } catch {}
  }

  watch([filter, page, pageSize], saveCache, { deep: true })

  async function fetchList() {
    loading.value = true
    errorMsg.value = ''
    try {
      const params = {}
      if (filter.value.types.length) params.types = filter.value.types.join(',')
      if (filter.value.batch) params.batch = filter.value.batch
      if (filter.value.knowledge) params.knowledge = filter.value.knowledge
      if (filter.value.primary) params.primary = filter.value.primary
      if (filter.value.keyword) params.keyword = filter.value.keyword
      if (filter.value.unreviewedOnly) params.reviewed = 0
      const { data } = await apiManageQuestionList(params)
      if (data?.success) {
        questions.value = data.questions || []
        questionCount.value = data.question_count || data.questions?.length || 0
        typeCounts.value = data.type_counts || {}
        knowledgeOptions.value = data.knowledge_points || []
        primaryOptions.value = data.primary_knowledge_options || []
        pendingCount.value = data.pending_count || 0
        if (page.value > pageCount.value) page.value = 1
      } else {
        errorMsg.value = data?.error_msg || '加载失败'
        questions.value = []
        questionCount.value = 0
        pendingCount.value = 0
      }
    } catch {
      errorMsg.value = '网络错误'
      questions.value = []
      questionCount.value = 0
      pendingCount.value = 0
    } finally {
      loading.value = false
    }
  }

  function resetFilter() {
    filter.value = { types: [], batch: '', knowledge: '', primary: '', keyword: '', unreviewedOnly: false }
    page.value = 1
    fetchList()
  }

  function setSimpleMode() {
    // 简洁页无需过滤即可使用 fetchList()
  }

  return {
    // state
    loading, errorMsg, questions, questionCount, typeCounts, knowledgeOptions, primaryOptions, pendingCount,
    filter, page, pageSize, total, pageCount, pageData,
    // methods
    fetchList, resetFilter, loadCache, setSimpleMode
  }
}
