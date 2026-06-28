<template>
  <div>
    <section class="panel">
      <div class="panel-head">
        <h2>经营看板</h2>
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
      <section class="metric-grid">
        <article class="metric"><span>订单金额</span><strong>¥{{ summary.amount }}</strong></article>
        <article class="metric"><span>订单数</span><strong>{{ summary.order_count }}</strong></article>
        <article class="metric"><span>老客户订单数</span><strong>{{ summary.returning_customer_order_count }}</strong></article>
        <article class="metric"><span>产生售后订单数</span><strong>{{ summary.after_sales_order_count }}</strong></article>
      </section>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2>订单金额趋势</h2>
        <span>{{ data?.start_date }} 至 {{ data?.end_date }}</span>
      </div>
      <div class="chart">
        <svg viewBox="0 0 800 280" role="img" aria-label="订单金额折线图">
          <line x1="40" y1="230" x2="760" y2="230" stroke="#d8dee9" />
          <line x1="40" y1="30" x2="40" y2="230" stroke="#d8dee9" />
          <polyline :points="amountPoints" fill="none" stroke="#2563eb" stroke-width="4" stroke-linejoin="round" stroke-linecap="round" />
          <circle v-for="point in pointList" :key="point.date" :cx="point.x" :cy="point.y" r="5" fill="#2563eb" />
          <text x="44" y="24" fill="#6b7280" font-size="12">金额</text>
          <text x="704" y="252" fill="#6b7280" font-size="12">日期</text>
        </svg>
        <div class="chart-labels">
          <span v-for="item in series" :key="item.date">{{ item.date.slice(5) }}</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head"><h2>每日明细</h2></div>
      <el-table :data="series" border>
        <el-table-column prop="date" label="日期" />
        <el-table-column prop="amount" label="订单金额" />
        <el-table-column prop="order_count" label="订单数" />
        <el-table-column prop="returning_customer_order_count" label="老客户订单数" />
        <el-table-column prop="after_sales_order_count" label="产生售后订单数" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api/client'
import { dateRangeShortcuts, recentDateRange } from '../utils/dateShortcuts'

interface KanbanRow {
  date: string
  amount: string
  order_count: number
  returning_customer_order_count: number
  after_sales_order_count: number
}

const range = ref<[string, string]>(recentDateRange(7))
const data = ref<any>(null)
const summary = reactive({
  amount: '0.00',
  order_count: 0,
  returning_customer_order_count: 0,
  after_sales_order_count: 0
})
const series = ref<KanbanRow[]>([])

const pointList = computed(() => {
  const max = Math.max(...series.value.map((item) => Number(item.amount)), 1)
  const count = Math.max(series.value.length - 1, 1)
  return series.value.map((item, index) => ({
    date: item.date,
    x: 40 + (720 / count) * index,
    y: 230 - (Number(item.amount) / max) * 190
  }))
})
const amountPoints = computed(() => pointList.value.map((item) => `${item.x},${item.y}`).join(' '))

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
}

onMounted(load)
</script>
