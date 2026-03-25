<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { apiManageStudentList, apiManageStudentSave, apiManageStudentDelete, apiManageStudentsBatchDegradeVip, apiManageFaceReset } from '../../api/index'
import { useRoute, useRouter } from 'vue-router'

const loading = ref(false)
const errorMsg = ref('')
const students = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const roles = ref(['学生', 'VIP', '老师', '管理员'])

const role = ref(localStorage.getItem('role') || '')
const isAdmin = computed(() => role.value === '管理员')
const roleHome = computed(() => role.value === '管理员' ? '/admin' : role.value === '老师' ? '/teacher' : (role.value === '学生' || role.value === 'VIP') ? '/student' : '/')

const route = useRoute();
const router = useRouter()
// 增加过滤 + 服务端排序字段（替换本地排序）
const filter = ref({ username: '', classroom: '', department: '', role: '', vip_status: '', face_status: '' })
const sortField = ref('')
const sortDir = ref('asc')
// 多选
const selectedIds = ref([])
const allChecked = computed(()=> students.value.length>0 && students.value.every(u=> selectedIds.value.includes(u.user_id)))
function toggleAll(){
  if (allChecked.value) selectedIds.value=[]; else selectedIds.value=students.value.map(u=>u.user_id)
}
function toggleOne(id){
  const idx = selectedIds.value.indexOf(id)
  if (idx>=0) selectedIds.value.splice(idx,1); else selectedIds.value.push(id)
}

function applyQueryParams(){
  const q = route.query || {}
  ;['username','classroom','department','role','vip_status','face_status'].forEach(k=>{ if(q[k]) filter.value[k]=String(q[k]) })
  if(q.sort_field) sortField.value = String(q.sort_field)
  if(q.sort_dir) sortDir.value = String(q.sort_dir)
}
function pushQuery(){
  const q = { ...filter.value }
  if (sortField.value) { q.sort_field = sortField.value; q.sort_dir = sortDir.value }
  q.page = page.value
  router.replace({ query: q })
}

function toggleSort(field){
  if (sortField.value === field) sortDir.value = (sortDir.value==='asc'?'desc':'asc')
  else { sortField.value = field; sortDir.value='asc' }
  page.value = 1
  fetchList()
}

function onlyVip(){ filter.value.role='VIP'; page.value=1; fetchList() }

async function batchDegradeVip(){
  if (!isAdmin.value) { alert('无权限'); return }
  if (!selectedIds.value.length){ alert('请先勾选用户'); return }
  const vipIds = students.value.filter(u=> selectedIds.value.includes(u.user_id) && u.role==='VIP').map(u=>u.user_id)
  if(!vipIds.length){ alert('所选中没有 VIP 用户'); return }
  if(!confirm(`确定将 ${vipIds.length} 个 VIP 降级为学生？`)) return
  try{
    const { data } = await apiManageStudentsBatchDegradeVip(vipIds)
    if(data?.success){ alert(`已降级 ${data.changed} 个 VIP`); selectedIds.value=[]; fetchList() } else { alert(data?.error_msg||'降级失败') }
  }catch{ alert('网络错误，降级失败') }
}

// 覆盖 fetchList 使用服务端排序
async function fetchList(){
  loading.value=true; errorMsg.value=''
  try{
    const params = { ...filter.value, page: page.value, page_size: pageSize.value }
    if (sortField.value) { params.sort_field = sortField.value; params.sort_dir = sortDir.value }
    const { data } = await apiManageStudentList(params)
    if(data?.success){
      students.value = data.students||[];
      total.value = data.total||0;
      const serverRoles = Array.isArray(data.roles) ? data.roles : []
      const base = ['学生','VIP','老师','管理员']
      roles.value = Array.from(new Set([...serverRoles, ...base]))
    } else { students.value=[]; errorMsg.value = data?.error_msg||'加载失败' }
    pushQuery()
  }catch{ students.value=[]; errorMsg.value='网络错误' } finally { loading.value=false }
}

function onSearch(){ page.value=1; fetchList() }
function resetFilters(){ filter.value={ username:'', classroom:'', department:'', role:'', vip_status:'', face_status:'' }; sortField.value=''; sortDir.value='asc'; page.value=1; fetchList() }
function prevPage() { if (page.value > 1) { page.value--; fetchList() } }
function nextPage() { if (page.value * pageSize.value < total.value) { page.value++; fetchList() } }

