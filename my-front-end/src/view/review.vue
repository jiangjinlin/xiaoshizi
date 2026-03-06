<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <nav class="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-5xl mx-auto h-full px-6 flex items-center justify-between">
        <div class="flex items-center gap-6 relative">
          <AppLogo :height="36" class="cursor-pointer" @click="$router.push('/student')" />
          <span class="hidden sm:inline text-lg font-semibold text-gray-700">题目审查</span>
          <!-- 应用考纲：按钮 + 弹出面板 -->
          <div>
            <button class="h-9 px-3 rounded-lg text-xs text-gray-700 bg-white/70 border border-gray-300 hover:bg-white transition" @click="showSyllabus = !showSyllabus">应用考纲</button>
            <div v-if="showSyllabus" class="absolute left-0 top-12 z-50 w-[26rem] rounded-xl border border-gray-200 bg-white/95 backdrop-blur shadow-lg p-4">
              <div class="text-sm font-semibold text-gray-800 mb-2">选择考纲</div>
              <div class="grid grid-cols-2 gap-2 mb-3">
                <select v-model="selProvince" class="h-9 px-2 rounded border border-gray-300 bg-white/80 text-sm">
                  <option value="">选择省份</option>
                  <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
                </select>
                <select v-model="selMajor" class="h-9 px-2 rounded border border-gray-300 bg-white/80 text-sm">
                  <option value="">选择专业</option>
                  <option v-for="m in majorsFor(selProvince)" :key="m" :value="m">{{ m }}</option>
                </select>
              </div>
              <div class="flex items-center gap-2">
                <button class="h-9 px-3 rounded bg-primary text-white text-xs disabled:opacity-50" :disabled="!selProvince || !selMajor" @click="applySyllabus">应用</button>
                <button v-if="usingPreset" class="h-9 px-3 rounded border text-xs bg-white hover:bg-gray-50" @click="clearSyllabus">清除</button>
                <div class="text-[11px] text-gray-500 ml-auto" v-if="usingPreset">已应用：{{ appliedPresetName }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <button class="px-4 h-10 rounded-lg text-gray-600 bg-white/60 border border-gray-200 hover:bg-white hover:text-gray-800 transition" @click="goBack">返回学生页</button>
        </div>
      </div>
    </nav>

    <div class="max-w-5xl mx-auto pt-24 pb-16 px-4">
      <div class="rounded-2xl border border-gray-200 bg-white/70 backdrop-blur shadow-sm overflow-hidden">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-800">逐题审查</h2>
          <div class="text-xs text-gray-500">共识阈值：5 人</div>
        </div>

        <div v-if="loading" class="p-12 text-center text-gray-500">加载中...</div>
        <div v-else-if="!question" class="p-12 text-center text-gray-400">暂无可审题目，感谢您的贡献！</div>

        <div v-else class="p-6 space-y-6">
          <!-- 派发筛选器 -->
          <div class="rounded-lg border border-gray-200 bg-white/60 p-4 flex flex-wrap gap-3 items-center text-xs text-gray-700">
            <label class="inline-flex items-center gap-1">
              <input type="checkbox" v-model="filters.pending_only" /> 仅未达共识
            </label>
            <label class="inline-flex items-center gap-1">
              <input type="checkbox" v-model="filters.conflict_only" /> 仅存在分歧
            </label>
            <!-- 移除批次筛选 -->
            <div class="flex items-center gap-1">
              <span>考纲</span>
              <select v-model="filters.kp" class="h-8 px-2 rounded border border-gray-300 bg-white/70">
                <option value="">全部</option>
                <option v-for="kp in kpOptions" :key="kp" :value="kp">{{ kp }}</option>
              </select>
            </div>
            <button class="ml-auto h-8 px-3 rounded bg-white border border-gray-300 hover:bg-gray-50" @click="reloadWithFilters">应用</button>
          </div>

          <div>
            <div class="mb-2 flex items-center gap-2">
              <span class="inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-full bg-primary/10 text-primary">{{ question.type }}</span>
            </div>
            <div class="text-gray-800 leading-relaxed whitespace-pre-wrap">{{ question.content }}</div>
            <!-- 仅当题干未内联选项时渲染 ABCD 列表 -->
            <ul v-if="question.options && question.options.length && !hasInlineChoices(question.content)" class="mt-3 space-y-1 text-sm">
              <li v-for="opt in question.options" :key="opt.key" class="text-gray-700">{{ opt.key }}. {{ formatLabel(opt.label) }}</li>
            </ul>
          </div>

          <div class="grid md:grid-cols-2 gap-6">
            <div class="space-y-4">
              <h3 class="text-sm font-semibold text-gray-700">您的建议</h3>
              <div v-if="question.type==='单选'" class="space-y-2 text-sm">
                <template v-if="!hasInlineChoices(question.content)">
                  <label v-for="opt in question.options" :key="'s-'+opt.key" class="flex items-center gap-2 cursor-pointer">
                    <input type="radio" :value="opt.key" v-model="form.suggested_answer" />
                    <span>{{ opt.key }}. {{ formatLabel(opt.label) }}</span>
                  </label>
                </template>
                <template v-else>
                  <div class="flex flex-wrap gap-2">
                    <label v-for="k in ['A','B','C','D']" :key="'s-inline-'+k" class="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white/70 hover:bg-primary/5 cursor-pointer">
                      <input type="radio" :value="k" v-model="form.suggested_answer" />
                      <span class="font-mono">{{ k }}</span>
                    </label>
                  </div>
                </template>
              </div>
              <div v-else-if="question.type==='判断'" class="space-y-2 text-sm">
                <label class="flex items-center gap-2 cursor-pointer"><input type="radio" value="A" v-model="form.suggested_answer" />正确</label>
                <label class="flex items-center gap-2 cursor-pointer"><input type="radio" value="B" v-model="form.suggested_answer" />错误</label>
              </div>
              <div v-else-if="question.type==='多选'" class="space-y-2 text-sm">
                <div class="text-xs text-gray-500">可多选，系统会自动按字母排序合并</div>
                <template v-if="!hasInlineChoices(question.content)">
                  <label v-for="opt in question.options" :key="'m-'+opt.key" class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" :value="opt.key" v-model="multi" />
                    <span>{{ opt.key }}. {{ formatLabel(opt.label) }}</span>
                  </label>
                </template>
                <template v-else>
                  <div class="flex flex-wrap gap-2">
                    <label v-for="k in ['A','B','C','D']" :key="'m-inline-'+k" class="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white/70 hover:bg-primary/5 cursor-pointer">
                      <input type="checkbox" :value="k" v-model="multi" />
                      <span class="font-mono">{{ k }}</span>
                    </label>
                  </div>
                </template>
              </div>

              <div class="grid grid-cols-1 gap-3">
                <!-- 考纲大类（联动上游） -->
                <div>
                  <select v-model="form.suggested_kp" class="h-10 px-3 rounded border border-gray-300 bg-white/80 text-sm outline-none focus:ring-2 focus:ring-primary/30 w-full">
                    <option value="">选择考纲大类</option>
                    <option v-for="kp in kpOptions" :key="kp" :value="kp">{{ kp }}</option>
                  </select>
                </div>
                <!-- 一级知识点（根据上游联动过滤） -->
                <div>
                  <select v-model="form.suggested_primary" class="h-10 px-3 rounded border border-gray-300 bg-white/80 text-sm outline-none focus:ring-2 focus:ring-primary/30 w-full">
                    <option value="">选择一级知识点</option>
                    <option v-for="p in filteredPrimaryOptions" :key="p" :value="p">{{ p }}</option>
                  </select>
                </div>
                <label class="inline-flex items-center gap-2 text-sm text-gray-700 select-none">
                  <input type="checkbox" v-model="form.answer_wrong" />
                  <span>当前标准答案有误</span>
                </label>
                <textarea v-model.trim="form.suggested_analysis" rows="5" placeholder="添加解析（越详细越好）" class="w-full px-3 py-2 rounded border border-gray-300 bg-white/80 text-sm outline-none focus:ring-2 focus:ring-primary/30"></textarea>
                <div class="text-[11px] text-gray-500">提示：下拉列表来源于“考纲练习”配置，选择考纲后会仅展示对应一级知识点。</div>
              </div>

              <div class="flex flex-wrap gap-3 pt-2 items-center">
                <button class="h-10 px-4 rounded-lg bg-primary text-white text-xs font-medium shadow-sm hover:bg-primary/90 transition" :disabled="submitting" @click="submitAndNext">{{ submitting ? '提交中...' : '提交并下一题' }}</button>
                <button class="h-10 px-4 rounded-lg bg-white/70 border border-gray-300 text-gray-700 text-xs font-medium hover:bg-white transition" @click="loadNext">跳过</button>
                <router-link class="text-primary text-xs hover:underline" to="/review/rank">查看贡献榜</router-link>
              </div>

              <div v-if="feedback" class="mt-2 text-xs text-gray-600">
                <div>当前共识人数：<span class="font-semibold text-primary">{{ feedback.count }}</span></div>
                <div v-if="feedback.promoted" class="text-green-600">已达成共识，题库已更新。</div>
              </div>
            </div>

            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-gray-700">参考信息（当前题库）</h3>
              <div class="text-sm text-gray-600">
                <div>标准答案：<span class="font-mono">{{ question.current_answer || '（暂无）' }}</span></div>
                <div>考纲大类：<span>{{ question.current_kp || '（暂无）' }}</span></div>
                <div>一级知识点：<span>{{ question.current_primary || '（暂无）' }}</span></div>
              </div>
              <div>
                <div class="text-xs text-gray-500 mb-1">解析</div>
                <div class="text-sm text-gray-700 whitespace-pre-wrap break-words" v-if="question.current_analysis">{{ question.current_analysis }}</div>
                <div v-else class="text-sm text-gray-400">（暂无解析）</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiReviewNext, apiReviewSubmit, apiSyllabusOptions, apiSyllabusPresets } from '../api/index'
