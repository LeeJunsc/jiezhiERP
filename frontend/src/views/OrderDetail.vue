<template>
  <section class="panel" v-if="order">
    <div class="panel-head">
      <h2>订单 {{ order.order_no }}</h2>
      <div class="actions mobile-action-bar">
        <el-button :icon="ArrowLeft" @click="$router.push('/orders')">返回</el-button>
        <el-button :icon="Close" type="danger" plain @click="cancel" :loading="cancelling" :disabled="!canCancel">取消订单</el-button>
        <el-button type="primary" :icon="Promotion" @click="submit" :loading="submitting" :disabled="order.status !== 'draft'">提交订单</el-button>
      </div>
    </div>
    <el-descriptions border :column="3">
      <el-descriptions-item label="状态">{{ order.status }}</el-descriptions-item>
      <el-descriptions-item label="店铺">{{ order.store }}</el-descriptions-item>
      <el-descriptions-item label="客户">{{ order.customer }}</el-descriptions-item>
      <el-descriptions-item label="设计处理方式">{{ order.design_option }}</el-descriptions-item>
      <el-descriptions-item label="金额">{{ order.total_amount }}</el-descriptions-item>
      <el-descriptions-item label="加急">{{ order.urgent ? '是' : '否' }}</el-descriptions-item>
    </el-descriptions>
    <el-divider />
    <h3>定制说明</h3>
    <p>{{ order.customization_note || '暂无' }}</p>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Close, Promotion } from '@element-plus/icons-vue'
import { api } from '../api/client'

const route = useRoute()
const order = ref<any>(null)
const submitting = ref(false)
const cancelling = ref(false)
const canCancel = ref(false)

async function load() {
  const response = await api.get(`/orders/${route.params.id}/`)
  order.value = response.data
  canCancel.value = !['completed', 'cancelled'].includes(order.value.status)
}

async function submit() {
  if (submitting.value) return
  submitting.value = true
  try {
    await api.post(`/orders/${route.params.id}/submit/`)
    ElMessage.success('订单已提交')
    await load()
  } finally {
    submitting.value = false
  }
}

async function cancel() {
  if (cancelling.value || !canCancel.value) return
  cancelling.value = true
  try {
    await api.post(`/orders/${route.params.id}/cancel/`)
    ElMessage.success('订单已取消')
    await load()
  } finally {
    cancelling.value = false
  }
}

onMounted(load)
</script>
