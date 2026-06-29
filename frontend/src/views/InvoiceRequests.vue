<template>
  <section class="panel">
    <div class="panel-head">
      <div class="panel-title">
        <h2>发票审批</h2>
        <small>待处理 {{ pendingCount }} 单</small>
      </div>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-form inline :model="filters" class="search-bar">
      <el-form-item label="关键词">
        <el-input v-model="filters.keyword" clearable placeholder="申请号、订单号、客户、抬头" @keyup.enter="search" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 150px">
          <el-option label="待审批" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已驳回" value="rejected" />
          <el-option label="草稿" value="draft" />
          <el-option label="已撤回" value="withdrawn" />
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
        <span>申请数</span>
        <strong>{{ summary.request_count }}</strong>
      </div>
      <div>
        <span>申请金额</span>
        <strong>{{ money(summary.total_amount) }}</strong>
      </div>
    </div>

    <el-table :data="rows" border>
      <el-table-column prop="request_no" label="申请号" width="150" />
      <el-table-column prop="order_info.order_no" label="订单号" width="150" />
      <el-table-column prop="customer_info.name" label="客户" min-width="130" />
      <el-table-column prop="title" label="发票抬头" min-width="180" />
      <el-table-column label="类型" width="90">
        <template #default="{ row }">{{ invoiceTypeLabel(row.invoice_type) }}</template>
      </el-table-column>
      <el-table-column label="金额" width="120">
        <template #default="{ row }">{{ money(row.amount) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
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

  <el-drawer v-model="detailVisible" size="min(680px, 100vw)" :with-header="false" destroy-on-close>
    <section v-if="current" class="order-detail-drawer">
      <div class="drawer-head">
        <div>
          <span class="status-pill">{{ statusLabel(current.status) }}</span>
          <h2>{{ current.request_no }}</h2>
          <p>{{ current.order_info?.order_no || '未关联订单' }} · {{ current.customer_info?.name }}</p>
        </div>
        <el-button @click="detailVisible = false">关闭</el-button>
      </div>

      <div class="detail-section">
        <h3>发票信息</h3>
        <el-descriptions border :column="2">
          <el-descriptions-item label="发票类型">{{ invoiceTypeLabel(current.invoice_type) }}</el-descriptions-item>
          <el-descriptions-item label="金额">{{ money(current.amount) }}</el-descriptions-item>
          <el-descriptions-item label="抬头">{{ current.title }}</el-descriptions-item>
          <el-descriptions-item label="税号">{{ current.tax_number || '暂无' }}</el-descriptions-item>
          <el-descriptions-item label="申请人">{{ current.applicant_name || current.applicant }}</el-descriptions-item>
          <el-descriptions-item label="审批人">{{ current.approver_name || '暂无' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="detail-section">
        <h3>备注说明</h3>
        <p class="pre-line">{{ current.remark || '暂无备注' }}</p>
      </div>

      <div class="detail-section">
        <h3>发票附件</h3>
        <el-upload
          v-if="canApprove"
          v-model:file-list="invoiceFiles"
          action="#"
          :auto-upload="false"
          :on-change="handleInvoiceFileChange"
          multiple
          drag
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽发票 PDF、图片或文件到此处，或点击添加，选择后自动上传</div>
        </el-upload>
        <div v-if="invoiceAttachments.length" class="attachment-list">
          <a v-for="file in invoiceAttachments" :key="file.id" :href="file.file_url" target="_blank" rel="noreferrer">
            {{ file.file_name }}
          </a>
        </div>
        <p v-else class="empty-text">暂无发票附件</p>
      </div>

      <div v-if="canApprove && current.status === 'pending'" class="actions mobile-sticky-actions">
        <el-button type="primary" @click="approve(current)">通过</el-button>
        <el-button type="danger" plain @click="reject(current)">驳回</el-button>
      </div>
    </section>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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
const invoiceFiles = ref<any[]>([])
const invoiceAttachments = ref<any[]>([])
const uploadingFileUids = new Set<string>()
const filters = reactive({ keyword: '', status: 'pending' })
const summary = reactive({ request_count: 0, total_amount: '0.00' })
const canApprove = computed(() => Boolean(auth.user?.is_superuser || auth.user?.groups?.some((group) => ['管理员', '财务'].includes(group.name))))

function queryParams() {
  return {
    keyword: filters.keyword,
    status: filters.status,
    created_from: dateRange.value?.[0] || '',
    created_to: dateRange.value?.[1] || ''
  }
}

async function load() {
  const params = queryParams()
  const [data, summaryResponse, pendingPage] = await Promise.all([
    list<any>('/invoice-requests', { page: page.value, page_size: pageSize.value, ...params }),
    api.get('/invoice-requests/summary/', { params }),
    list<any>('/invoice-requests', { status: 'pending', page_size: 1 })
  ])
  rows.value = data.results
  total.value = data.count
  Object.assign(summary, summaryResponse.data)
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
  filters.status = 'pending'
  dateRange.value = []
  await search()
}

async function openDetail(row: any) {
  current.value = row
  invoiceFiles.value = []
  uploadingFileUids.clear()
  await loadInvoiceAttachments(row.id)
  detailVisible.value = true
}

async function loadInvoiceAttachments(invoiceId: string) {
  invoiceAttachments.value = (await list<any>('/attachments', { business_type: 'invoice', business_id: invoiceId, page_size: 50 })).results
}

async function handleInvoiceFileChange(file: any) {
  if (!current.value) return
  if (!file?.raw || uploadingFileUids.has(file.uid)) return
  uploadingFileUids.add(file.uid)
  try {
    const formData = new FormData()
    formData.append('file', file.raw)
    formData.append('business_type', 'invoice')
    formData.append('business_id', current.value.id)
    await api.post('/attachments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    invoiceFiles.value = invoiceFiles.value.filter((item) => item.uid !== file.uid)
    await loadInvoiceAttachments(current.value.id)
    ElMessage.success('发票附件已上传')
  } catch {
    uploadingFileUids.delete(file.uid)
    ElMessage.error('发票附件上传失败')
  }
}

async function approve(row: any) {
  try {
    await ElMessageBox.confirm(`确认通过发票申请 ${row.request_no}？`, '发票审批确认', {
      confirmButtonText: '通过',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  await api.post(`/invoice-requests/${row.id}/approve/`)
  ElMessage.success('发票申请已通过')
  detailVisible.value = false
  await load()
}

async function reject(row: any) {
  try {
    await ElMessageBox.confirm(`确认驳回发票申请 ${row.request_no}？`, '发票审批确认', {
      confirmButtonText: '驳回',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
  } catch {
    return
  }
  await api.post(`/invoice-requests/${row.id}/reject/`)
  ElMessage.success('发票申请已驳回')
  detailVisible.value = false
  await load()
}

function money(value: string | number | null | undefined) {
  return `¥${Number(value || 0).toFixed(2)}`
}

function invoiceTypeLabel(type: string) {
  const labels: Record<string, string> = { normal: '普票', special: '专票' }
  return labels[type] || type
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: '草稿',
    pending: '待审批',
    approved: '已通过',
    rejected: '已驳回',
    withdrawn: '已撤回'
  }
  return labels[status] || status
}

onMounted(async () => {
  await auth.loadMe()
  await load()
})
</script>
