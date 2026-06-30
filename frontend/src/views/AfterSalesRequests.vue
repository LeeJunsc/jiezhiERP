<template>
  <section class="panel">
    <div class="panel-head">
      <div class="panel-title">
        <h2>售后处理</h2>
        <small>待处理 {{ pendingCount }} 单</small>
      </div>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-form inline :model="filters" class="search-bar">
      <el-form-item label="关键词">
        <el-input v-model="filters.keyword" clearable placeholder="售后单、订单号、客户、说明" @keyup.enter="search" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 150px">
          <el-option label="待处理" value="pending_processing" />
          <el-option label="待处理" value="pending" />
          <el-option label="处理中" value="processing" />
          <el-option label="已完成" value="completed" />
          <el-option label="已驳回" value="closed" />
        </el-select>
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="filters.type" clearable placeholder="全部" style="width: 150px">
          <el-option label="退款" value="refund" />
          <el-option label="补发" value="reship" />
          <el-option label="返修" value="repair" />
          <el-option label="投诉" value="complaint" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>
      <el-form-item label="申请日期">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          unlink-panels
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          :shortcuts="dateRangeShortcuts"
        />
      </el-form-item>
      <el-button type="primary" @click="search">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </el-form>

    <div class="summary-strip">
      <div>
        <span>售后数</span>
        <strong>{{ total }}</strong>
      </div>
      <div>
        <span>待处理</span>
        <strong>{{ pendingCount }}</strong>
      </div>
    </div>

    <el-table :data="rows" border>
      <el-table-column prop="request_no" label="售后单号" width="150" />
      <el-table-column prop="order_info.order_no" label="订单号" width="150" />
      <el-table-column prop="order_info.customer.name" label="客户" min-width="130" />
      <el-table-column label="类型" width="90">
        <template #default="{ row }">{{ typeLabel(row.type) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column prop="description" label="问题说明" min-width="220" show-overflow-tooltip />
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="actions">
      <el-pagination
        layout="sizes, prev, pager, next"
        :page-sizes="pageSizeOptions"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @size-change="handlePageSizeChange"
        @current-change="page = $event; load()"
      />
    </div>
  </section>

  <el-drawer v-model="detailVisible" size="min(720px, 100vw)" :with-header="false" destroy-on-close>
    <section v-if="current" class="order-detail-drawer">
      <div class="drawer-head">
        <div>
          <span class="status-pill">{{ statusLabel(current.status) }}</span>
          <h2>{{ current.request_no }}</h2>
          <p>{{ current.order_info?.order_no }} · {{ current.order_info?.customer?.name }}</p>
        </div>
        <el-button @click="detailVisible = false">关闭</el-button>
      </div>

      <div class="detail-section">
        <h3>售后信息</h3>
        <el-descriptions border :column="2">
          <el-descriptions-item label="类型">{{ typeLabel(current.type) }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ current.owner_name || '暂无' }}</el-descriptions-item>
          <el-descriptions-item label="退款金额">{{ money(current.refund_amount) }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusLabel(current.status) }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="detail-section">
        <h3>问题说明</h3>
        <p class="pre-line">{{ current.description }}</p>
      </div>

      <div class="detail-section">
        <h3>处理备注</h3>
        <p class="pre-line">{{ current.remark || '暂无备注' }}</p>
      </div>

      <div class="detail-section">
        <h3>售后附件</h3>
        <el-upload
          v-if="canHandle"
          v-model:file-list="afterSalesFiles"
          action="#"
          :auto-upload="false"
          :on-change="handleAfterSalesFileChange"
          multiple
          drag
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽售后图片或文件到此处，或点击添加，选择后自动上传</div>
        </el-upload>
        <div v-if="afterSalesAttachments.length" class="attachment-list">
          <a v-for="file in afterSalesAttachments" :key="file.id" :href="file.file_url" target="_blank" rel="noreferrer">
            {{ file.file_name }}
          </a>
        </div>
        <p v-else class="empty-text">暂无售后附件</p>
      </div>

      <div v-if="canHandle && ['pending', 'processing'].includes(current.status)" class="actions mobile-sticky-actions">
        <el-button type="success" @click="openHandle(current, 'complete')">完成</el-button>
        <el-button type="danger" plain @click="openHandle(current, 'reject')">驳回</el-button>
      </div>
    </section>
  </el-drawer>

  <el-dialog v-model="handleVisible" :title="handleTitle" width="min(520px, 94vw)">
    <el-form label-position="top">
      <el-form-item label="处理备注">
        <el-input v-model="handleRemark" type="textarea" :rows="4" placeholder="填写处理结果、沟通记录或驳回原因" />
      </el-form-item>
      <el-form-item label="处理附件">
        <el-upload
          v-model:file-list="handleFiles"
          action="#"
          :auto-upload="false"
          :on-change="handleAfterSalesFileChange"
          multiple
          drag
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽处理图片或文件到此处，或点击添加，选择后自动上传</div>
        </el-upload>
      </el-form-item>
      <div v-if="afterSalesAttachments.length" class="attachment-list">
        <a v-for="file in afterSalesAttachments" :key="file.id" :href="file.file_url" target="_blank" rel="noreferrer">
          {{ file.file_name }}
        </a>
      </div>
    </el-form>
    <template #footer>
      <el-button @click="handleVisible = false">取消</el-button>
      <el-button :type="handleAction === 'reject' ? 'danger' : 'primary'" @click="submitHandle">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { api, list } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { dateRangeShortcuts } from '../utils/dateShortcuts'