import AppLogo from '../components/AppLogo.vue'

// 预置考纲：四川省-计算机类（作为无后端数据时的兜底）
const SYLLABUS_PRESETS = {
  '四川省': {
    '计算机类': {
      '计算机基础': [
        '了解计算机的发展、特点、分类及应用领域',
        '了解计算机的工作原理，熟悉计算机系统的组成',
        '理解计算机软件的概念和分类，了解程序的编译、解释等基本概念',
        '了解计算机中数据的分类和表示方法，掌握二进制、八进制、十进制、十六进制的转换方法',
        '理解数据的存储及字符的编码方法',
        '理解微型计算机的 CPU、主板、存储器、常用外部设备的主要性能指标',
        '了解总线的概念及微型计算机中常见的总线结构',
        '理解常用外部设备接口的作用',
        '了解 BIOS 和 CMOS 在计算机系统硬件配置和管理中的作用',
        '理解计算机病毒的概念、基本特征、种类及防治',
        '了解多媒体技术的基本概念及应用',
        '了解云计算、大数据、人工智能、虚拟现实、物联网等新一代信息技术的发展及应用领域',
        '了解信息安全、知识产权保护等法律法规'
      ],
      '数据库基础': [
        '了解数据、数据库、数据库系统及数据库管理系统等概念',
        '理解实体模型的相关术语以及实体间的关系',
        '了解数据模型和关系型数据库的基本特点',
        '理解数据表、字段、记录、关键字等基本概念',
        '理解选择、连接、投影三种关系运算',
        '掌握创建、打开、关闭数据库的方法',
        '了解 Access 数据库的对象，理解 Access 常用数据类型',
        '理解数据库运算符、表达式及其构成',
        '掌握创建数据表、修改和维护表结构的方法',
        '掌握数据表记录的录入、定位、编辑、删除等操作方法',
        '掌握字段标题、显示和输出格式、默认值、输入掩码、有效性规则等属性的设置方法',
        '掌握数据表格式的设置方法',
        '理解主键、索引的概念，掌握其设置方法',
        '掌握创建表间关系、设置参照完整性的方法',
        '理解查询的功能和类型，掌握创建与修改查询的方法',
        '理解 select 语句的基本语法并掌握其使用方法',
        '掌握 create、insert、update、delete 语句的使用方法',
        '了解常用国产数据库'
      ],
      '操作系统基础': [
        '理解操作系统的概念、主要功能及类型',
        '了解主流操作系统及其应用场景，了解常用国产操作系统',
        '掌握操作系统的安装、启动和退出方法',
        '了解切换用户、注销、锁定、重新启动、睡眠和休眠等作用与区别',
        '了解安全模式的概念及作用',
        '掌握驱动程序及应用软件的安装与卸载方法',
        '掌握操作系统账户的管理方法',
        '掌握磁盘分区、格式化、磁盘清理和碎片整理的操作方法',
        '掌握系统备份和还原方法',
        '了解获取帮助信息的方法',
        '理解桌面、图标、任务栏、窗口、对话框、开始菜单、快捷方式等概念',
        '理解文件和文件夹的概念、作用、命名规则，熟悉常见文件类型',
        '理解回收站、剪贴板的概念及作用',
        '了解 dir、cd、md、rd、copy、ren、del 等常用 cmd 命令的功能'
      ],
      '计算机网络基础': [
        '了解计算机网络的概念、组成、分类及应用',
        '理解计算机网络拓扑结构及分类',
        '理解 OSI 参考模型、TCP/IP 模型及其主要协议',
        '了解网络传输介质，熟悉常见的网络设备',
        '理解局域网的概念、组成和结构，掌握局域网的组建、配置与管理方法',
        '了解虚拟局域网（VLAN）的原理',
        '掌握常用网络测试命令（如 ping、ipconfig、tracert、netstat 等）的使用方法',
        '了解 Internet 概念、发展及接入方式',
        '掌握 IP 地址的概念、分类、组成、表示方法、子网掩码及其配置方法，了解 IPv6 基本知识',
        '掌握 WWW、URL、E-mail、DNS、FTP、Telnet 等网络服务（应用）的使用方法',
        '掌握常用浏览器和搜索引擎的使用方法',
        '了解加密与认证、防火墙等常用信息安全技术的基本概念和原理，掌握常用软件防火墙的安装、配置及使用方法',
        '了解计算机网络病毒，掌握网络防病毒软件的安装、配置及使用方法',
        '了解网页与网站的概念',
        '理解 HTML 基本结构、常用标记',
        '掌握列表、超链接、表格、表单、多媒体等标记以及 CSS 的使用方法'
      ],
      '图文编辑基础': [
        '了解 Word 的工作界面、视图',
        '掌握 Word 启动与退出的方法',
        '掌握文档的创建、打开、保存、保护、打印和关闭等基本操作方法',
        '掌握文本的录入、编辑、排版等基本操作方法，了解文本编辑的常用快捷键',
        '了解字符格式、段落格式及样式',
        '掌握图形、公式、图片与文字的环绕方式',
        '了解表格、图表、文本框、艺术字的功能',
        '了解邮件合并、修订、批注等功能',
        '掌握页眉、页脚、页码、目录及页面设置的基本操作方法'
      ],
      '电子表格基础': [
        '了解 Excel 的工作界面、视图',
        '掌握 Excel 启动与退出的方法',
        '理解工作簿、工作表及单元格等基本概念',
        '掌握工作簿新建、保存、打开和关闭的方法',
        '掌握工作表新建、删除、重命名、复制和移动的方法',
        '理解 Excel 中常用的数据类型',
        '掌握数据输入、编辑及填充的方法',
        '掌握单元格选定、插入、删除、复制和移动的方法',
        '掌握单元格格式设置、表格格式套用、单元格样式设置的方法',
        '掌握冻结窗格、条件格式设置的方法',
        '理解单元格引用的概念及分类，掌握单元格引用的方法',
        '理解常用函数功能，掌握公式的使用方法',
        '掌握排序、筛选、分类汇总、合并计算的方法',
        '掌握数据透视表创建的方法',
        '了解图表构成及图表类型，掌握图表创建、图表格式设置的方法',
        '掌握分页符、打印标题、页面设置、预览和打印的使用方法',
        '掌握工作簿或工作表保护、隐藏的方法'
      ],
      '演示文稿基础': [
        '了解 PowerPoint 的工作界面、视图',
        '掌握 PowerPoint 启动与退出的方法',
        '掌握演示文稿新建、打开、保存和关闭的方法',
        '掌握添加和设置文字的方法',
        '掌握插入图片、艺术字、形状、智能图形（SmartArt 图形）、图表、音频、视频等对象并进行相关设置的方法',
        '了解幻灯片版式、配色方案、前景色、背景色、备注页、母版等概念',
        '掌握超链接、动作按钮、动画效果、切换方式和放映方式的设置方法',
        '了解幻灯片打包和输出的方法'
      ]
    }
  }
}

