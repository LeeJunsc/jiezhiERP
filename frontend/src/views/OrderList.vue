<template>
  <section class="panel">
    <div class="panel-head">
      <h2>订单列表</h2>
      <el-button type="primary" @click="$router.push('/orders/new')">新建订单</el-button>
    </div>

    <el-form inline :model="filters" class="search-bar">
      <el-form-item label="关键词">
        <el-input v-model="filters.keyword" clearable placeholder="搜索订单所有信息" @keyup.enter="search" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 160px">
          <el-option label="草稿" value="draft" />
          <el-option label="待设计" value="pending_design" />
          <el-option label="设计中" value="designing" />
          <el-option label="待生产安排" value="pending_production" />
          <el-option label="已完成" value="completed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
      </el-form-item>
      <el-form-item label="下单日期">
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
        <span>订单数</span>
        <strong>{{ summary.order_count }}</strong>
      </div>
      <div>
        <span>订单金额</span>
        <strong>{{ money(summary.total_amount) }}</strong>
      </div>
    </div>

    <el-table :data="rows" border>
      <el-table-column prop="order_no" label="订单号" width="160" />
      <el-table-column prop="platform_order_no" label="平台订单号" width="170" />
      <el-table-column prop="store.name" label="店铺" min-width="130" />
      <el-table-column prop="customer.name" label="客户" min-width="120" />
      <el-table-column prop="design_option.name" label="设计处理方式" width="160" />
      <el-table-column label="状态" width="130">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column label="金额" width="120">
        <template #default="{ row }">{{ money(row.total_amount) }}</template>
      </el-table-column>
      <el-table-column label="订单生成时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="设计定稿时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.design_finalized_at) }}</template>
      </el-table-column>
      <el-table-column label="生产安排时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.production_arranged_at) }}</template>
      </el-table-column>
      <el-table-column label="发票申请时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.invoice_requested_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDetail(row.id)">详情</el-button>
          <el-button v-if="isAdmin" size="small" type="danger" plain @click="deleteOrder(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="actions">
      <el-pagination
        layout="prev, pager, next"
        :total="total"
        :page-size="20"
        :current-page="page"
        @current-change="page = $event; load()"
      />
    </div>
  </section>

  <el-drawer v-model="detailVisible" size="min(920px, 100vw)" :with-header="false" destroy-on-close>
    <section v-if="currentOrder" class="order-detail-drawer">
      <div class="drawer-head">
        <div>
          <span class="status-pill">{{ statusLabel(currentOrder.status) }}</span>
          <h2>{{ currentOrder.order_no }}</h2>
          <p>{{ currentOrder.platform_order_no || '暂无平台订单号' }}</p>
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

      <div class="detail-section">
        <h3>关联资料</h3>
        <div class="related-grid">
          <article class="related-card">
            <div class="related-card-head">
              <strong>订单素材</strong>
              <span>{{ attachmentCount(orderRelated?.order_attachments) }}</span>
            </div>
            <AttachmentList :files="orderRelated?.order_attachments || []" />
          </article>

          <article class="related-card">
            <div class="related-card-head">
              <strong>设计定稿</strong>
              <span>{{ orderRelated?.design_task ? designTaskStatusLabel(orderRelated.design_task.status) : '无设计任务' }}</span>
            </div>
            <el-descriptions v-if="orderRelated?.design_task" border :column="2" size="small">
              <el-descriptions-item label="任务号">{{ orderRelated.design_task.task_no }}</el-descriptions-item>
              <el-descriptions-item label="定稿时间">{{ formatDateTime(orderRelated.design_task.confirmed_at) }}</el-descriptions-item>
              <el-descriptions-item label="设计师">{{ orderRelated.design_task.designer_name || '暂无' }}</el-descriptions-item>
              <el-descriptions-item label="备注">{{ orderRelated.design_task.remark || '暂无' }}</el-descriptions-item>
            </el-descriptions>
            <AttachmentList :files="orderRelated?.design_attachments || []" />
          </article>

          <article class="related-card">
            <div class="related-card-head">
              <strong>生产安排</strong>
              <span>{{ orderRelated?.production_arrangement ? productionStatusLabel(orderRelated.production_arrangement.status) : '无生产安排' }}</span>
            </div>
            <el-descriptions v-if="orderRelated?.production_arrangement" border :column="2" size="small">
              <el-descriptions-item label="安排号">{{ orderRelated.production_arrangement.arrangement_no }}</el-descriptions-item>
              <el-descriptions-item label="代工工厂">{{ orderRelated.production_arrangement.factory_name || '暂无' }}</el-descriptions-item>
              <el-descriptions-item label="安排时间">{{ formatDateTime(orderRelated.production_arrangement.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="确认时间">{{ formatDateTime(orderRelated.production_arrangement.confirmed_at) }}</el-descriptions-item>
              <el-descriptions-item label="备注">{{ orderRelated.production_arrangement.remark || '暂无' }}</el-descriptions-item>
            </el-descriptions>
            <AttachmentList :files="orderRelated?.production_attachments || []" />
          </article>

          <article class="related-card wide">
            <div class="related-card-head">
              <strong>发票申请</strong>
              <span>{{ (orderRelated?.invoice_requests || []).length }} 条</span>
            </div>
            <div v-if="orderRelated?.invoice_requests?.length" class="related-list">
              <section v-for="invoice in orderRelated.invoice_requests" :key="invoice.id" class="related-record">
                <el-descriptions border :column="2" size="small">
                  <el-descriptions-item label="申请号">{{ invoice.request_no }}</el-descriptions-item>
                  <el-descriptions-item label="状态">{{ invoiceStatusLabel(invoice.status) }}</el-descriptions-item>
                  <el-descriptions-item label="申请时间">{{ formatDateTime(invoice.created_at) }}</el-descriptions-item>
                  <el-descriptions-item label="金额">{{ money(invoice.amount) }}</el-descriptions-item>
                  <el-descriptions-item label="抬头">{{ invoice.title }}</el-descriptions-item>
                  <el-descriptions-item label="备注">{{ invoice.remark || '暂无' }}</el-descriptions-item>
                </el-descriptions>
                <AttachmentList :files="invoice.attachments || []" />
              </section>
            </div>
            <p v-else class="empty-text">暂无发票申请</p>
          </article>

          <article class="related-card wide">
            <div class="related-card-head">
              <strong>售后记录</strong>
              <span>{{ (orderRelated?.after_sales_requests || []).length }} 条</span>
            </div>
            <div v-if="orderRelated?.after_sales_requests?.length" class="related-list">
              <section v-for="afterSales in orderRelated.after_sales_requests" :key="afterSales.id" class="related-record">
                <el-descriptions border :column="2" size="small">
                  <el-descriptions-item label="售后单号">{{ afterSales.request_no }}</el-descriptions-item>
                  <el-descriptions-item label="状态">{{ afterSalesStatusLabel(afterSales.status) }}</el-descriptions-item>
                  <el-descriptions-item label="类型">{{ afterSalesTypeLabel(afterSales.type) }}</el-descriptions-item>
                  <el-descriptions-item label="申请时间">{{ formatDateTime(afterSales.created_at) }}</el-descriptions-item>
                  <el-descriptions-item label="问题说明">{{ afterSales.description }}</el-descriptions-item>
                  <el-descriptions-item label="处理说明">{{ afterSales.solution || '暂无' }}</el-descriptions-item>
                </el-descriptions>
                <AttachmentList :files="afterSales.attachments || []" />
              </section>
            </div>
            <p v-else class="empty-text">暂无售后记录</p>
          </article>
        </div>
      </div>

      <div class="detail-section">
        <h3>后续事项</h3>
        <div class="actions drawer-actions">
          <el-button type="primary" plain @click="openInvoiceDialog">申请发票</el-button>
          <el-button type="warning" plain @click="openAfterSalesDialog">申请售后</el-button>
        </div>
      </div>
    </section>
  </el-drawer>

  <el-dialog v-model="invoiceVisible" title="申请发票" width="min(560px, 94vw)">
    <el-form label-position="top" :model="invoiceForm">
      <el-form-item label="发票类型">
        <el-select v-model="invoiceForm.invoice_type" style="width: 100%">
          <el-option label="普票" value="normal" />
          <el-option label="专票" value="special" />
        </el-select>
      </el-form-item>
      <el-form-item label="发票金额">
        <el-input-number v-model="invoiceForm.amount" :min="0" :precision="2" style="width: 100%" />
      </el-form-item>
      <el-form-item label="发票抬头">
        <el-input v-model="invoiceForm.title" placeholder="填写发票抬头" />
      </el-form-item>
      <el-form-item label="税号">
        <el-input v-model="invoiceForm.tax_number" placeholder="专票或需要税号时填写" />
      </el-form-item>
      <el-form-item label="备注说明">
        <el-input v-model="invoiceForm.remark" type="textarea" :rows="3" placeholder="填写开票要求、邮寄说明或其他备注" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="invoiceVisible = false">取消</el-button>
      <el-button type="primary" @click="submitInvoiceRequest">提交申请</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="afterSalesVisible" title="申请售后" width="min(560px, 94vw)">
    <el-form label-position="top" :model="afterSalesForm">
      <el-form-item label="售后类型">
        <el-select v-model="afterSalesForm.type" style="width: 100%">
          <el-option label="退款" value="refund" />
          <el-option label="补发" value="reship" />
          <el-option label="返修" value="repair" />
          <el-option label="投诉" value="complaint" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>
      <el-form-item label="退款金额">
        <el-input-number v-model="afterSalesForm.refund_amount" :min="0" :precision="2" style="width: 100%" />
      </el-form-item>
      <el-form-item label="问题说明">
        <el-input v-model="afterSalesForm.description" type="textarea" :rows="4" placeholder="填写客户反馈、问题描述和期望处理方式" />
      </el-form-item>
      <el-form-item label="证据附件">
        <el-upload v-model:file-list="afterSalesFiles" action="#" :auto-upload="false" multiple drag>
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽问题图片或文件到此处，或点击添加</div>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="afterSalesVisible = false">取消</el-button>
      <el-button type="primary" @click="submitAfterSalesRequest">提交申请</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { api, list } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { dateRangeShortcuts } from '../utils/dateShortcuts'

const auth = useAuthStore()
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const dateRange = ref<string[]>([])
const detailVisible = ref(false)
const invoiceVisible = ref(false)
const afterSalesVisible = ref(false)
const afterSalesFiles = ref<any[]>([])
const currentOrder = ref<any>(null)
const orderRelated = ref<any>(null)
const summary = reactive({ order_count: 0, total_amount: '0.00' })
const filters = reactive({ keyword: '', status: '' })
const invoiceForm = reactive({
  invoice_type: 'normal',
  amount: 0,
  title: '',
  tax_number: '',
  remark: ''
})
const afterSalesForm = reactive({
  type: 'refund',
  refund_amount: 0,
  description: ''
})
const isAdmin = computed(() => Boolean(auth.user?.is_superuser || auth.user?.groups?.some((group) => group.name === '管理员')))

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
  const [data, summaryResponse] = await Promise.all([
    list<any>('/orders', { page: page.value, page_size: 20, ...params }),
    api.get('/orders/summary/', { params })
  ])
  rows.value = data.results
  total.value = data.count
  Object.assign(summary, summaryResponse.data)
}

async function search() {
  page.value = 1
  await load()
}

async function resetFilters() {
  filters.keyword = ''
  filters.status = ''
  dateRange.value = []
  await search()
}

async function openDetail(id: string) {
  orderRelated.value = null
  const [orderResponse, relatedResponse] = await Promise.all([
    api.get(`/orders/${id}/`),
    api.get(`/orders/${id}/related/`)
  ])
  currentOrder.value = orderResponse.data
  orderRelated.value = relatedResponse.data
  detailVisible.value = true
}

function openInvoiceDialog() {
  if (!currentOrder.value) return
  invoiceForm.invoice_type = 'normal'
  invoiceForm.amount = Number(currentOrder.value.total_amount || 0)
  invoiceForm.title = currentOrder.value.customer_info?.invoice_title || currentOrder.value.customer_info?.company || currentOrder.value.customer_info?.name || ''
  invoiceForm.tax_number = currentOrder.value.customer_info?.tax_number || ''
  invoiceForm.remark = ''
  invoiceVisible.value = true
}

async function submitInvoiceRequest() {
  if (!currentOrder.value) return
  if (!invoiceForm.title.trim()) {
    ElMessage.warning('请填写发票抬头')
    return
  }
  await api.post('/invoice-requests/', {
    order: currentOrder.value.id,
    customer: currentOrder.value.customer,
    invoice_type: invoiceForm.invoice_type,
    amount: invoiceForm.amount,
    title: invoiceForm.title.trim(),
    tax_number: invoiceForm.tax_number.trim(),
    remark: invoiceForm.remark.trim()
  })
  ElMessage.success('发票申请已提交')
  invoiceVisible.value = false
}

function openAfterSalesDialog() {
  afterSalesForm.type = 'refund'
  afterSalesForm.refund_amount = 0
  afterSalesForm.description = ''
  afterSalesFiles.value = []
  afterSalesVisible.value = true
}

async function submitAfterSalesRequest() {
  if (!currentOrder.value) return
  if (!afterSalesForm.description.trim()) {
    ElMessage.warning('请填写售后问题说明')
    return
  }
  const response = await api.post('/after-sales-requests/', {
    order: currentOrder.value.id,
    type: afterSalesForm.type,
    refund_amount: afterSalesForm.refund_amount || null,
    description: afterSalesForm.description.trim()
  })
  await uploadAfterSalesFiles(response.data.id)
  ElMessage.success('售后申请已提交')
  afterSalesVisible.value = false
}

async function uploadAfterSalesFiles(afterSalesId: string) {
  const files = afterSalesFiles.value.filter((file) => file.raw)
  for (const file of files) {
    const formData = new FormData()
    formData.append('file', file.raw)
    formData.append('business_type', 'after_sales')
    formData.append('business_id', afterSalesId)
    await api.post('/attachments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
  afterSalesFiles.value = []
}

async function deleteOrder(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除订单 ${row.order_no}？`, '删除订单', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  await api.delete(`/orders/${row.id}/`)
  ElMessage.success('订单已删除')
  if (rows.value.length === 1 && page.value > 1) page.value -= 1
  await load()
}

function money(value: string | number | null | undefined) {
  return `¥${Number(value || 0).toFixed(2)}`
}

const AttachmentList = defineComponent({
  props: {
    files: { type: Array, required: true }
  },
  setup(props) {
    return () => {
      const files = props.files as any[]
      if (!files.length) return h('p', { class: 'empty-text' }, '暂无附件')
      return h(
        'div',
        { class: 'attachment-list' },
        files.map((file) =>
          h(
            'a',
            {
              key: file.id,
              href: file.file_url,
              target: '_blank',
              rel: 'noreferrer'
            },
            `${file.file_name} · ${formatDateTime(file.created_at)}`
          )
        )
      )
    }
  }
})

function attachmentCount(files: any[] | null | undefined) {
  return `${files?.length || 0} 个附件`
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  const pad = (number: number) => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function statusLabel(status: string) {
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

function designTaskStatusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: '待领取',
    designing: '设计中',
    waiting_confirmation: '待确认',
    needs_changes: '需修改',
    confirmed: '已确认'
  }
  return labels[status] || status
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

function invoiceStatusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: '草稿',
    pending: '待审批',
    approved: '已通过',
    rejected: '已驳回',
    withdrawn: '已撤回'
  }
  return labels[status] || status
}

function afterSalesStatusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: '待受理',
    processing: '处理中',
    completed: '已完成',
    closed: '已关闭'
  }
  return labels[status] || status
}

function afterSalesTypeLabel(type: string) {
  const labels: Record<string, string> = {
    refund: '退款',
    reship: '补发',
    repair: '返修',
    complaint: '投诉',
    other: '其他'
  }
  return labels[type] || type
}

function paymentStatusLabel(status: string) {
  const labels: Record<string, string> = {
    unpaid: '未收款',
    partial: '部分收款',
    paid: '已收款'
  }
  return labels[status] || status
}

onMounted(async () => {
  await auth.loadMe()
  await load()
})
</script>