function validateForm() {
  const f = form.value
  if (!f.username || f.username.length < 3) return '用户名长度至少为3个字符'
  if (!isEdit.value && (!f.password || f.password.length < 6)) return '密码长度至少为6个字符'
  if (f.password && f.password.length < 6) return '密码长度至少为6个字符'
  if (!['学生', 'VIP', '老师', '管理员'].includes(f.role)) return '角色不合法'
  if (f.role === '老师' && !f.department) return '请选择或填写部门'
  if ((f.role === '学生' || f.role === 'VIP') && !f.classroom) return '请选择或填写班级'
  return ''
}

async function onSave() {
  if (!isAdmin.value) { alert('无权限，仅管理员可操作'); return }
  const msg = validateForm()
  if (msg) { alert(msg); return }
  try {
    const payload = { ...form.value }
    if (!payload.password) delete payload.password
    const { data } = await apiManageStudentSave(payload)
    if (data?.success) { closeModal(); fetchList() }
    else alert(data?.error_msg || '保存失败')
  } catch { alert('网络错误，保存失败') }
}

async function onDelete(id) {
  if (!isAdmin.value) { alert('无权限，仅管理员可操作'); return }
  if (!confirm('确定删除该用户吗？')) return
  try {
    const { data } = await apiManageStudentDelete(id)
    if (data?.success) fetchList()
    else alert(data?.error_msg || '删除失败')
  } catch { alert('网络错误，删除失败') }
}

async function onResetFace(u) {
  if (!isAdmin.value) { alert('无权限，仅管理员可操作'); return }
  if (!u?.user_id) return
  if (!confirm(`确定重置用户 ${u.username} 的人脸信息吗？重置后需重新录入。`)) return
  try {
    const { data } = await apiManageFaceReset({ user_id: u.user_id })
    if (data?.success) {
      alert(data?.message || '人脸信息已重置')
      fetchList()
    } else {
      alert(data?.error_msg || '重置失败')
    }
  } catch {
    alert('网络错误，重置失败')
  }
}

// 徽章样式函数
function badgeClass(state, type='vip') {
  const base = 'px-2 py-0.5 rounded-full text-[11px] border'
  if (type === 'face') {
    switch(state){
      case 'valid': return base + ' bg-emerald-50 text-emerald-700 border-emerald-200'
      case 'expiring': return base + ' bg-amber-50 text-amber-700 border-amber-200'
      case 'expired': return base + ' bg-red-50 text-red-600 border-red-200'
      case 'missing': return base + ' bg-gray-100 text-gray-600 border-gray-300'
      default: return base + ' bg-gray-100 text-gray-600 border-gray-300'
    }
  } else { // vip
    switch(state){
      case 'valid': return base + ' bg-emerald-50 text-emerald-700 border-emerald-200'
      case 'expiring': return base + ' bg-amber-50 text-amber-700 border-amber-200'
      case 'expired': return base + ' bg-red-50 text-red-600 border-red-200'
      default: return base + ' bg-gray-100 text-gray-600 border-gray-300'
    }
  }
}

function stateLabel(state, type='vip') {
  if (!state) return type==='face' ? '—' : ''
  const map = { valid:'有效', expiring:'即将到期', expired:'已过期', missing:'未提交' }
  return map[state] || state
}

const showModal = ref(false)
const isEdit = ref(false)
const form = ref({ user_id: '', username: '', password: '', role: '学生', department: '', classroom: '' })
const upgrading = ref(false)
function openNew(){
  if(!isAdmin.value){ alert('无权限'); return }
  isEdit.value=false
  form.value={ user_id:'', username:'', password:'', role:'学生', department:'', classroom:'' }
  showModal.value=true
}
function openEdit(row){
  if(!isAdmin.value){ alert('无权限'); return }
  isEdit.value=true
  form.value={ user_id: row.user_id, username: row.username, password:'', role: row.role, department: row.department||'', classroom: row.classroom||'' }
  showModal.value=true
}
function closeModal(){ showModal.value=false }
async function upgradeToVip(u){
  if(!isAdmin.value){ alert('无权限'); return }
  if(u.role==='VIP'){ return }
  if(!confirm(`确定将用户 ${u.username} 升级为 VIP 吗？`)) return
  upgrading.value=true
  try{
    const payload={ user_id: u.user_id, username: u.username, role:'VIP', department: u.department||'', classroom: u.classroom||'' }
    const { data } = await apiManageStudentSave(payload)
    if(data?.success){ fetchList() } else { alert(data?.error_msg||'升级失败') }
  }catch{ alert('网络错误，升级失败') } finally { upgrading.value=false }
}