const router = useRouter()
const loading = ref(true)
const submitting = ref(false)
const question = ref(null)
const feedback = ref(null)

const form = reactive({
  question_id: null,
  suggested_answer: '',
  suggested_kp: '',
  suggested_primary: '',
  suggested_analysis: '',
  answer_wrong: false,
})
const multi = ref([])
const kpOptions = ref([])
const primaryOptions = ref([])
const kpToPrimary = ref({})
// 应用考纲开关与选择
const showSyllabus = ref(false)
const selProvince = ref('')
const selMajor = ref('')
const usingPreset = ref(false)
const appliedPresetName = ref('')

// 后端预置：省份与省->专业映射
const provincesFromApi = ref([])
const majorsByProvince = ref({})

const filteredPrimaryOptions = computed(() => {
  const kp = form.suggested_kp || ''
  if (!kp) return primaryOptions.value
  const arr = kpToPrimary.value[kp]
  return Array.isArray(arr) && arr.length ? arr : primaryOptions.value
})

const filters = reactive({ pending_only: true, conflict_only: false, kp: '' })

watch(multi, (val) => {
  // 合并多选
  const set = Array.from(new Set((val || []).map(v => String(v).toUpperCase()))).sort()
  form.suggested_answer = set.join('')
})

// 取消：选择一级知识点自动填充解析（改为手动输入）
// 已移除相关 watch

