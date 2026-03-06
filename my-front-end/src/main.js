import { createApp } from 'vue'
import './style.css'
import './styles/tokens.css'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import { useUiStore } from './stores/ui'
import { getLanConfig } from './api/http'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
// init theme (system preference if no stored value)
useUiStore().initTheme()
app.use(router)
app.mount('#app')

// 自动登出：页面/标签关闭时，如果这是最后一个标签，则调用后端 /api/logout
;(function setupAutoLogoutOnClose(){
  const TAB_KEY = 'open_tabs'
  const tabId = Math.random().toString(36).slice(2)
  let logoutSent = false

  function readTabs(){
    try { return JSON.parse(localStorage.getItem(TAB_KEY) || '[]') } catch { return [] }
  }
  function writeTabs(list){
    try { localStorage.setItem(TAB_KEY, JSON.stringify(list)) } catch {}
  }
  function addTab(){
    const list = readTabs()
    if (!list.includes(tabId)) { list.push(tabId); writeTabs(list) }
  }
  function removeTab(){
    const list = readTabs().filter(id => id !== tabId)
    writeTabs(list)
    return list.length
  }
  function apiBase(){
    try { return (getLanConfig().baseURL || '').replace(/\/$/, '') } catch { return '' }
  }
  function sendLogout(){
    if (logoutSent) return
    logoutSent = true
    const url = apiBase() + '/api/logout'
    try {
      const payload = new Blob([JSON.stringify({})], { type: 'application/json' })
      if (navigator.sendBeacon && url) {
        navigator.sendBeacon(url, payload)
        return
      }
    } catch {}
    try {
      if (url) {
        fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', keepalive: true, body: '{}' })
      }
    } catch {}
  }

  // 注册本标签页
  addTab()

  // 在可见性切换为隐藏或页面卸载时尝试登出（若仅剩当前标签）
  function handleCloseAttempt(){
    try {
      const remain = removeTab()
      if (remain === 0) sendLogout()
    } catch {}
  }
  window.addEventListener('pagehide', handleCloseAttempt)
  window.addEventListener('beforeunload', handleCloseAttempt)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') handleCloseAttempt()
  })

  // 兼容：其他标签变动时，清理已不存在的重复项
  window.addEventListener('storage', (e) => {
    if (e.key === TAB_KEY && e.newValue) {
      try {
        const uniq = Array.from(new Set(JSON.parse(e.newValue)))
        writeTabs(uniq)
      } catch {}
    }
  })
})()
