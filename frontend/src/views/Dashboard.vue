<template>
  <div>
    <section class="metric-grid">
      <article class="metric"><span>订单总数</span><strong>{{ metrics.orders }}</strong></article>
      <article class="metric"><span>待设计</span><strong>{{ metrics.design }}</strong></article>
      <article class="metric"><span>待生产安排</span><strong>{{ metrics.production }}</strong></article>
      <article class="metric"><span>已完成</span><strong>{{ metrics.completed }}</strong></article>
      <article class="metric"><span>当天订单总金额</span><strong>¥{{ metrics.todayAmount }}</strong></article>
      <article class="metric"><span>当天订单数</span><strong>{{ metrics.todayCount }}</strong></article>
      <article class="metric"><span>售后未处理</span><strong>{{ metrics.pendingAfterSales }}</strong></article>
      <article class="metric"><span>发票待处理</span><strong>{{ metrics.pendingInvoices }}</strong></article>
    </section>
    <section class="panel">
      <div class="panel-head">
        <h2>最近订单</h2>
        <el-button type="primary" @click="$router.push('/orders/new')">新建订单</el-button>
      </div>
      <el-table :data="orders" border>
        <el-table-column prop="order_no" label="订单号" width="160" />
        <el-table-column prop="customer.name" label="客户" />
        <el-table-column prop="store.name" label="店铺" />
        <el-table-column prop="status" label="状态" />
        <el-table-column prop="total_amount" label="金额" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api/client'

const orders = ref<any[]>([])
const metrics = reactive({
  orders: 0,
  design: 0,
  production: 0,
  completed: 0,
  todayAmount: '0.00',
  todayCount: 0,
  pendingAfterSales: 0,
  pendingInvoices: 0
})

onMounted(async () => {
  const response = await api.get('/dashboard/summary')
  const data = response.data
  orders.value = data.recent_orders
  metrics.orders = data.orders
  metrics.design = data.pending_design
  metrics.production = data.pending_production
  metrics.completed = data.completed
  metrics.todayAmount = data.today_order_amount
  metrics.todayCount = data.today_order_count
  metrics.pendingAfterSales = data.pending_after_sales
  metrics.pendingInvoices = data.pending_invoices
})
</script>
