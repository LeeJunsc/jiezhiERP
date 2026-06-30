<template>
  <router-view v-if="isLoginPage" />
  <div v-else-if="authReady && auth.user" class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <img class="brand-logo" :src="logoWhite" alt="介知包装" />
        <small class="brand-time">{{ currentMinute }}</small>
      </div>
      <RouterLink v-if="canCreateOrder" class="sidebar-primary-action" to="/orders/new">新建订单</RouterLink>
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
  <div v-else class="app-loading">加载中...</div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import logoWhite from './assets/jiezhi-logo-square-white.png'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const now = ref(new Date())
const authReady = ref(false)
let timer: number | undefined

const allNavItems = [
  { path: '/', label: '工作台' },
  { path: '/orders', label: '订单列表', permissions: ['orders.view_order'] },
  { path: '/design-tasks', label: '设计任务', permissions: ['design.view_designtask'] },
  { path: '/production-arrangements', label: '生产安排', permissions: ['production.view_productionarrangement'] },
  { path: '/invoice-requests', label: '发票审批', permissions: ['finance.view_invoicerequest'] },
  { path: '/after-sales-requests', label: '售后处理', permissions: ['after_sales.view_aftersalesrequest'] },
  { path: '/customers', label: '客户管理', permissions: ['customers.view_customer'] },
  {
    path: '/system',
    label: '系统管理',
    permissions: [
      'stores.change_store',
      'orders.change_designoption',
      'system_settings.change_paymentchannel',
      'auth.view_user',
      'auth.view_group'
    ]
  }
]
const routeTitles: Record<string, string> = {
  '/orders/new': '新建订单'
}

const isLoginPage = computed(() => route.path === '/login')
const navItems = computed(() => allNavItems.filter((item) => !item.permissions || auth.hasAnyPermission(item.permissions)))
const canCreateOrder = computed(() => auth.hasPermission('orders.add_order'))
const currentTitle = computed(() => routeTitles[route.path] || allNavItems.find((item) => item.path === route.path)?.label || '订单详情')
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
})

watch(
  () => route.path,
  async () => {
    if (isLoginPage.value) {
      authReady.value = true
      return
    }
    authReady.value = false
    if (!auth.user) {
      await auth.loadMe()
    }
    if (!auth.user) {
      await router.push('/login')
      return
    }
    authReady.value = true
  },
  { immediate: true }
)

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>
