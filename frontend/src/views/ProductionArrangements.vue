<template>
  <section class="panel">
    <div class="panel-head">
      <div class="panel-title">
        <h2>生产安排</h2>
        <small>待处理订单 {{ pendingCount }} 单</small>
      </div>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="rows" border>
      <el-table-column prop="arrangement_no" label="安排号" width="160" />
      <el-table-column prop="order.order_no" label="订单号" width="160" />
      <el-table-column prop="order.customer.name" label="客户" />
      <el-table-column prop="factory_name" label="代工工厂" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">{{ productionStatusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openProductionDetail(row)" :disabled="row.status === 'confirmed'">生产确认</el-button>
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
        <el-input v-model="productionRemark" type="textarea" :rows="3" placeholder="填写生产安排备注、代工特殊要求或异常说明" />
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
          <el-button type="primary" :loading="confirming" :disabled="!canConfirmProduction" @click="confirmProduction">生产确认</el-button>
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
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { api, list } from '../api/client'

const rows = ref<any[]>([])
const pendingCount = ref(0)
const detailVisible = ref(false)
const currentArrangement = ref<any>(null)
const currentOrder = ref<any>(null)
const productionFiles = ref<any[]>([])
const productionAttachments = ref<any[]>([])
const productionRemark = ref('')
const uploadingCount = ref(0)
const confirming = ref(false)
const uploadedFileUids = new Set<string>()
const uploading = computed(() => uploadingCount.value > 0)
const canConfirmProduction = computed(() => Boolean(currentArrangement.value && currentArrangement.value.status !== 'confirmed' && !uploading.value))

async function load() {
  const [arrangementPage, pendingPage, scheduledPage, exceptionPage] = await Promise.all([
    list<any>('/production-arrangements'),
    list<any>('/production-arrangements', { status: 'pending', page_size: 1 }),
    list<any>('/production-arrangements', { status: 'scheduled', page_size: 1 }),
    list<any>('/production-arrangements', { status: 'exception', page_size: 1 })
  ])
  rows.value = arrangementPage.results
  pendingCount.value = pendingPage.count + scheduledPage.count + exceptionPage.count
}

async function openProductionDetail(arrangement: any) {
  currentArrangement.value = arrangement
  productionFiles.value = []
  productionRemark.value = arrangement.remark || ''
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
  confirming.value = true
  try {
    let arrangement = currentArrangement.value
    if (productionRemark.value.trim() !== (arrangement.remark || '')) {
      const remarkResponse = await api.patch(`/production-arrangements/${arrangement.id}/`, { remark: productionRemark.value.trim() })
      arrangement = remarkResponse.data
      currentArrangement.value = arrangement
    }
    const response = await api.post(`/production-arrangements/${arrangement.id}/confirm/`)
    currentArrangement.value = response.data
    ElMessage.success('生产已确认，订单完成')
    detailVisible.value = false
    await load()
  } finally {
    confirming.value = false
  }
}

function money(value: string | number | null | undefined) {
  return `¥${Number(value || 0).toFixed(2)}`
}

function productionStatusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: '待安排',
    scheduled: '已安排',
    confirmed: '已确认',
    exception: '异常'
  }
  return labels[status] || status
}

function orderStatusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: '草稿',
    submitted: '已提交',
    pending_design: '待设计',
    designing: '设计中',
    design_confirmed: '设计确认',
    pending_production: '待生产安排',
    completed: '已完成',
    cancelled: '已取消'
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
