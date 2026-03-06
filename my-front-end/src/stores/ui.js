import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', {
  state: () => ({
    theme: (typeof localStorage !== 'undefined' && localStorage.getItem('theme')) || 'light'
  }),
  actions: {
    setTheme(t) {
      this.theme = t
      try { localStorage.setItem('theme', t) } catch(e) {}
      if (typeof document !== 'undefined') {
        document.documentElement.dataset.theme = t
      }
    },
    toggleTheme() { this.setTheme(this.theme === 'light' ? 'dark' : 'light') },
    initTheme() {
      // Always ensure [data-theme] is set; prefer stored value, fallback to system, else current state
      let t = null
      try { t = localStorage.getItem('theme') } catch(e) { t = null }
      if (!t && typeof window !== 'undefined') {
        try {
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
          t = prefersDark ? 'dark' : 'light'
        } catch { t = null }
      }
      this.setTheme(t || this.theme || 'light')
    }
  }
})
