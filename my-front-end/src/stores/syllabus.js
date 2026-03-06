import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiSyllabusPresets, apiSyllabusSelection, apiSyllabusSelectionSave } from '../api'

const LS_KEY = 'global_syllabus'

export const useSyllabusStore = defineStore('syllabus', () => {
  const province = ref('')
  const major = ref('')
  const provinces = ref([])
  const majorsByProvince = ref({})

  function loadFromLocal(){
    try{
      const raw = JSON.parse(localStorage.getItem(LS_KEY) || 'null')
      if(raw){ province.value = raw.province || ''; major.value = raw.major || '' }
    }catch{}
  }
  function saveToLocal(){
    try{ localStorage.setItem(LS_KEY, JSON.stringify({ province: province.value, major: major.value })) }catch{}
  }
  async function saveToServer(){
    try { await apiSyllabusSelectionSave(province.value, major.value) } catch {}
  }
  async function loadFromServer(){
    try {
      const { data } = await apiSyllabusSelection()
      if (data?.success) {
        const sp = data.province || ''
        const sm = data.major || ''
        if (sp || sm) {
          province.value = sp
          // 确保所选专业有效
          major.value = sm
          saveToLocal()
          return true
        }
      }
    } catch {}
    return false
  }

  async function init(){
    // 优先采用服务器会话中的选择（若已登录）
    const got = await loadFromServer()
    if (!got) {
      // 回落本地
      loadFromLocal()
      // 若本地有选择，尝试同步到服务器（登录后才成功）
      if (province.value || major.value) {
        saveToServer()
      }
    }
  }

  async function loadPresets(){
    try{
      const { data } = await apiSyllabusPresets()
      if(data?.success){
        provinces.value = data.provinces || []
        majorsByProvince.value = data.majors_by_province || {}
      }
    }catch{}
  }

  function setProvince(p){
    province.value = p || ''
    // 省份变化时校验专业
    if(!getMajors.value.includes(major.value)) major.value = ''
    saveToLocal()
    saveToServer()
  }
  function setMajor(m){
    major.value = m || ''
    saveToLocal()
    saveToServer()
  }
  function clear(){
    province.value = ''
    major.value = ''
    saveToLocal()
    // 清空服务器会话中的选择
    saveToServer()
  }

  const getMajors = computed(() => majorsByProvince.value[province.value] || [])
  const selected = computed(() => ({ province: province.value, major: major.value }))

  // 初始化：尝试从服务器/本地恢复
  init()
  // 不自动 loadPresets，交给组件首次显示时调用

  return { province, major, provinces, majorsByProvince, getMajors, selected, loadPresets, setProvince, setMajor, clear }
})
