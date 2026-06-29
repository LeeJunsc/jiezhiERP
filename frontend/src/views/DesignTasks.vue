<template>
  <section class="panel">
    <div class="panel-head">
      <div class="panel-title">
        <h2>设计任务</h2>
        <small>待处理订单 {{ pendingCount }} 单</small>
      </div>
      <div class="actions">
        <el-button @click="load">刷新</el-button>
        <el-button-group>
          <el-button :type="viewMode === 'pending' ? 'primary' : 'default'" @click="switchViewMode('pending')">待处理</el-button>
          <el-button :type="viewMode === 'recent' ? 'primary' : 'default'" @click="switchViewMode('recent')">最近完成</el-button>
        </el-button-group>
      </div>
    </div>
    <el-table :data="rows" border>
      <el-table-column prop="task_no" label="任务号" width="160" />
      <el-table-column prop="order.order_no" label="订单号" width="160" />
      <el-table-column prop="order.customer.name" label="客户" />
      <el-table-column label="任务状态" width="120">
        <template #default="{ row }">{{ taskStatusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column prop="order.status" label="订单状态" width="140">
        <template #default="{ row }">{{ orderStatusLabel(row.order.status) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="claim(row.id)" :disabled="row.status !== 'pending'">领取</el-button>
          <el-button size="small" type="primary" @click="openDesignDetail(row)" :disabled="row.status === 'confirmed'">确认设计</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>

  <el-drawer v-model="detailVisible" size="min(780px, 100vw)" :with-header="false" destroy-on-close>
    <section v-if="currentOrder && currentTask" class="order-detail-drawer">
      <div class="drawer-head">
        <div>
          <span class="status-pill">{{ orderStatusLabel(currentOrder.status) }}</span>
          <h2>{{ currentOrder.order_no }}</h2>
          <p>{{ currentOrder.platform_order_no || '暂无平台订单号' }} · 设计任务：{{ taskStatusLabel(currentTask.status) }}</p>
        </div>
        <el-button @click="detailVisible = false">关闭</el-button>
      </div>

      <div class="detail-section">
        <h3>客户</h3>
        <el-descriptions border :column="2">
          <el-descriptions-item label="客户">{{ currentOrder.customer_info?.name }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ currentOrder.customer_info?.phone || '暂无' }}</el-descriptions-item>
          <el-descriptions-item label="公司">{{ currentOrder.customer_info?.company || '暂无' }}</el-descriptions-item>
          <el-descriptions-item label="标签">{{ currentOrder.customer_info?.tags || '暂无' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="detail-section">
        <h3>来源与设计</h3>
        <el-descriptions border :column="2">
          <el-descriptions-item label="店铺">{{ currentOrder.store_info?.name }}</el-descriptions-item>
          <el-descriptions-item label="销售">{{ currentOrder.salesperson_name || currentOrder.salesperson }}</el-descriptions-item>
          <el-descriptions-item label="设计处理方式">{{ currentOrder.design_option_info?.name }}</el-descriptions-item>
          <el-descriptions-item label="加急">{{ currentOrder.urgent ? '是' : '否' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="detail-section">
        <h3>产品</h3>
        <el-table :data="currentOrder.items || []" border size="small">
          <el-table-column prop="product_name" label="商品" min-width="180" />
          <el-table-column prop="sku" label="SKU" min-width="120" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column label="单价" width="110">
            <template #default="{ row }">{{ money(row.unit_price) }}</template>
          </el-table-column>
          <el-table-column label="小计" width="110">
            <template #default="{ row }">{{ money(row.line_amount) }}</template>
          </el-table-column>
        </el-table>
      </div>

      <div class="detail-section">
        <h3>金额</h3>
        <el-descriptions border :column="2">
          <el-descriptions-item label="订单金额">{{ money(currentOrder.total_amount) }}</el-descriptions-item>
          <el-descriptions-item label="已收金额">{{ money(currentOrder.paid_amount) }}</el-descriptions-item>
          <el-descriptions-item label="收款状态">{{ paymentStatusLabel(currentOrder.payment_status) }}</el-descriptions-item>
          <el-descriptions-item label="收款渠道">{{ currentOrder.payment_channel_info?.name || '暂无' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="detail-section">
        <h3>订单说明</h3>
        <p class="pre-line">{{ currentOrder.customization_note || '暂无定制说明' }}</p>
        <p class="pre-line muted">{{ currentOrder.remark || '暂无备注 / 收货信息' }}</p>
      </div>

      <div class="detail-section finalize-section">
        <h3>设计定稿</h3>
        <el-input v-model="finalRemark" type="textarea" :rows="3" placeholder="填写设计备注、生产注意事项或定稿说明" />
        <el-upload
          v-model:file-list="finalFiles"
          action="#"
          :auto-upload="false"
          :on-change="handleFinalFileChange"
          multiple
          drag
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽定稿图或文件到此处，或点击添加，选择后自动上传</div>
        </el-upload>
        <div class="upload-actions">
          <el-button type="primary" :loading="finalizing" :disabled="!canFinalize" @click="finalizeDesign">定稿</el-button>
        </div>
        <div v-if="finalAttachments.length" class="attachment-list">
          <a v-for="file in finalAttachments" :key="file.id" :href="file.file_url" target="_blank" rel="noreferrer">
            {{ file.file_name }}
          </a>
        </div>
      </div>
    </section>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { api, list } from '../api/client'

const rows = ref<any[]>([])
const pendingCount = ref(0)
const viewMode = ref<'pending' | 'recent'>('pending')
const detailVisible = ref(false)
const currentTask = ref<any>(null)
const currentOrder = ref<any>(null)
const finalFiles = ref<any[]>([])
const finalAttachments = ref<any[]>([])
const finalRemark = ref('')
const uploadingCount = ref(0)
const finalizing = ref(false)
const uploadedFileUids = new Set<string>()
const uploading = computed(() => uploadingCount.value > 0)
const canFinalize = computed(() => Boolean(currentTask.value && currentTask.value.status !== 'confirmed' && finalAttachments.value.length && !uploading.value))

async function load() {
  const pendingStatuses = 'pending,designing,waiting_confirmation,needs_changes'
  const pendingPage = await list<any>('/design-tasks', { status: pendingStatuses, page_size: viewMode.value === 'pending' ? 100 : 1 })
  pendingCount.value = pendingPage.count
  if (viewMode.value === 'pending') {
    rows.value = pendingPage.results
    return
  }
  const completedPage = await list<any>('/design-tasks', { status: 'confirmed', ordering: 'recent_completed', page_size: 30 })
  rows.value = completedPage.results
}

async function switchViewMode(mode: 'pending' | 'recent') {
  if (viewMode.value === mode) return
  viewMode.value = mode
  await load()
}

async function claim(id: string) {
  await api.post(`/design-tasks/${id}/claim/`)
  ElMessage.success('已领取')
  await load()
}

async function openDesignDetail(task: any) {
  currentTask.value = task
  finalFiles.value = []
  finalRemark.value = task.remark || ''
  uploadedFileUids.clear()
  const [orderResponse] = await Promise.all([
    api.get(`/orders/${task.order.id}/`),
    loadFinalAttachments(task.id)
  ])
  currentOrder.value = orderResponse.data
  detailVisible.value = true
}

async function loadFinalAttachments(taskId: string) {
  finalAttachments.value = (await list<any>('/attachments', { business_type: 'design', business_id: taskId, page_size: 50 })).results
}

async function handleFinalFileChange(file: any) {
  if (!currentTask.value) return
  if (!file?.raw || uploadedFileUids.has(file.uid)) return
  uploadedFileUids.add(file.uid)
  uploadingCount.value += 1
  try {
    const formData = new FormData()
    formData.append('file', file.raw)
    formData.append('business_type', 'design')
    formData.append('business_id', currentTask.value.id)
    await api.post('/attachments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    finalFiles.value = finalFiles.value.filter((item) => item.uid !== file.uid)
    await loadFinalAttachments(currentTask.value.id)
    ElMessage.success('定稿文件已上传')
  } catch {
    uploadedFileUids.delete(file.uid)
    ElMessage.error('定稿文件上传失败')
  } finally {
    uploadingCount.value -= 1
  }
}

async function finalizeDesign() {
  if (!currentTask.value || !finalAttachments.value.length) return ElMessage.warning('请先上传设计定稿')
  finalizing.value = true
  try {
    let task = currentTask.value
    if (task.status === 'pending') {
      const claimResponse = await api.post(`/design-tasks/${task.id}/claim/`)
      task = claimResponse.data
      currentTask.value = task
    }
    if (finalRemark.value.trim() !== (task.remark || '')) {
      const remarkResponse = await api.patch(`/design-tasks/${task.id}/`, { remark: finalRemark.value.trim() })
      task = remarkResponse.data
      currentTask.value = task
    }
    const response = await api.post(`/design-tasks/${task.id}/confirm/`)
    currentTask.value = response.data
    ElMessage.success('设计已定稿，进入生产安排')
    detailVisible.value = false
    await load()
  } finally {
    finalizing.value = false
  }
}

function money(value: string | number | null | undefined) {
  return `¥${Number(value || 0).toFixed(2)}`
}

function taskStatusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: '待领取',
    designing: '设计中',
    waiting_confirmation: '待确认',
    needs_changes: '需修改',
    confirmed: '已确认'
  }
  return labels[status] || status
}

function orderStatusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: '待设计',
    submitted: '待设计',
    pending_design: '待设计',
    designing: '待设计',
    design_confirmed: '待生产',
    pending_production: '待生产',
    completed: '已完成',
    cancelled: '已撤销'
  }
  return labels[status] || status
}

function paymentStatusLabel(status: string) {
  const labels: Record<string, string> = {
    unpaid: '未收款',
    partial: '部分收款',
    paid: '已收款'
  }
  return labels[status] || status
}

onMounted(load)
</script>