function buildFromPreset(province, major){
  const prov = SYLLABUS_PRESETS[province] || {}
  const spec = prov[major] || {}
  const kpList = Object.keys(spec)
  const ktp = {}
  const primSet = new Set()
  kpList.forEach(kp => {
    const arr = Array.isArray(spec[kp]) ? spec[kp] : []
    ktp[kp] = arr
    arr.forEach(s => primSet.add(s))
  })
  return {
    kpOptions: kpList,
    primaryOptions: Array.from(primSet),
    kpToPrimary: ktp,
  }
}

const provinces = computed(() => {
  return (provincesFromApi.value && provincesFromApi.value.length)
    ? provincesFromApi.value
    : Object.keys(SYLLABUS_PRESETS)
})
function majorsFor(p){
  if (!p) return []
  const m = majorsByProvince.value[p]
  if (Array.isArray(m) && m.length) return m
  const node = SYLLABUS_PRESETS[p] || {}
  return Object.keys(node)
}

async function fetchPresetsMeta(){
  try{
    const { data } = await apiSyllabusPresets()
    if (data?.success){
      provincesFromApi.value = data.provinces || []
      majorsByProvince.value = data.majors_by_province || {}
    }
  }catch{}
}

async function applySyllabus(){
  const p = selProvince.value, m = selMajor.value
  if (!p || !m) return
  // 优先从后端读取指定省份专业的映射
  try{
    const { data } = await apiSyllabusPresets({ province: p, major: m })
    if (data?.success && Array.isArray(data.kp_list) && data.kp_list.length){
      kpOptions.value = data.kp_list
      kpToPrimary.value = data.kp_to_primary || {}
      const primSet = new Set()
      Object.values(kpToPrimary.value).forEach(arr => (arr||[]).forEach(x => primSet.add(x)))
      primaryOptions.value = Array.from(primSet)
      usingPreset.value = true
      appliedPresetName.value = `${p}·${m}`
      // 清空选择，让用户按新考纲重新选择
      form.suggested_kp = ''
      form.suggested_primary = ''
      // 解析改为手动填写
      // form.suggested_analysis = '' // 不强制清空，保留已写内容
      showSyllabus.value = false
      return
    }
  }catch{}
  // 后端无该考纲时，回退到内置预置
  const pack = buildFromPreset(p, m)
  kpOptions.value = pack.kpOptions
  primaryOptions.value = pack.primaryOptions
  kpToPrimary.value = pack.kpToPrimary
  usingPreset.value = true
  appliedPresetName.value = `${p}·${m}`
  form.suggested_kp = ''
  form.suggested_primary = ''
  showSyllabus.value = false
}

