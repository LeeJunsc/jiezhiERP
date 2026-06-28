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

  <el-drawer v-model="detailVisible" size="min(760px, 100vw)" :with-header="false" destroy-on-close>
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
    </section>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, list } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { dateRangeShortcuts } from '../utils/dateShortcuts'

const auth = useAuthStore()
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const dateRange = ref<string[]>([])
const detailVisible = ref(false)
const currentOrder = ref<any>(null)
const summary = reactive({ order_count: 0, total_amount: '0.00' })
const filters = reactive({ keyword: '', status: '' })
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
  const response = await api.get(`/orders/${id}/`)
  currentOrder.value = response.data
  detailVisible.value = true
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
