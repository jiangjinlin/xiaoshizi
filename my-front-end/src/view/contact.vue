<template>
  <div class="min-h-screen flex flex-col bg-gray-50 font-sans">
    <header class="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button class="rounded-button bg-white border px-3 py-1.5 text-sm" @click="$router.push('/')">← 返回首页</button>
          <h1 class="text-lg md:text-xl font-semibold text-gray-800">联系我们</h1>
        </div>
        <button class="rounded-button bg-primary text-white px-4 py-2 text-sm" @click="$router.push('/login')">登录系统</button>
      </div>
    </header>

    <main class="flex-1">
      <section class="py-8 md:py-12">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 grid gap-6 lg:grid-cols-3">
          <!-- 联系方式卡片 -->
          <div class="space-y-4">
            <div class="rounded-2xl bg-white border border-gray-100 p-5 shadow-sm">
              <div class="flex items-center gap-2 text-gray-500 text-sm mb-2"><i class="fas fa-phone text-primary"></i>电话</div>
              <div class="flex items-center justify-between">
                <a class="text-lg font-semibold text-gray-900" :href="'tel:' + phone">{{ phone }}</a>
                <button class="text-xs text-primary hover:underline" @click="copy(phone)">复制</button>
              </div>
            </div>
            <div class="rounded-2xl bg-white border border-gray-100 p-5 shadow-sm">
              <div class="flex items-center gap-2 text-gray-500 text-sm mb-2"><i class="fas fa-envelope text-primary"></i>邮箱</div>
              <div class="flex items-center justify-between">
                <a class="text-lg font-semibold text-gray-900" :href="'mailto:' + email">{{ email }}</a>
                <button class="text-xs text-primary hover:underline" @click="copy(email)">复制</button>
              </div>
            </div>
            <div class="rounded-2xl bg-white border border-gray-100 p-5 shadow-sm">
              <div class="flex items-center gap-2 text-gray-500 text-sm mb-2"><i class="fas fa-location-dot text-primary"></i>地址</div>
              <div class="text-lg font-semibold text-gray-900">{{ address }}</div>
              <div class="mt-2 text-xs text-gray-500">
                <a class="text-primary hover:underline" :href="mapLink" target="_blank" rel="noopener">在地图中查看</a>
              </div>
            </div>
            <div class="rounded-2xl bg-white border border-gray-100 p-5 shadow-sm">
              <div class="flex items-center gap-2 text-gray-500 text-sm mb-2"><i class="fab fa-weixin text-primary"></i>微信</div>
              <div class="flex items-center gap-3">
                <img :src="wechatQR" alt="微信二维码" class="w-40 h-40 object-contain rounded border border-gray-100 bg-white" @error="onQrError"/>
                <div class="text-xs text-gray-500 leading-relaxed">
                  <div>微信扫码添加咨询（工作日 9:00-18:00）（请备注来意）</div>
                  <div v-if="qrMissing" class="mt-1 text-amber-600">提示：请将二维码图片放到 my-front-end/public/wechat-qr.png</div>
                  <div class="mt-2 flex gap-2">
                    <button class="px-3 py-1.5 rounded border text-gray-700" @click="downloadQR">下载二维码</button>
                    <button class="px-3 py-1.5 rounded border text-gray-700" @click="copy(email)">复制邮箱</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 表单 -->
          <div class="lg:col-span-2 rounded-2xl bg-white border border-gray-100 p-5 md:p-6 shadow-sm">
            <div class="text-base md:text-lg font-semibold text-gray-900 mb-4">在线留言</div>
            <div class="grid md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs text-gray-500 mb-1">姓名</label>
                <input v-model.trim="form.name" class="w-full h-10 px-3 rounded border border-gray-300 bg-white" placeholder="请输入您的姓名"/>
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">邮箱</label>
                <input v-model.trim="form.email" class="w-full h-10 px-3 rounded border border-gray-300 bg-white" placeholder="用于接收回复（可选）"/>
              </div>
              <div class="md:col-span-2">
                <label class="block text-xs text-gray-500 mb-1">主题</label>
                <input v-model.trim="form.subject" class="w-full h-10 px-3 rounded border border-gray-300 bg-white" placeholder="例如：产品咨询 / 技术支持 / 合作洽谈"/>
              </div>
              <div class="md:col-span-2">
                <label class="block text-xs text-gray-500 mb-1">留言内容</label>
                <textarea v-model.trim="form.message" rows="6" class="w-full px-3 py-2 rounded border border-gray-300 bg-white" placeholder="请描述您的需求或问题，我们会尽快回复您"></textarea>
              </div>
            </div>
            <div class="mt-4 flex items-center gap-2">
              <button class="h-10 px-4 rounded bg-primary text-white" :disabled="!canSend" @click="sendMail">发送邮件</button>
              <button class="h-10 px-4 rounded border" :disabled="!canSend" @click="copy(composeMailBody())">复制到剪贴板</button>
              <span v-if="tip" :class="tipOk ? 'text-emerald-600' : 'text-red-600'" class="text-xs">{{ tip }}</span>
            </div>
            <div class="mt-3 text-[11px] text-gray-500">说明：点击“发送邮件”将打开系统默认邮件客户端并自动填充标题与内容；若未安装邮件客户端，请使用“复制到剪贴板”后粘贴发送至 {{ email }}。</div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const phone = '暂时未开放'
