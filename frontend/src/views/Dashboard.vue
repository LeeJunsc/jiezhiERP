<template>
  <div>
    <section class="panel">
      <div class="panel-head">
        <div class="panel-title">
          <h2>经营看板</h2>
          <small>{{ data?.start_date }} 至 {{ data?.end_date }}</small>
        </div>
        <el-date-picker
          v-model="range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          :shortcuts="dateRangeShortcuts"
          @change="load"
        />
      </div>
      <section class="metric-grid dashboard-metric-grid">
        <article
          v-for="metric in metrics"
          :key="metric.key"
          class="metric metric-button"
          :class="{ active: activeMetric === metric.key }"
          role="button"
          tabindex="0"
          @click="activeMetric = metric.key"
          @keydown.enter="activeMetric = metric.key"
        >
          <span>{{ metric.label }}</span>
          <strong>{{ metric.summaryValue() }}</strong>
        </article>
      </section>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2>{{ activeMetricConfig.label }}趋势</h2>
        <span>{{ data?.start_date }} 至 {{ data?.end_date }}</span>
      </div>
      <div class="chart">
        <svg viewBox="0 0 800 280" role="img" :aria-label="`${activeMetricConfig.label}折线图`">
          <line x1="40" y1="230" x2="760" y2="230" stroke="#d8dee9" />
          <line x1="40" y1="30" x2="40" y2="230" stroke="#d8dee9" />
          <text x="44" y="46" fill="#6b7280" font-size="12">{{ activeMetricConfig.axisLabel }}</text>
          <text x="704" y="252" fill="#6b7280" font-size="12">日期</text>
          <text x="44" y="226" fill="#9ca3af" font-size="11">{{ activeMetricConfig.format(0) }}</text>
          <text x="44" y="34" fill="#9ca3af" font-size="11">{{ activeMetricConfig.format(maxMetricValue) }}</text>
          <polyline :points="chartPoints" fill="none" stroke="#2563eb" stroke-width="4" stroke-linejoin="round" stroke-linecap="round" />
          <circle v-for="point in pointList" :key="point.date" :cx="point.x" :cy="point.y" r="5" fill="#2563eb" />
        </svg>
        <div class="chart-labels">
          <span v-for="item in series" :key="item.date">{{ item.date.slice(5) }}</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head"><h2>每日明细</h2></div>
      <el-table :data="paginatedSeries" border>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="amount" label="订单金额" />
        <el-table-column prop="order_count" label="订单数" />
        <el-table-column prop="returning_customer_order_count" label="老客户订单数" />
        <el-table-column prop="after_sales_order_count" label="产生售后订单数" />
        <el-table-column prop="pending_design_order_count" label="待设计" />
        <el-table-column prop="pending_production_order_count" label="待生产" />
        <el-table-column prop="pending_invoice_count" label="待开票" />
      </el-table>
      <div class="actions">
        <el-pagination
          layout="sizes, prev, pager, next"
          :page-sizes="pageSizeOptions"
          :total="series.length"
          :page-size="dailyPageSize"
          :current-page="dailyPage"
          @size-change="handleDailyPageSizeChange"
          @current-change="dailyPage = $event"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api/client'
import { dateRangeShortcuts } from '../utils/dateShortcuts'
import { pageSizeOptions } from '../utils/pagination'

interface KanbanRow {
  date: string
  amount: string
  order_count: number
  returning_customer_order_count: number
  after_sales_order_count: number
  pending_design_order_count: number
  pending_production_order_count: number
  pending_invoice_count: number
}

const today = new Date()
const todayText = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const range = ref<[string, string]>([todayText, todayText])
const data = ref<any>(null)
const summary = reactive({
  amount: '0.00',
  order_count: 0,
  returning_customer_order_count: 0,
  after_sales_order_count: 0,
  pending_design_order_count: 0,
  pending_production_order_count: 0,
  pending_invoice_count: 0
})
const series = ref<KanbanRow[]>([])
const activeMetric = ref<MetricKey>('amount')
const dailyPage = ref(1)
const dailyPageSize = ref(20)

