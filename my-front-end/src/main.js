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

// 自动登出：仅在最后一个标签真实关闭时再请求后端登出，避免刷新页面误触发退出
;(function setupAutoLogoutOnClose(){
  const TAB_KEY = 'open_tabs'
  const tabId = Math.random().toString(36).slice(2)
  let logoutSent = false
  let reloadLikely = false

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
    if (logoutSent || reloadLikely) return
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

  addTab()

  function markReloadLikely(){
    reloadLikely = true
    try { sessionStorage.setItem('page_reload_in_progress', '1') } catch {}
  }

  function clearReloadFlagSoon(){
    window.setTimeout(() => {
      reloadLikely = false
      try { sessionStorage.removeItem('page_reload_in_progress') } catch {}
    }, 1500)
  }

  function handleCloseAttempt(){
    try {
      const remain = removeTab()
      if (remain === 0) sendLogout()
    } catch {}
  }

  window.addEventListener('keydown', (e) => {
    const key = String(e.key || '').toLowerCase()
    if (key === 'f5' || ((e.ctrlKey || e.metaKey) && key === 'r')) markReloadLikely()
  })
  window.addEventListener('beforeunload', () => {
    markReloadLikely()
    window.setTimeout(() => {
      if (!reloadLikely) return
      addTab()
    }, 0)
  })
  window.addEventListener('pagehide', (e) => {
    if (e.persisted || reloadLikely) return
    handleCloseAttempt()
  })

  // 首屏恢复时，若是刷新，补回当前标签记录
  try {
    if (sessionStorage.getItem('page_reload_in_progress') === '1') {
      addTab()
      clearReloadFlagSoon()
    }
  } catch {}

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
