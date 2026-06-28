<template>
  <router-view v-if="isLoginPage" />
  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <img class="brand-logo" :src="logoWhite" alt="介知包装" />
        <small class="brand-time">{{ currentMinute }}</small>
      </div>
      <nav>
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path">{{ item.label }}</RouterLink>
      </nav>
    </aside>
    <main class="main">
      <header class="topbar">
        <div>
          <p>第一轮开发版</p>
          <h1>{{ currentTitle }}</h1>
        </div>
        <div class="user-box">
          <span>{{ auth.user?.first_name || auth.user?.username || '未登录' }}</span>
          <el-button size="small" @click="handleLogout">退出</el-button>
        </div>
      </header>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import logoWhite from './assets/jiezhi-logo-square-white.png'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const now = ref(new Date())
let timer: number | undefined

const navItems = [
  { path: '/', label: '工作台' },
  { path: '/kanban', label: '看板' },
  { path: '/orders', label: '订单列表' },
  { path: '/orders/new', label: '新建订单' },
  { path: '/design-tasks', label: '设计任务' },
  { path: '/production-arrangements', label: '生产安排' },
  { path: '/customers', label: '客户管理' },
  { path: '/system', label: '系统管理' }
]

const isLoginPage = computed(() => route.path === '/login')
const currentTitle = computed(() => navItems.find((item) => item.path === route.path)?.label || '订单详情')
const currentMinute = computed(() => {
  const date = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(now.value)
  return date.replace(/\//g, '-')
})

onMounted(async () => {
  timer = window.setInterval(() => {
    now.value = new Date()
  }, 1000 * 30)
  if (!isLoginPage.value) {
    await auth.loadMe()
    if (!auth.user) router.push('/login')
  }
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>