const email = '2300035250@qq.com'
const address = '海科路皇家女子学院'
const mapLink = 'https://uri.amap.com/search?keyword=' + encodeURIComponent(address)
const wechatQR = '/wechat-qr.png'

const form = reactive({ name: '', email: '', subject: '', message: '' })
const canSend = computed(() => !!(form.subject && form.message))
const tip = ref('')
const tipOk = ref(false)
const qrMissing = ref(false)
const tipTimer = ref(0)

function onQrError(){ qrMissing.value = true }

function showTip(msg, ok=true){
  tipOk.value = !!ok
  tip.value = msg
  if (tipTimer.value) { clearTimeout(tipTimer.value) }
  tipTimer.value = setTimeout(()=>{ tip.value=''; tipTimer.value=0 }, 3000)
}

function normalizeCRLF(str){
  // 将 \n 规范为 CRLF，兼容更多邮件客户端
  return str.replace(/\r?\n/g, '\r\n')
}

function composeMailBody(){
  let lines = []
  if (form.name) lines.push(`姓名：${form.name}`)
  if (form.email) lines.push(`联系邮箱：${form.email}`)
  lines.push('')
  lines.push('留言内容：')
  lines.push(form.message || '')
  return lines.join('\n')
}

function sendMail(){
  if (!canSend.value) { showTip('请先填写主题与留言内容', false); return }
  try{
    const subject = encodeURIComponent(form.subject)
    const bodyRaw = normalizeCRLF(composeMailBody())
    // 一些客户端更偏好 %0D%0A，先做 CRLF 规范化再编码
    const body = encodeURIComponent(bodyRaw)
    const href = `mailto:${email}?subject=${subject}&body=${body}`
    // 使用 a 标签触发，兼容部分浏览器对 window.location 的拦截
    const a = document.createElement('a')
    a.href = href
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    a.remove()
    showTip('已尝试打开邮件客户端', true)
  }catch(e){ showTip('打开邮件客户端失败', false) }
}

async function copy(text){
  const content = String(text || composeMailBody())
  // 先尝试现代 API
  try{
    if (navigator.clipboard && navigator.clipboard.writeText){
      await navigator.clipboard.writeText(content)
      showTip('已复制到剪贴板', true)
      return
    }
  }catch{ /* 降级 */ }
  // 降级方案：隐藏 textarea + execCommand
  try{
    const ta = document.createElement('textarea')
    ta.value = content
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    ta.style.left = '-9999px'
    document.body.appendChild(ta)
    ta.select()
    ta.setSelectionRange(0, ta.value.length)
    const ok = document.execCommand && document.execCommand('copy')
    document.body.removeChild(ta)
    if (ok) { showTip('已复制到剪贴板', true) } else { throw new Error('execCommand copy failed') }
  }catch{
    showTip('复制失败，请手动选择复制', false)
  }
}

function downloadQR(){
  try{
    const a = document.createElement('a')
    a.href = wechatQR
    a.download = 'wechat-qr.png'
    document.body.appendChild(a)
    a.click()
    a.remove()
  }catch{}
}
</script>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
/* use global .text-primary/.bg-primary/.rounded-button from tokens.css */
</style>
