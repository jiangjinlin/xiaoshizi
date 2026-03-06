import axios from 'axios'

// 生产环境优先使用同域根路径，便于 Nginx/IIS 反向代理；开发环境保留局域网直连逻辑
function isProdEnv() {
  try {
    return Boolean(typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.PROD)
  } catch {
    return false
  }
}

function joinUrl(base, path = '') {
  const cleanBase = (base || '').replace(/\/$/, '')
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${cleanBase}${cleanPath}`
}

function computeDefaultBase() {
  if (isProdEnv()) return ''
  try {
    if (typeof window !== 'undefined' && window.location) {
      const { protocol, hostname } = window.location
      const proto = /^https:/i.test(protocol) ? 'https' : 'http'
      return `${proto}://${hostname}:8000`
    }
  } catch {}
  return 'http://localhost:8000'
}
const DEFAULT_BASE = computeDefaultBase()

function readAddrEnabled() {
  try { return (localStorage.getItem('addr_enabled') || '0') === '1' } catch { return false }
}
export function setAddrEnabled(enabled) {
  try { localStorage.setItem('addr_enabled', enabled ? '1' : '0') } catch {}
  // 切换后端 baseURL 以即时生效
  http.defaults.baseURL = buildBaseURL()
}

function readLanSettings() {
  try {
    const host = (localStorage.getItem('lan_host') || '').trim()
    return { host }
  } catch {
    return { host: '' }
  }
}
function buildBaseURL() {
  const master = readAddrEnabled()
  const { host } = readLanSettings()
  if (!master) return DEFAULT_BASE
  if (!host) return DEFAULT_BASE
  let url = host
  try {
    if (!/^https?:\/\//i.test(url)) {
      // 未显式协议：补 http://，若无端口则默认 8000
      if (/^\[[0-9a-fA-F:]+](:\d+)?$/.test(url)) {
        // IPv6 形式 [::1]:8000 或 [::1]
        if (!/:\d+]$/.test(url)) url = `${url}:8000`
        url = `http://${url}`
      } else if (/^\d+\.\d+\.\d+\.\d+(?::\d+)?$/.test(url) || /^[a-zA-Z0-9_.-]+(?::\d+)?$/.test(url)) {
        // IPv4 或域名，可带端口
        if (!/:\d+$/.test(url)) url = `${url}:8000`
        url = `http://${url}`
      } else {
        // 兜底
        url = `http://${url}:8000`
      }
    }
  } catch {
    url = DEFAULT_BASE
  }
  return url.replace(/\/$/, '')
}

export const http = axios.create({
  baseURL: buildBaseURL(),
  withCredentials: true,
  timeout: 20000
})

export function setLanEnabled(enabled) {
  // 保留兼容，但实际以 addr_enabled 为准
  setAddrEnabled(!!enabled)
}
export function setLanHost(host) {
  try { localStorage.setItem('lan_host', host || '') } catch {}
  http.defaults.baseURL = buildBaseURL()
}
export function getLanConfig() {
  const cfg = readLanSettings()
  return { enabled: readAddrEnabled(), host: cfg.host, baseURL: buildBaseURL() }
}
export function getDefaultBaseURL() {
  return DEFAULT_BASE
}
export function getStaticURL(path = '/static/logo.png') {
  return joinUrl(buildBaseURL(), path)
}

// 请求拦截：GET 防缓存 & 统一 headers
http.interceptors.request.use(cfg => {
  try {
    cfg.headers = cfg.headers || {}
    cfg.headers['X-Requested-With'] = 'XMLHttpRequest'
    if (cfg.method === 'get') {
      const p = cfg.params || {}
      // 避免影响分页 / 查询，使用较短 key
      p._ts = Date.now()
      cfg.params = p
    }
  } catch {}
  return cfg
})

// 响应拦截：基础错误语义化 + 人脸403跳转 + 401 全局处理
http.interceptors.response.use(
  resp => resp,
  err => {
    if (err.response) {
      const { status, data } = err.response
      const emsg = data?.error_msg || ''
      if (status === 403 && (emsg.includes('人脸') || emsg.includes('需先进行人脸验证'))) {
        try {
          const hash = typeof window !== 'undefined' ? (window.location.hash || '#/') : '#/'
          const current = hash.startsWith('#') ? hash.substring(1) : hash
          const target = `#/signin?redirect=${encodeURIComponent(current)}`
          if (typeof window !== 'undefined') window.location.hash = target
        } catch {}
      }
      if (status === 401) {
        try {
          localStorage.removeItem('user_id')
          localStorage.removeItem('role')
          const hash = typeof window !== 'undefined' ? (window.location.hash || '#/') : '#/'
          const current = hash.startsWith('#') ? hash.substring(1) : hash
          const target = `#/login?redirect=${encodeURIComponent(current)}`
          if (typeof window !== 'undefined') window.location.hash = target
        } catch {}
      }
      err._friendly = emsg || (status === 401 ? '未登录或登录已过期' : (status === 403 ? '没有权限' : '请求失败'))
    } else if (err.request) {
      err._friendly = '无法连接服务器'
    } else {
      err._friendly = '请求被中断'
    }
    return Promise.reject(err)
  }
)
