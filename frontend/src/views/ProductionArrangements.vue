<template>
  <section class="panel">
    <div class="panel-head">
      <div class="panel-title">
        <h2>生产安排</h2>
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
      <el-table-column prop="arrangement_no" label="安排号" width="160" />
      <el-table-column prop="order.order_no" label="订单号" width="160" />
      <el-table-column prop="order.customer.name" label="客户" />
      <el-table-column prop="factory_name" label="代工工厂" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">{{ productionStatusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openProductionDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>

  <el-drawer v-model="detailVisible" size="min(780px, 100vw)" :with-header="false" destroy-on-close>
    <section v-if="currentOrder && currentArrangement" class="order-detail-drawer">
      <div class="drawer-head">
        <div>
          <span class="status-pill">{{ orderStatusLabel(currentOrder.status) }}</span>
          <h2>{{ currentOrder.order_no }}</h2>
          <p>{{ currentOrder.platform_order_no || '暂无平台订单号' }} · 生产安排：{{ productionStatusLabel(currentArrangement.status) }}</p>
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
        <h3>来源与生产</h3>
        <el-descriptions border :column="2">
          <el-descriptions-item label="店铺">{{ currentOrder.store_info?.name }}</el-descriptions-item>
          <el-descriptions-item label="销售">{{ currentOrder.salesperson_name || currentOrder.salesperson }}</el-descriptions-item>
          <el-descriptions-item label="设计处理方式">{{ currentOrder.design_option_info?.name }}</el-descriptions-item>
          <el-descriptions-item label="代工工厂">{{ currentArrangement.factory_name || '暂无' }}</el-descriptions-item>
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
        <h3>生产确认</h3>
        <el-form label-position="top" class="compact-form">
          <el-form-item label="代工工厂">
            <el-input v-model="factoryName" placeholder="填写本单安排的代工工厂" />
          </el-form-item>
          <el-form-item label="预计完成时间">
            <el-date-picker
              v-model="plannedFinishAt"
              type="datetime"
              value-format="YYYY-MM-DDTHH:mm:ss"
              placeholder="选择预计完成时间"
              style="width: 100%"
            />
          </el-form-item>
        </el-form>
        <el-input v-model="productionRemark" type="textarea" :rows="3" placeholder="填写生产安排备注、代工特殊要求或处理说明" />
        <el-upload
          v-model:file-list="productionFiles"
          action="#"
          :auto-upload="false"
          :on-change="handleProductionFileChange"
          multiple
          drag
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽生产素材或文件到此处，或点击添加，选择后自动上传</div>
        </el-upload>
        <div class="upload-actions">
          <el-button plain :loading="returning" :disabled="!canHandleProduction" @click="returnToDesign">退回设计</el-button>
          <el-button type="primary" :loading="confirming" :disabled="!canHandleProduction" @click="confirmProduction">生产确认</el-button>
          <el-button type="danger" plain :loading="rejecting" :disabled="!canHandleProduction" @click="rejectOrder">驳回订单</el-button>
        </div>
        <div v-if="productionAttachments.length" class="attachment-list">
          <a v-for="file in productionAttachments" :key="file.id" :href="file.file_url" target="_blank" rel="noreferrer">
            {{ file.file_name }}
          </a>
        </div>
      </div>
    </section>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { api, list } from '../api/client'

const rows = ref<any[]>([])
const pendingCount = ref(0)
const viewMode = ref<'pending' | 'recent'>('pending')
const detailVisible = ref(false)
const currentArrangement = ref<any>(null)
const currentOrder = ref<any>(null)
const productionFiles = ref<any[]>([])
const productionAttachments = ref<any[]>([])
const productionRemark = ref('')
const factoryName = ref('')
const plannedFinishAt = ref('')
const uploadingCount = ref(0)
const confirming = ref(false)
const returning = ref(false)
const rejecting = ref(false)
const uploadedFileUids = new Set<string>()
const uploading = computed(() => uploadingCount.value > 0)
const canHandleProduction = computed(() =>
  Boolean(
    currentArrangement.value &&
      !['confirmed', 'exception'].includes(currentArrangement.value.status) &&
      !['completed', 'cancelled'].includes(currentOrder.value?.status) &&
      !uploading.value
  )
)

async function load() {
  const pendingStatuses = 'pending,scheduled,exception'
  const [pendingPage, activePage] = await Promise.all([
    list<any>('/production-arrangements', { status: 'pending,scheduled', page_size: 1 }),
    viewMode.value === 'pending'
      ? list<any>('/production-arrangements', { status: pendingStatuses, page_size: 100 })
      : list<any>('/production-arrangements', { status: 'confirmed', ordering: 'recent_completed', page_size: 30 })
  ])
  pendingCount.value = pendingPage.count
  rows.value = activePage.results
}