import { pageSizeOptions } from '../utils/pagination'

const auth = useAuthStore()
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const pendingCount = ref(0)
const dateRange = ref<string[]>([])
const detailVisible = ref(false)
const current = ref<any>(null)
const handleVisible = ref(false)
const handleAction = ref<'complete' | 'reject'>('complete')
const handleRemark = ref('')
const afterSalesFiles = ref<any[]>([])
const handleFiles = ref<any[]>([])
const afterSalesAttachments = ref<any[]>([])
const uploadedFileUids = new Set<string>()
const filters = reactive({ keyword: '', status: 'pending_processing', type: '' })
const canHandle = computed(() => Boolean(auth.user?.is_superuser || auth.user?.groups?.some((group) => ['管理员', '售后'].includes(group.name))))
const handleTitle = computed(() => (handleAction.value === 'reject' ? '驳回售后' : '完成售后'))

function queryParams() {
  const statusMap: Record<string, string> = {
    pending_processing: 'pending,processing'
  }
  return {
    keyword: filters.keyword,
    status: statusMap[filters.status] || filters.status,
    type: filters.type,
    created_from: dateRange.value?.[0] || '',
    created_to: dateRange.value?.[1] || ''
  }
}

async function load() {
  const params = queryParams()
  const [data, pendingPage] = await Promise.all([
    list<any>('/after-sales-requests', { page: page.value, page_size: pageSize.value, ...params }),
    list<any>('/after-sales-requests', { status: 'pending,processing', page_size: 1 })
  ])
  rows.value = data.results
  total.value = data.count
  pendingCount.value = pendingPage.count
}

async function handlePageSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
  await load()
}

async function search() {
  page.value = 1
  await load()
}

async function resetFilters() {
  filters.keyword = ''
  filters.status = 'pending_processing'
  filters.type = ''
  dateRange.value = []
  await search()
}

async function openDetail(row: any) {
  current.value = row
  afterSalesFiles.value = []
  handleFiles.value = []
  uploadedFileUids.clear()
  await loadAfterSalesAttachments(row.id)
  detailVisible.value = true
}

async function openHandle(row: any, action: 'complete' | 'reject') {
  current.value = row
  handleAction.value = action
  handleRemark.value = row.remark || ''
  handleFiles.value = []
  uploadedFileUids.clear()
  await loadAfterSalesAttachments(row.id)
  handleVisible.value = true
}

async function loadAfterSalesAttachments(afterSalesId: string) {
  afterSalesAttachments.value = (await list<any>('/attachments', { business_type: 'after_sales', business_id: afterSalesId, page_size: 50 })).results
}

async function handleAfterSalesFileChange(file: any) {
  if (!current.value) return
  if (!file?.raw || uploadedFileUids.has(file.uid)) return
  uploadedFileUids.add(file.uid)
  try {
    const formData = new FormData()
    formData.append('file', file.raw)
    formData.append('business_type', 'after_sales')
    formData.append('business_id', current.value.id)
    await api.post('/attachments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    afterSalesFiles.value = afterSalesFiles.value.filter((item) => item.uid !== file.uid)
    handleFiles.value = handleFiles.value.filter((item) => item.uid !== file.uid)
    await loadAfterSalesAttachments(current.value.id)
    ElMessage.success('售后附件已上传')
  } catch {
    uploadedFileUids.delete(file.uid)
    ElMessage.error('售后附件上传失败')
  }
}

async function submitHandle() {
  if (!current.value) return
  await api.post(`/after-sales-requests/${current.value.id}/${handleAction.value}/`, {
    remark: handleRemark.value.trim()
  })
  ElMessage.success(handleAction.value === 'reject' ? '售后已驳回' : '售后已完成')
  handleVisible.value = false
  detailVisible.value = false
  await load()
}

function money(value: string | number | null | undefined) {
  return `¥${Number(value || 0).toFixed(2)}`
}

function typeLabel(type: string) {
  const labels: Record<string, string> = {
    refund: '退款',
    reship: '补发',
    repair: '返修',
    complaint: '投诉',
    other: '其他'
  }
  return labels[type] || type
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    closed: '已驳回'
  }
  return labels[status] || status
}

onMounted(async () => {
  await auth.loadMe()
  await load()
})
</script>
