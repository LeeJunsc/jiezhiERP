<template>
  <section class="panel">
    <div class="panel-head">
      <h2>新建订单</h2>
      <div class="actions mobile-action-bar">
        <el-button :icon="ArrowLeft" @click="$router.push('/orders')">取消</el-button>
        <el-button type="primary" :icon="Promotion" :loading="submitting" @click="submitOrder">提交订单</el-button>
      </div>
    </div>
    <el-form label-position="top" :model="form">
      <div class="order-form">
        <section class="form-block">
          <div class="form-block-head">
            <h3>客户</h3>
            <el-button type="primary" @click="customerDialogVisible = true">新建客户</el-button>
          </div>
          <el-form-item label="选择客户">
            <el-select
              v-model="form.customer"
              filterable
              remote
              clearable
              reserve-keyword
              placeholder="输入客户名称、手机号、公司或标签筛选"
              :remote-method="searchCustomers"
              :loading="customerLoading"
            >
              <el-option
                v-for="customer in customers"
                :key="customer.id"
                :label="customerLabel(customer)"
                :value="customer.id"
              />
            </el-select>
          </el-form-item>
        </section>

        <section class="form-block">
          <h3>订单号</h3>
          <div class="form-grid">
            <el-form-item label="平台订单号"><el-input v-model="form.platform_order_no" placeholder="请输入平台订单号" /></el-form-item>
            <el-form-item label="系统单据号"><el-input :model-value="systemOrderNo" disabled /></el-form-item>
          </div>
        </section>

        <section class="form-block">
          <h3>来源</h3>
          <div class="form-grid">
            <el-form-item label="来源店铺">
              <el-select v-model="form.store">
                <el-option v-for="store in stores" :key="store.id" :label="storeLabel(store)" :value="store.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="销售负责人"><el-input :model-value="auth.user?.first_name || auth.user?.username" disabled /></el-form-item>
          </div>
        </section>

        <section class="form-block">
          <div class="form-block-head">
            <h3>产品</h3>
            <el-button type="primary" plain @click="addProduct">添加产品 / SKU</el-button>
          </div>
          <el-table :data="items" border size="small" row-key="local_id" class="product-table">
            <el-table-column label="商品名称" min-width="220">
              <template #default="{ row }"><el-input v-model="row.product_name" /></template>
            </el-table-column>
            <el-table-column label="SKU" min-width="160">
              <template #default="{ row }"><el-input v-model="row.sku" /></template>
            </el-table-column>
            <el-table-column label="数量" width="130">
              <template #default="{ row }"><el-input-number v-model="row.quantity" :min="1" controls-position="right" /></template>
            </el-table-column>
            <el-table-column label="单价" width="140">
              <template #default="{ row }"><el-input-number v-model="row.unit_price" :min="0" :precision="2" controls-position="right" /></template>
            </el-table-column>
            <el-table-column label="小计" width="110">
              <template #default="{ row }">{{ productLineAmount(row).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="" width="80">
              <template #default="{ row }">
                <el-button text type="danger" :disabled="items.length === 1" @click="removeProduct(row.local_id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="form-block">
          <h3>订单金额</h3>
          <div class="form-grid">
            <el-form-item label="订单金额"><el-input-number v-model="form.total_amount" :min="0" :precision="2" /></el-form-item>
            <el-form-item label="已收金额"><el-input-number v-model="form.paid_amount" :min="0" :precision="2" /></el-form-item>
            <el-form-item label="付款状态">
              <el-select v-model="form.payment_status">
                <el-option label="未收款" value="unpaid" />
                <el-option label="部分收款" value="partial" />
                <el-option label="已收款" value="paid" />
              </el-select>
            </el-form-item>
            <el-form-item label="收款渠道">
              <el-select v-model="form.payment_channel">
                <el-option v-for="channel in paymentChannels" :key="channel.id" :label="channel.name" :value="channel.id" />
              </el-select>
            </el-form-item>
          </div>
        </section>

        <section class="form-block">
          <h3>设计</h3>
          <div class="form-grid">
            <el-form-item label="设计处理方式">
              <el-select v-model="form.design_option">
                <el-option v-for="option in designOptions" :key="option.id" :label="option.name" :value="option.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="加急"><el-switch v-model="form.urgent" /></el-form-item>
          </div>
        </section>

        <section class="form-block">
          <h3>订单说明</h3>
          <div class="form-grid">
            <el-form-item class="wide" label="定制说明"><el-input v-model="form.customization_note" type="textarea" :rows="4" /></el-form-item>
            <el-form-item class="wide" label="内部备注"><el-input v-model="form.remark" type="textarea" :rows="4" /></el-form-item>
          </div>
        </section>

        <section class="form-block">
          <h3>收货信息</h3>
          <div class="form-grid">
            <el-form-item label="收货人"><el-input v-model="shipping.receiver" /></el-form-item>
            <el-form-item label="联系电话"><el-input v-model="shipping.phone" /></el-form-item>
            <el-form-item class="wide" label="收货地址"><el-input v-model="shipping.address" type="textarea" :rows="3" /></el-form-item>
          </div>
        </section>

        <section class="form-block">
          <h3>设计稿</h3>
          <el-upload
            v-model:file-list="draftFiles"
            action="#"
            :auto-upload="false"
            multiple
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处，或点击添加文件 / 图片</div>
          </el-upload>
        </section>
      </div>
    </el-form>
  </section>

  <el-dialog v-model="customerDialogVisible" title="新建客户" width="720px" destroy-on-close>
    <el-form label-position="top" :model="customerForm">
      <div class="form-grid">
        <el-form-item label="客户名称"><el-input v-model="customerForm.name" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="customerForm.source" placeholder="淘宝 / 抖音 / 小红书 / 线下" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="customerForm.phone" /></el-form-item>
        <el-form-item label="公司"><el-input v-model="customerForm.company" /></el-form-item>
        <el-form-item label="微信"><el-input v-model="customerForm.wechat" /></el-form-item>
        <el-form-item label="WhatsApp"><el-input v-model="customerForm.whatsapp" /></el-form-item>
        <el-form-item label="Line"><el-input v-model="customerForm.line" /></el-form-item>
        <el-form-item label="标签"><el-input v-model="customerForm.tags" placeholder="复购,企业客户,加急" /></el-form-item>
      </div>
    </el-form>
    <template #footer>
      <el-button :icon="Close" @click="customerDialogVisible = false">取消</el-button>
      <el-button type="primary" :icon="Check" @click="saveCustomer">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check, Close, Promotion, UploadFilled } from '@element-plus/icons-vue'