type MetricKey =
  | 'amount'
  | 'order_count'
  | 'returning_customer_order_count'
  | 'after_sales_order_count'
  | 'pending_design_order_count'
  | 'pending_production_order_count'
  | 'pending_invoice_count'

const metricConfigs: Record<MetricKey, {
  key: MetricKey
  label: string
  axisLabel: string
  value: (row: KanbanRow) => number
  summaryValue: () => string
  format: (value: number) => string
}> = {
  amount: {
    key: 'amount',
    label: '订单金额',
    axisLabel: '金额',
    value: (row) => Number(row.amount),
    summaryValue: () => `¥${Number(summary.amount || 0).toFixed(2)}`,
    format: (value) => `¥${Number(value || 0).toFixed(0)}`
  },
  order_count: {
    key: 'order_count',
    label: '订单数',
    axisLabel: '数量',
    value: (row) => Number(row.order_count),
    summaryValue: () => `${summary.order_count}`,
    format: (value) => `${Number(value || 0).toFixed(0)}单`
  },
  returning_customer_order_count: {
    key: 'returning_customer_order_count',
    label: '老客户订单数',
    axisLabel: '数量',
    value: (row) => Number(row.returning_customer_order_count),
    summaryValue: () => `${summary.returning_customer_order_count}`,
    format: (value) => `${Number(value || 0).toFixed(0)}单`
  },
  after_sales_order_count: {
    key: 'after_sales_order_count',
    label: '产生售后订单数',
    axisLabel: '数量',
    value: (row) => Number(row.after_sales_order_count),
    summaryValue: () => `${summary.after_sales_order_count}`,
    format: (value) => `${Number(value || 0).toFixed(0)}单`
  },
  pending_design_order_count: {
    key: 'pending_design_order_count',
    label: '待设计',
    axisLabel: '数量',
    value: (row) => Number(row.pending_design_order_count),
    summaryValue: () => `${summary.pending_design_order_count}`,
    format: (value) => `${Number(value || 0).toFixed(0)}单`
  },
  pending_production_order_count: {
    key: 'pending_production_order_count',
    label: '待生产',
    axisLabel: '数量',
    value: (row) => Number(row.pending_production_order_count),
    summaryValue: () => `${summary.pending_production_order_count}`,
    format: (value) => `${Number(value || 0).toFixed(0)}单`
  },
  pending_invoice_count: {
    key: 'pending_invoice_count',
    label: '待开票',
    axisLabel: '数量',
    value: (row) => Number(row.pending_invoice_count),
    summaryValue: () => `${summary.pending_invoice_count}`,
    format: (value) => `${Number(value || 0).toFixed(0)}单`
  }
}
const metrics = Object.values(metricConfigs)
const activeMetricConfig = computed(() => metricConfigs[activeMetric.value])
const maxMetricValue = computed(() => Math.max(...series.value.map((item) => activeMetricConfig.value.value(item)), 1))

const pointList = computed(() => {
  const count = Math.max(series.value.length - 1, 1)
  return series.value.map((item, index) => ({
    date: item.date,
    x: 40 + (720 / count) * index,
    y: 230 - (activeMetricConfig.value.value(item) / maxMetricValue.value) * 190
  }))
})
const chartPoints = computed(() => pointList.value.map((item) => `${item.x},${item.y}`).join(' '))
const paginatedSeries = computed(() => {
  const start = (dailyPage.value - 1) * dailyPageSize.value
  return series.value.slice(start, start + dailyPageSize.value)
})

function handleDailyPageSizeChange(size: number) {
  dailyPageSize.value = size
  dailyPage.value = 1
}

async function load() {
  const response = await api.get('/dashboard/kanban', {
    params: {
      start_date: range.value?.[0],
      end_date: range.value?.[1]
    }
  })
  data.value = response.data
  Object.assign(summary, response.data.summary)
  series.value = response.data.series
  dailyPage.value = 1
}

onMounted(load)
</script>
