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
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" :class="{ 'sidebar-nav-spread': item.label.length === 3 }">
          {{ item.label }}
        </RouterLink>
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
import { ElNotification } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { api } from './api/client'
import { useAuthStore } from './stores/auth'
import logoWhite from './assets/jiezhi-logo-square-white.png'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const now = ref(new Date())
const authReady = ref(false)
let clockTimer: number | undefined
let designAlertTimer: number | undefined
let designAlertLoading = false
let designAlertInitialized = false
const knownPendingDesignTaskIds = new Set<string>()

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
      'system_settings.change_invoicetypeoption',
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
const canReceiveDesignAlerts = computed(() => auth.hasPermission('design.view_designtask'))
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
  clockTimer = window.setInterval(() => {
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

watch(
  () => [auth.user?.id, canReceiveDesignAlerts.value] as const,
  () => {
    if (auth.user && canReceiveDesignAlerts.value) {
      startDesignAlerts()
      return
    }
    stopDesignAlerts()
  },
  { immediate: true }
)

onUnmounted(() => {
  if (clockTimer) window.clearInterval(clockTimer)
  stopDesignAlerts()
})

async function handleLogout() {
  stopDesignAlerts()
  await auth.logout()
  router.push('/login')
}

function startDesignAlerts() {
  if (designAlertTimer) return
  checkNewDesignTasks()
  designAlertTimer = window.setInterval(checkNewDesignTasks, 1000 * 30)
}

function stopDesignAlerts() {
  if (designAlertTimer) {
    window.clearInterval(designAlertTimer)
    designAlertTimer = undefined
  }
  designAlertLoading = false
  designAlertInitialized = false
  knownPendingDesignTaskIds.clear()
}

async function checkNewDesignTasks() {
  if (!auth.user || !canReceiveDesignAlerts.value || designAlertLoading) return
  designAlertLoading = true
  try {
    const response = await api.get('/design-tasks', {
      params: { status: 'pending', page_size: 20 }
    })
    const tasks = response.data.results || []
    const incomingIds = new Set<string>(tasks.map((task: any) => task.id))
    const newTasks = tasks.filter((task: any) => !knownPendingDesignTaskIds.has(task.id))

    knownPendingDesignTaskIds.clear()
    for (const id of incomingIds) knownPendingDesignTaskIds.add(id)

    if (!designAlertInitialized) {
      designAlertInitialized = true
      return
    }

    if (newTasks.length) {
      notifyNewDesignTasks(newTasks)
    }
  } catch {
    // 提醒功能不能影响主流程，接口异常时下一轮轮询再恢复。
  } finally {
    designAlertLoading = false
  }
}

function notifyNewDesignTasks(tasks: any[]) {
  playDesignAlertSound()
  const firstTask = tasks[0]
  const orderNo = firstTask?.order?.order_no || '新订单'
  const customerName = firstTask?.order?.customer?.name || '客户'
  ElNotification({
    title: '新待设计订单',
    message: tasks.length === 1 ? `${orderNo} / ${customerName}` : `新增 ${tasks.length} 个待设计任务`,
    type: 'info',
    duration: 6000,
    onClick: () => router.push('/design-tasks')
  })
}

function playDesignAlertSound() {
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
    if (!AudioContextClass) return
    const audioContext = new AudioContextClass()
    const oscillator = audioContext.createOscillator()
    const gain = audioContext.createGain()
    oscillator.type = 'sine'
    oscillator.frequency.setValueAtTime(880, audioContext.currentTime)
    gain.gain.setValueAtTime(0.001, audioContext.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.12, audioContext.currentTime + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.35)
    oscillator.connect(gain)
    gain.connect(audioContext.destination)
    oscillator.start()
    oscillator.stop(audioContext.currentTime + 0.38)
  } catch {
    // 部分浏览器会限制非用户手势触发的声音，网页通知仍会正常显示。
  }
}
</script>