import { api, create, list } from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const stores = ref<any[]>([])
const customers = ref<any[]>([])
const designOptions = ref<any[]>([])
const paymentChannels = ref<any[]>([])
const customerLoading = ref(false)
const customerDialogVisible = ref(false)
const draftFiles = ref<any[]>([])
const submitting = ref(false)
const items = ref([
  { local_id: 1, product_name: '定制亚克力展示架', sku: '', quantity: 1, unit_price: 0 }
])
let nextItemId = 2
const form = reactive<any>({
  order_no: '',
  platform_order_no: '',
  store: '',
  customer: '',
  salesperson: '',
  design_option: '',
  total_amount: 0,
  paid_amount: 0,
  payment_status: 'paid',
  payment_channel: '',
  urgent: false,
  customization_note: '',
  remark: ''
})
const shipping = reactive({ receiver: '', phone: '', address: '' })
const customerForm = reactive({
  name: '',
  source: '',
  phone: '',
  company: '',
  wechat: '',
  whatsapp: '',
  line: '',
  tags: ''
})
const systemOrderNo = computed(() => form.order_no || '提交时自动生成')
const itemsTotal = computed(() => items.value.reduce((sum, row) => sum + productLineAmount(row), 0))
const localDraftKey = 'jiezhi.newOrder.localDraft'
let restoringLocalDraft = false

onMounted(async () => {
  restoringLocalDraft = true
  await auth.loadMe()
  form.salesperson = auth.user?.id
  stores.value = (await list<any>('/stores', { status: 'enabled' })).results
  await searchCustomers('')
  designOptions.value = (await list<any>('/design-options', { status: 'enabled' })).results
  paymentChannels.value = (await list<any>('/payment-channels', { status: 'enabled' })).results
  form.store = stores.value[0]?.id
  form.customer = customers.value[0]?.id
  form.design_option = designOptions.value[0]?.id
  form.payment_channel = paymentChannels.value.find((channel) => channel.is_default)?.id || paymentChannels.value[0]?.id
  restoreLocalDraft()
  restoringLocalDraft = false
})

watch(
  () => form.customer,
  (customerId) => {
    if (restoringLocalDraft) return
    const customer = customers.value.find((item) => item.id === customerId)
    if (!customer) return
    shipping.receiver = customer.name
    shipping.phone = customer.phone
    shipping.address = customer.address || ''
  }
)

watch(
  items,
  () => {
    if (restoringLocalDraft) return
    form.total_amount = Number(itemsTotal.value.toFixed(2))
    if (form.payment_status === 'paid') {
      form.paid_amount = form.total_amount
    }
  },
  { deep: true }
)

watch(
  [form, shipping, items],
  () => {
    if (restoringLocalDraft) return
    saveLocalDraft()
  },
  { deep: true }
)

watch(
  () => form.payment_status,
  (status) => {
    if (status === 'paid') {
      form.paid_amount = form.total_amount
    }
  }
)

function customerLabel(customer: any) {
  const company = customer.company ? ` / ${customer.company}` : ''
  const phone = customer.phone ? ` / ${customer.phone}` : ''
  return `${customer.name}${company}${phone}`
}

function storeLabel(store: any) {
  const platform = store.platform_label || store.custom_platform || ''
  return platform ? `${store.name} / ${platform}` : store.name
}