async function switchViewMode(mode: 'pending' | 'recent') {
  if (viewMode.value === mode) return
  viewMode.value = mode
  await load()
}

async function openProductionDetail(arrangement: any) {
  currentArrangement.value = arrangement
  productionFiles.value = []
  productionRemark.value = arrangement.remark || ''
  factoryName.value = arrangement.factory_name || ''
  plannedFinishAt.value = arrangement.planned_finish_at || ''
  uploadedFileUids.clear()
  const [orderResponse] = await Promise.all([
    api.get(`/orders/${arrangement.order.id}/`),
    loadProductionAttachments(arrangement.id)
  ])
  currentOrder.value = orderResponse.data
  detailVisible.value = true
}

async function loadProductionAttachments(arrangementId: string) {
  productionAttachments.value = (await list<any>('/attachments', { business_type: 'production', business_id: arrangementId, page_size: 50 })).results
}

async function handleProductionFileChange(file: any) {
  if (!currentArrangement.value) return
  if (!file?.raw || uploadedFileUids.has(file.uid)) return
  uploadedFileUids.add(file.uid)
  uploadingCount.value += 1
  try {
    const formData = new FormData()
    formData.append('file', file.raw)
    formData.append('business_type', 'production')
    formData.append('business_id', currentArrangement.value.id)
    await api.post('/attachments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    productionFiles.value = productionFiles.value.filter((item) => item.uid !== file.uid)
    await loadProductionAttachments(currentArrangement.value.id)
    ElMessage.success('生产素材已上传')
  } catch {
    uploadedFileUids.delete(file.uid)
    ElMessage.error('生产素材上传失败')
  } finally {
    uploadingCount.value -= 1
  }
}

async function confirmProduction() {
  if (!currentArrangement.value) return
  try {
    await ElMessageBox.confirm(`确认生产完成订单 ${currentOrder.value?.order_no || ''}？`, '生产确认', {
      confirmButtonText: '生产确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  confirming.value = true
  try {
    let arrangement = currentArrangement.value
    const patchPayload = {
      factory_name: factoryName.value.trim(),
      planned_finish_at: plannedFinishAt.value || null,
      remark: productionRemark.value.trim()
    }
    if (
      patchPayload.factory_name !== (arrangement.factory_name || '') ||
      patchPayload.planned_finish_at !== (arrangement.planned_finish_at || null) ||
      patchPayload.remark !== (arrangement.remark || '')
    ) {
      const remarkResponse = await api.patch(`/production-arrangements/${arrangement.id}/`, patchPayload)
      arrangement = remarkResponse.data
      currentArrangement.value = arrangement
    }
    const response = await api.post(`/production-arrangements/${arrangement.id}/confirm/`)
    currentArrangement.value = response.data
    ElMessage.success('订单已完成')
    detailVisible.value = false
    await load()
  } finally {
    confirming.value = false
  }
}

async function returnToDesign() {
  if (!currentArrangement.value) return
  try {
    await ElMessageBox.confirm(`确认将订单 ${currentOrder.value?.order_no || ''} 退回设计？`, '退回设计', {
      confirmButtonText: '退回设计',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  returning.value = true
  try {
    await api.post(`/production-arrangements/${currentArrangement.value.id}/return-to-design/`, {
      remark: productionRemark.value.trim()
    })
    ElMessage.success('订单已退回设计')
    detailVisible.value = false
    await load()
  } finally {
    returning.value = false
  }
}

async function rejectOrder() {
  if (!currentArrangement.value) return
  try {
    await ElMessageBox.confirm(`确认驳回订单 ${currentOrder.value?.order_no || ''}？`, '驳回订单', {
      confirmButtonText: '驳回订单',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
  } catch {
    return
  }
  rejecting.value = true
  try {
    await api.post(`/production-arrangements/${currentArrangement.value.id}/reject-order/`, {
      remark: productionRemark.value.trim()
    })
    ElMessage.success('订单已驳回')
    detailVisible.value = false
    await load()
  } finally {
    rejecting.value = false
  }
}

function money(value: string | number | null | undefined) {
  return `¥${Number(value || 0).toFixed(2)}`
}

function productionStatusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: '待安排',
    scheduled: '已安排',
    confirmed: '已安排',
    exception: '已驳回'
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