async function clearSyllabus(){
  usingPreset.value = false
  appliedPresetName.value = ''
  await loadOptions() // 恢复后端默认选项
  form.suggested_kp = ''
  form.suggested_primary = ''
}

function resetForm() {
  form.question_id = null
  form.suggested_answer = ''
  form.suggested_kp = ''
  form.suggested_primary = ''
  // 解析改为手动，保持不动
  form.answer_wrong = false
  multi.value = []
  feedback.value = null
}

async function loadOptions(){
  try{
    const { data } = await apiSyllabusOptions()
    if (data?.success){
      if (!usingPreset.value){
        kpOptions.value = Array.isArray(data.knowledge_points) ? data.knowledge_points : []
        primaryOptions.value = Array.isArray(data.primary_points) ? data.primary_points : []
        kpToPrimary.value = data.kp_to_primary || {}
      }
    }
  }catch{}
}

function hasInlineChoices(text){
  const t = String(text||'')
  return /(^|[\n\r])\s*[A-D]\s*[。.、．:：]/.test(t)
}
function formatLabel(label){
  const s = String(label || '')
  return s.replace(/^\s*[A-D]\s*[。.、．:：]\s*/u, '')
}

async function loadNext() {
  if (!kpOptions.value.length) await loadOptions()
  // 同步拉取后端可用预置元数据（省份/专业）
  if (!provincesFromApi.value.length) await fetchPresetsMeta()
  loading.value = true
  feedback.value = null
  try {
    const params = {}
    if (filters.pending_only) params.pending_only = 1
    if (filters.conflict_only) params.conflict_only = 1
    // 始终仅审未审核题目
    params.reviewed = 0
    // 批次筛选已取消
    if (filters.kp) params.kp = filters.kp
    const { data } = await apiReviewNext(params)
    if (data?.success && data.question) {
      question.value = data.question
      form.question_id = data.question.id
      // 取消判断题默认预选，保持空，让学生主动选择
      form.suggested_answer = ''
      if (Array.isArray(multi.value)) multi.value = []
    } else {
      question.value = null
    }
  } catch (e) {
    question.value = null
  } finally {
    loading.value = false
  }
}

async function submitAndNext() {
  if (!form.question_id || submitting.value) return
  submitting.value = true
  try {
    const payload = { ...form, question_id: form.question_id }
    const { data } = await apiReviewSubmit(payload)
    if (data?.success) {
      feedback.value = { count: data.consensus_count || 0, promoted: !!data.promoted }
      // 短暂停留后切下一题
      setTimeout(() => { loadNext() }, 600)
    }
  } finally {
    submitting.value = false
  }
}

function reloadWithFilters(){ loadNext() }
function goBack(){ router.push('/student') }

loadNext()
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
/* use global .text-primary/.bg-primary from tokens.css */
</style>
