<template>
  <section class="panel">
    <div class="panel-head">
      <h2>客户管理</h2>
      <div class="actions">
        <el-button v-if="isAdmin" type="danger" plain :disabled="!selectedRows.length" @click="deleteSelected">删除选中</el-button>
        <el-button type="primary" @click="openCreateDialog">新建客户</el-button>
      </div>
    </div>

    <el-form inline :model="filters" class="search-bar">
      <el-form-item label="搜索">
        <el-input v-model="filters.keyword" clearable placeholder="客户名称 / 来源 / 手机 / 公司 / 微信 / 标签" @keyup.enter="search" />
      </el-form-item>
      <el-button type="primary" @click="search">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </el-form>

    <el-table :data="rows" border @selection-change="selectedRows = $event">
      <el-table-column v-if="isAdmin" type="selection" width="48" />
      <el-table-column prop="name" label="客户" min-width="120" />
      <el-table-column prop="source" label="来源" min-width="100" />
      <el-table-column prop="company" label="公司" min-width="150" />
      <el-table-column prop="phone" label="手机" min-width="130" />
      <el-table-column prop="wechat" label="微信" min-width="120" />
      <el-table-column prop="whatsapp" label="WhatsApp" min-width="130" />
      <el-table-column prop="line" label="Line" min-width="120" />
      <el-table-column prop="tags" label="标签" min-width="160" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
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

  <el-dialog v-model="dialogVisible" :title="editingId ? '编辑客户' : '新建客户'" width="720px" destroy-on-close>
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
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="saveCustomer">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, create, list } from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const rows = ref<any[]>([])
const selectedRows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref('')
const filters = reactive({ keyword: '' })
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
const isAdmin = computed(() => Boolean(auth.user?.is_superuser || auth.user?.groups?.some((group) => group.name === '管理员')))

async function load() {
  const data = await list<any>('/customers', { page: page.value, page_size: 20, keyword: filters.keyword })
  rows.value = data.results
  total.value = data.count
  selectedRows.value = []
}

async function search() {
  page.value = 1
  await load()
}

async function resetFilters() {
  filters.keyword = ''
  await search()
}

function resetForm() {
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
}

function openCreateDialog() {
  editingId.value = ''
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(row: any) {
  editingId.value = row.id
  Object.assign(customerForm, {
    name: row.name || '',
    source: row.source || '',
    phone: row.phone || '',
    company: row.company || '',
    wechat: row.wechat || '',
    whatsapp: row.whatsapp || '',
    line: row.line || '',
    tags: row.tags || ''
  })
  dialogVisible.value = true
}

async function saveCustomer() {
  if (!customerForm.name) return ElMessage.warning('请填写客户名称')
  saving.value = true
  try {
    if (editingId.value) {
      await api.patch(`/customers/${editingId.value}/`, customerForm)
      ElMessage.success('客户已更新')
    } else {
      await create('/customers/', customerForm)
      ElMessage.success('客户已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function deleteSelected() {
  if (!selectedRows.value.length) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${selectedRows.value.length} 个客户？`, '删除客户', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  const failed: string[] = []
  for (const row of selectedRows.value) {
    try {
      await api.delete(`/customers/${row.id}/`)
    } catch {
      failed.push(row.name)
    }
  }
  if (failed.length) {
    ElMessage.warning(`${failed.length} 个客户未删除，可能已有订单记录`)
  } else {
    ElMessage.success('客户已删除')
  }
  if (rows.value.length === selectedRows.value.length && page.value > 1) page.value -= 1
  await load()
}

onMounted(async () => {
  await auth.loadMe()
  await load()
})
</script>