onMounted(()=>{ applyQueryParams(); fetchList() })
watch(pageSize, () => { page.value = 1; fetchList() })
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">学生管理</h1>
      <div class="flex items-center flex-wrap gap-3">
        <button class="bg-white border text-xs px-3 py-1.5 rounded hover:bg-gray-50" @click="onlyVip">只看VIP</button>
        <button v-if="isAdmin" class="bg-blue-600 text-white px-4 py-2 rounded" @click="openNew"><i class="fas fa-user-plus mr-1"></i>新增用户</button>
        <span v-else class="text-gray-500 text-sm">当前仅可查看学生信息</span>
        <button class="bg-gray-600 text-white px-4 py-2 rounded" @click="$router.push(roleHome)">返回</button>
      </div>
    </div>
    <!-- 批量操作条 -->
    <div v-if="isAdmin && selectedIds.length" class="mb-4 flex items-center gap-4 bg-amber-50 border border-amber-200 text-amber-700 rounded px-4 py-2 text-xs">
      <span>已选 {{ selectedIds.length }} 项</span>
      <button class="px-3 h-7 rounded bg-red-600 text-white" @click="batchDegradeVip">批量降级 VIP</button>
      <button class="px-3 h-7 rounded bg-gray-200 text-gray-700" @click="selectedIds=[]">清空选择</button>
    </div>
    <div class="bg-white rounded shadow p-4 mb-4">
      <div class="grid grid-cols-1 md:grid-cols-7 gap-4">
        <div>
          <label class="block text-gray-600 mb-1">姓名</label>
          <input v-model="filter.username" type="text" class="w-full border rounded px-3 py-2" placeholder="模糊匹配" />
        </div>
        <div>
          <label class="block text-gray-600 mb-1">班级</label>
            <input v-model="filter.classroom" type="text" class="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label class="block text-gray-600 mb-1">部门</label>
          <input v-model="filter.department" type="text" class="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label class="block text-gray-600 mb-1">角色</label>
          <select v-model="filter.role" class="w-full border rounded px-3 py-2">
            <option value="">全部</option>
            <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>
        <div>
          <label class="block text-gray-600 mb-1">VIP状态</label>
          <select v-model="filter.vip_status" class="w-full border rounded px-3 py-2">
            <option value="">全部</option>
            <option value="valid">有效</option>
            <option value="expiring">即将到期</option>
            <option value="expired">已过期</option>
          </select>
        </div>
        <div>
          <label class="block text-gray-600 mb-1">人脸状态</label>
          <select v-model="filter.face_status" class="w-full border rounded px-3 py-2">
            <option value="">全部</option>
            <option value="valid">有效</option>
            <option value="expiring">即将到期</option>
            <option value="expired">已过期</option>
            <option value="missing">未提交</option>
          </select>
        </div>
        <div class="flex items-end gap-2">
          <button class="bg-blue-600 text-white px-4 py-2 rounded" @click="onSearch">查询</button>
          <button class="bg-gray-300 text-gray-700 px-4 py-2 rounded" @click="resetFilters">重置</button>
        </div>
      </div>
    </div>

    <div v-if="errorMsg" class="mb-4 text-red-600">{{ errorMsg }}</div>

    <div class="overflow-x-auto bg-white rounded shadow mt-4">
      <table class="min-w-[1250px] w-full text-sm">
        <thead>
          <tr class="bg-blue-50 text-blue-700 text-left">
            <th class="py-3 px-3 w-10 text-center">
              <input type="checkbox" :checked="allChecked" @change="toggleAll" />
            </th>
            <th class="py-3 px-4">ID</th>
            <th class="py-3 px-4">姓名</th>
            <th class="py-3 px-4">角色</th>
            <th class="py-3 px-4">部门</th>
            <th class="py-3 px-4">班级</th>
            <th class="py-3 px-4 cursor-pointer select-none" @click="toggleSort('vip_days_left')">VIP状态 <span v-if="sortField==='vip_days_left'" class="ml-1">{{ sortDir==='asc'?'▲':'▼' }}</span></th>
            <th class="py-3 px-4 cursor-pointer select-none" @click="toggleSort('face_days_left')">人脸状态 <span v-if="sortField==='face_days_left'" class="ml-1">{{ sortDir==='asc'?'▲':'▼' }}</span></th>
            <th class="py-3 px-4 text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in students" :key="u.user_id" class="border-t hover:bg-gray-50">
            <td class="py-2 px-3 text-center">
              <input type="checkbox" :checked="selectedIds.includes(u.user_id)" @change="toggleOne(u.user_id)" />
            </td>
            <td class="py-2 px-4">{{ u.user_id }}</td>
            <td class="py-2 px-4">{{ u.username }}</td>
            <td class="py-2 px-4">{{ u.role }}</td>
            <td class="py-2 px-4">{{ u.department }}</td>
            <td class="py-2 px-4">{{ u.classroom }}</td>
            <td class="py-2 px-4">
              <div class="flex items-center gap-2">
                <span v-if="u.role==='VIP'" :class="badgeClass(u.vip_status,'vip')">{{ stateLabel(u.vip_status,'vip') }}</span>
                <span v-else class="text-gray-400 text-xs">—</span>
                <span v-if="u.vip_days_left!=null && u.role==='VIP' && u.vip_status!=='expired'" class="text-[11px] text-gray-500">剩余{{ u.vip_days_left }}天</span>
              </div>
            </td>
            <td class="py-2 px-4">
              <div class="flex items-center gap-2">
                <span :class="badgeClass(u.face_status,'face')">{{ stateLabel(u.face_status,'face') }}</span>
                <span v-if="u.face_days_left!=null && u.face_status!=='expired' && u.face_status!=='missing'" class="text-[11px] text-gray-500">剩余{{ u.face_days_left }}天</span>
              </div>
            </td>
            <td class="py-2 px-4 text-center">
              <div class="flex justify-center gap-3 flex-wrap">
                <template v-if="isAdmin">
                  <button class="text-blue-600" @click="openEdit(u)"><i class="fas fa-edit"></i> 编辑</button>
                  <button class="text-red-600" @click="onDelete(u.user_id)"><i class="fas fa-trash"></i> 删除</button>
                  <button class="text-orange-600" @click="onResetFace(u)"><i class="fas fa-face-smile"></i> 重置人脸</button>
                  <button v-if="u.role!=='VIP'" :disabled="upgrading" class="text-emerald-600 disabled:opacity-40" @click="upgradeToVip(u)"><i class="fas fa-level-up-alt"></i> 升级VIP</button>
                </template>
                <template v-else>
                  <span class="text-gray-400">-</span>
                </template>
              </div>
            </td>
          </tr>
          <tr v-if="!students.length && !loading"><td colspan="9" class="py-6 text-center text-gray-400">暂无数据</td></tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between mt-4">
      <div class="text-gray-500">共 {{ total }} 条，每页
        <select v-model.number="pageSize" class="border rounded px-2 py-1">
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
        条
      </div>
      <div class="flex items-center gap-2">
        <button class="px-3 py-1 border rounded" :disabled="page===1" @click="prevPage">上一页</button>
        <span>第 {{ page }} 页</span>
        <button class="px-3 py-1 border rounded" :disabled="page*pageSize>=total" @click="nextPage">下一页</button>
      </div>
    </div>

    <!-- 弹窗表单（仅管理员可见） -->
    <div v-if="showModal && isAdmin" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="bg-white w-full max-w-lg rounded shadow-lg">
        <div class="px-5 py-3 border-b flex items-center justify-between">
          <h3 class="text-lg font-semibold">{{ isEdit ? '编辑用户' : '新增用户' }}</h3>
          <button class="text-gray-500" @click="closeModal"><i class="fas fa-times"></i></button>
        </div>
        <div class="p-5 space-y-4">
          <div>
            <label class="block mb-1">用户名</label>
            <input v-model="form.username" type="text" class="w-full border rounded px-3 py-2" placeholder="至少3个字符" />
          </div>
          <div>
            <label class="block mb-1">密码 <span class="text-gray-400 text-sm">{{ isEdit ? '（留空表示不修改）' : '' }}</span></label>
            <input v-model="form.password" type="password" class="w-full border rounded px-3 py-2" :placeholder="isEdit ? '不修改请留空' : '至少6个字符'" />
          </div>
          <div>
            <label class="block mb-1">角色</label>
            <select v-model="form.role" class="w-full border rounded px-3 py-2">
              <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
          <div v-if="form.role==='老师'">
            <label class="block mb-1">部门</label>
            <input v-model="form.department" type="text" class="w-full border rounded px-3 py-2" placeholder="请输入部门" />
          </div>
          <div v-if="form.role==='学生' || form.role==='VIP'">
            <label class="block mb-1">班级</label>
            <input v-model="form.classroom" type="text" class="w-full border rounded px-3 py-2" placeholder="请输入班级" />
          </div>
        </div>
        <div class="px-5 py-4 border-t flex justify-end gap-2">
          <button class="px-4 py-2 bg-gray-300 text-gray-700 rounded" @click="closeModal">取消</button>
          <button class="px-4 py-2 bg-blue-600 text-white rounded" @click="onSave"><i class="fas fa-save mr-1"></i>保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
