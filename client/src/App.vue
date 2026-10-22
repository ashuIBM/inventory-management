<template>
  <div class="app">
    <header class="top-nav">
      <div class="nav-container">
        <div class="logo">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <nav class="nav-tabs">
          <router-link to="/" :class="{ active: $route.path === '/' }">
            {{ t('nav.overview') }}
          </router-link>
          <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
            {{ t('nav.inventory') }}
          </router-link>
          <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
            {{ t('nav.orders') }}
          </router-link>
          <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
            {{ t('nav.finance') }}
          </router-link>
          <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
            {{ t('nav.demandForecast') }}
          </router-link>
          <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }">
            {{ t('nav.restocking') }}
          </router-link>
          <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
            {{ t('nav.reports') }}
          </router-link>
        </nav>
        <button
          class="theme-toggle"
          type="button"
          :aria-label="isDark ? t('theme.toLight') : t('theme.toDark')"
          :title="isDark ? t('theme.toLight') : t('theme.toDark')"
          @click="toggleTheme"
        >
          <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
          </svg>
        </button>
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </header>
    <FilterBar v-if="showFilterBar" />
    <main class="main-content">
      <router-view />
    </main>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import { useTheme } from './composables/useTheme'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const { isDark, toggleTheme } = useTheme()
    const route = useRoute()

    // Routes are unnamed, so match by path. The Restocking page ignores the
    // global filters (warehouse/category/month/status), so the bar is hidden there.
    const showFilterBar = computed(() => route.path !== '/restocking')
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      isDark,
      toggleTheme,
      showFilterBar,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* Theme tokens: dark navy + orange. Light is the default; [data-theme="dark"]
   is set on <html> by composables/useTheme.js. Status hues (red/green/amber)
   stay literal in components; only their soft backgrounds/text are tokens. */
:root {
  color-scheme: light;
  --navy-900: #0b1b33;
  --navy-800: #10264a;
  --navy-600: #1f3d6b;
  --accent: #f97316;
  --accent-strong: #ea580c;
  --accent-deep: #c2410c;
  --accent-bright: #fdba74;
  --accent-soft: #fff4ea;
  --accent-softer: #fed7aa;
  --on-accent: #ffffff;

  --surface: #ffffff;
  --surface-alt: #f4f6fa;
  --surface-muted: #eaeef5;
  --border: #dde3ed;
  --border-strong: #c3ccdb;
  --text: #0b1b33;
  --text-secondary: #2c3e5c;
  --text-muted: #5b6b85;
  --text-subtle: #8c99ae;
  --primary-bg: #0b1b33;
  --primary-bg-hover: #1f3d6b;

  --nav-bg: #0b1b33;
  --nav-text: #ffffff;
  --nav-text-muted: #a9b8d0;
  --nav-border: #24406b;
  --nav-hover: rgba(255, 255, 255, 0.08);
  --nav-active: rgba(249, 115, 22, 0.22);

  --danger-soft: #fef2f2;
  --danger-border: #fecaca;
  --danger-text: #991b1b;
  --success-soft: #dcfce7;
  --success-border: #bbf7d0;
  --success-text: #166534;
  --warning-soft: #fff7ed;
  --warning-border: #fed7aa;
  --warning-text: #9a3412;
}

:root[data-theme="dark"] {
  color-scheme: dark;
  --accent-soft: rgba(249, 115, 22, 0.14);
  --accent-softer: rgba(249, 115, 22, 0.3);
  --accent-deep: #fdba74;

  --surface: #12223d;
  --surface-alt: #0a1628;
  --surface-muted: #1a2d4d;
  --border: #233a5e;
  --border-strong: #31507d;
  --text: #e8eef8;
  --text-secondary: #c3cfe2;
  --text-muted: #94a6c2;
  --text-subtle: #6f82a2;
  --primary-bg: #f97316;
  --primary-bg-hover: #ea580c;

  --nav-bg: #07101f;
  --nav-border: #1c3152;

  --danger-soft: rgba(239, 68, 68, 0.14);
  --danger-border: rgba(239, 68, 68, 0.35);
  --danger-text: #fca5a5;
  --success-soft: rgba(16, 185, 129, 0.14);
  --success-border: rgba(16, 185, 129, 0.35);
  --success-text: #6ee7b7;
  --warning-soft: rgba(245, 158, 11, 0.14);
  --warning-border: rgba(245, 158, 11, 0.35);
  --warning-text: #fcd34d;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--surface-alt);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-nav {
  background: var(--nav-bg);
  border-bottom: 3px solid var(--accent);
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  padding: 0 2rem;
  height: 70px;
}

.nav-container > .nav-tabs {
  margin-left: auto;
  margin-right: 1rem;
}

.theme-toggle {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  margin-right: 0.75rem;
  border: 1px solid var(--nav-border);
  border-radius: 8px;
  background: transparent;
  color: var(--nav-text);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.theme-toggle:hover {
  background: var(--nav-hover);
  border-color: var(--accent);
}

.theme-toggle svg {
  width: 18px;
  height: 18px;
}

.nav-container > .language-switcher {
  margin-right: 1rem;
}

.logo {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.logo h1 {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--nav-text);
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.813rem;
  color: var(--nav-text-muted);
  font-weight: 400;
  padding-left: 0.75rem;
  border-left: 1px solid var(--nav-border);
}

.nav-tabs {
  display: flex;
  gap: 0.25rem;
}

.nav-tabs a {
  padding: 0.625rem 1.25rem;
  color: var(--nav-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  position: relative;
}

.nav-tabs a:hover {
  color: var(--nav-text);
  background: var(--nav-hover);
}

.nav-tabs a.active {
  color: var(--nav-text);
  background: var(--nav-active);
}

.nav-tabs a.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent);
}

.main-content {
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-muted);
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--surface);
  padding: 1.25rem;
  border-radius: 10px;
  border: 1px solid var(--border);
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: #ea580c;
}

.stat-card.success .stat-value {
  color: #059669;
}

.stat-card.danger .stat-value {
  color: #dc2626;
}

.stat-card.info .stat-value {
  color: var(--accent-strong);
}

.card {
  background: var(--surface);
  border-radius: 10px;
  padding: 1.25rem;
  border: 1px solid var(--border);
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--surface-alt);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--surface-alt);
}

.badge {
  display: inline-block;
  padding: 0.313rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--success-soft);
  color: var(--success-text);
}

.badge.warning {
  background: var(--warning-soft);
  color: var(--warning-text);
}

.badge.danger {
  background: var(--danger-soft);
  color: var(--danger-text);
}

.badge.info {
  background: var(--accent-soft);
  color: var(--accent-deep);
}

.badge.increasing {
  background: var(--success-soft);
  color: var(--success-text);
}

.badge.decreasing {
  background: var(--danger-soft);
  color: var(--danger-text);
}

.badge.stable {
  background: var(--accent-soft);
  color: var(--accent-deep);
}

.badge.high {
  background: var(--danger-soft);
  color: var(--danger-text);
}

.badge.medium {
  background: var(--warning-soft);
  color: var(--warning-text);
}

.badge.low {
  background: var(--accent-soft);
  color: var(--accent-deep);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
  font-size: 0.938rem;
}

.error {
  background: var(--danger-soft);
  border: 1px solid var(--danger-border);
  color: var(--danger-text);
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
