import { defineStore } from 'pinia'
import { apiProfileInfo } from '../api/index'

function bustUrl(url, seed) {
  if (!url) return ''
  try {
    const u = new URL(url)
    if (seed) {
      u.searchParams.set('t', String(seed))
    } else if (!u.searchParams.has('t')) {
      u.searchParams.set('t', String(Date.now()))
    }
    return u.toString()
  } catch {
    const sep = url.includes('?') ? '&' : '?'
    return `${url}${sep}t=${seed || Date.now()}`
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    userId: null,
    username: '',
    role: '',
    avatarUrl: '',
    profileLoaded: false,
  }),
  actions: {
    async loadProfile(force = false) {
      if (this.profileLoaded && !force) return
      try {
        const { data } = await apiProfileInfo()
        if (data?.success) {
          const p = data.profile || {}
          this.userId = p.user_id || null
          this.username = p.username || ''
          this.role = p.role || ''
          this.avatarUrl = bustUrl(p.avatar_url)
          this.profileLoaded = true
          return true
        }
      } catch (e) {
        this.clear()
      }
      return false
    },
    setAvatarUrl(url) {
      this.avatarUrl = bustUrl(url, Date.now())
    },
    clear() {
      this.userId = null
      this.username = ''
      this.role = ''
      this.avatarUrl = ''
      this.profileLoaded = false
    }
  }
})