function addProduct() {
  items.value.push({ local_id: nextItemId++, product_name: '', sku: '', quantity: 1, unit_price: 0 })
}

async function removeProduct(localId: number) {
  if (items.value.length === 1) return
  try {
    await ElMessageBox.confirm('确认删除该产品 / SKU？', '删除产品', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
  } catch {
    return
  }
  items.value = items.value.filter((row) => row.local_id !== localId)
}

function productLineAmount(row: any) {
  return Number(row.quantity || 0) * Number(row.unit_price || 0)
}

async function searchCustomers(keyword: string) {
  customerLoading.value = true
  try {
    customers.value = (await list<any>('/customers', { keyword, page_size: 20 })).results
  } finally {
    customerLoading.value = false
  }
}

async function saveCustomer() {
  if (!customerForm.name) return ElMessage.warning('请填写客户名称')
  const customer = await create<any>('/customers/', customerForm)
  await searchCustomers(customer.name)
  form.customer = customer.id
  shipping.receiver = customer.name
  shipping.phone = customer.phone
  shipping.address = customer.address || ''
  Object.assign(customerForm, {
    name: '',
    source: '',
    phone: '',
    company: '',
    wechat: '',
    whatsapp: '',
    line: '',
    tags: ''
  })
  customerDialogVisible.value = false
  ElMessage.success('客户已创建')
}

function buildOrderPayload() {
  const orderItems = items.value
    .filter((row) => row.product_name || row.sku)
    .map((row) => ({
      product_name: row.product_name || row.sku,
      sku: row.sku,
      quantity: Number(row.quantity || 1),
      unit_price: Number(row.unit_price || 0),
      line_amount: productLineAmount(row)
    }))
  if (!form.customer) {
    ElMessage.warning('请选择客户')
    return null
  }
  if (!form.store) {
    ElMessage.warning('请选择来源店铺')
    return null
  }
  if (!form.design_option) {
    ElMessage.warning('请选择设计处理方式')
    return null
  }
  if (!orderItems.length) {
    ElMessage.warning('请至少填写一个产品')
    return null
  }
  const totalAmount = Number(form.total_amount || itemsTotal.value || 0)
  return {
    ...form,
    order_no: undefined,
    total_amount: totalAmount,
    paid_amount: form.payment_status === 'paid' && !Number(form.paid_amount) ? totalAmount : form.paid_amount,
    remark: [form.remark, shipping.receiver ? `收货人：${shipping.receiver}` : '', shipping.phone ? `联系电话：${shipping.phone}` : '', shipping.address ? `收货地址：${shipping.address}` : '', draftFiles.value.length ? `设计稿附件：${draftFiles.value.map((file) => file.name).join('、')}` : '']
      .filter(Boolean)
      .join('\n'),
    items: orderItems
  }
}

async function createOrder() {
  const payload = buildOrderPayload()
  if (!payload) return null
  const order = await create<any>('/orders/', payload)
  await uploadDraftFiles(order.id)
  return order
}

async function uploadDraftFiles(orderId: string) {
  if (!draftFiles.value.length) return
  for (const file of draftFiles.value) {
    if (!file.raw) continue
    const formData = new FormData()
    formData.append('file', file.raw)
    formData.append('business_type', 'order')
    formData.append('business_id', orderId)
    await api.post('/attachments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

async function submitOrder() {
  if (submitting.value) return
  submitting.value = true
  try {
    const order = await createOrder()
    if (!order) return
    await api.post(`/orders/${order.id}/submit/`)
    clearLocalDraft()
    ElMessage.success('订单已提交')
    router.push(`/orders/${order.id}`)
  } catch (error: any) {
    const detail = error?.response?.data
    const message = detail?.platform_order_no?.[0] || detail?.message || detail?.detail || '订单提交失败，请检查填写内容'
    ElMessage.error(message)
  } finally {
    submitting.value = false
  }
}

function saveLocalDraft() {
  const payload = {
    form: { ...form },
    shipping: { ...shipping },
    items: items.value.map((item) => ({ ...item })),
    nextItemId
  }
  window.localStorage.setItem(localDraftKey, JSON.stringify(payload))
}

function restoreLocalDraft() {
  const raw = window.localStorage.getItem(localDraftKey)
  if (!raw) return
  try {
    const draft = JSON.parse(raw)
    if (draft?.form) Object.assign(form, draft.form)
    if (draft?.shipping) Object.assign(shipping, draft.shipping)
    if (Array.isArray(draft?.items) && draft.items.length) items.value = draft.items
    if (Number(draft?.nextItemId)) nextItemId = Number(draft.nextItemId)
    ElMessage.info('已恢复上次未提交的订单内容')
  } catch {
    window.localStorage.removeItem(localDraftKey)
  }
}

function clearLocalDraft() {
  window.localStorage.removeItem(localDraftKey)
}
</script>
