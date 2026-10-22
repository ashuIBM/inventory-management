import { ref, computed } from 'vue'

const STORAGE_KEY = 'app-theme'

function initialTheme() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'light' || saved === 'dark') return saved
  } catch {
    // Storage can be unavailable (private mode); fall back to the OS setting
  }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

// Shared theme state (singleton pattern, like useFilters / useI18n)
const theme = ref(initialTheme())

function applyTheme(value) {
  document.documentElement.dataset.theme = value
}

export function useTheme() {
  const isDark = computed(() => theme.value === 'dark')

  const setTheme = (value) => {
    theme.value = value
    applyTheme(value)
    try {
      localStorage.setItem(STORAGE_KEY, value)
    } catch {
      // Non-fatal: theme just won't persist across reloads
    }
  }

  const toggleTheme = () => setTheme(isDark.value ? 'light' : 'dark')

  return { theme, isDark, setTheme, toggleTheme }
}

// Called from main.js before mount so the first paint uses the right theme
export function initTheme() {
  applyTheme(theme.value)
}
