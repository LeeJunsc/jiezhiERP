<template>
  <section class="panel">
    <div class="panel-head">
      <h2>系统管理</h2>
      <el-button @click="loadAll">刷新</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="店铺" name="stores">
        <el-form inline :model="storeForm">
          <el-form-item label="店铺名"><el-input v-model="storeForm.name" /></el-form-item>
          <el-form-item label="平台">
            <el-select v-model="storeForm.platform" style="width: 150px">
              <el-option label="淘宝" value="taobao" />
              <el-option label="拼多多" value="pinduoduo" />
              <el-option label="抖音" value="douyin" />
              <el-option label="小红书" value="xiaohongshu" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item><el-button type="primary" @click="createStore">新建店铺</el-button></el-form-item>
        </el-form>
        <el-table :data="stores" border>
          <el-table-column prop="name" label="店铺" />
          <el-table-column prop="platform" label="平台" />
          <el-table-column prop="status" label="状态" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="设计处理方式" name="design">
        <el-form inline :model="designForm">
          <el-form-item label="名称"><el-input v-model="designForm.name" /></el-form-item>
          <el-form-item label="生成设计任务"><el-switch v-model="designForm.requires_design" /></el-form-item>
          <el-form-item label="排序"><el-input-number v-model="designForm.sort_order" :min="0" /></el-form-item>
          <el-form-item><el-button type="primary" @click="createDesignOption">新增</el-button></el-form-item>
        </el-form>
        <el-table :data="designOptions" border>
          <el-table-column prop="name" label="名称" />
          <el-table-column label="需要设计任务">
            <template #default="{ row }">{{ row.requires_design ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="100" />
          <el-table-column prop="status" label="状态" width="120" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="收款渠道" name="payments">
        <el-form inline :model="channelForm">
          <el-form-item label="名称"><el-input v-model="channelForm.name" /></el-form-item>
          <el-form-item label="编码"><el-input v-model="channelForm.code" placeholder="英文或拼音" /></el-form-item>
          <el-form-item label="默认"><el-switch v-model="channelForm.is_default" /></el-form-item>
          <el-form-item label="排序"><el-input-number v-model="channelForm.sort_order" :min="0" /></el-form-item>
          <el-form-item><el-button type="primary" @click="createChannel">新增渠道</el-button></el-form-item>
        </el-form>
        <el-table :data="paymentChannels" border>
          <el-table-column prop="name" label="渠道" />
          <el-table-column prop="code" label="编码" />
          <el-table-column label="默认" width="100">
            <template #default="{ row }">{{ row.is_default ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="100" />
          <el-table-column prop="status" label="状态" width="120" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="用户权限" name="users">
        <el-table :data="users" border>
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="first_name" label="姓名" />
          <el-table-column label="角色">
            <template #default="{ row }">{{ roleNames(row.groups) }}</template>
          </el-table-column>
          <el-table-column label="启用" width="100">
            <template #default="{ row }">{{ row.is_active ? '是' : '否' }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { create, list } from '../api/client'

const activeTab = ref('stores')
const stores = ref<any[]>([])
const designOptions = ref<any[]>([])
const paymentChannels = ref<any[]>([])
const users = ref<any[]>([])

const storeForm = reactive({ name: '', platform: 'taobao', status: 'enabled' })
const designForm = reactive({ name: '', requires_design: true, sort_order: 50, status: 'enabled', description: '' })
const channelForm = reactive({ name: '', code: '', is_default: false, sort_order: 70, status: 'enabled', description: '' })

function roleNames(groups: Array<{ name: string }>) {
  return groups.map((item) => item.name).join('、') || '未分配'
}

async function loadAll() {
  const [storePage, designPage, channelPage, userPage] = await Promise.all([
    list<any>('/stores'),
    list<any>('/design-options'),
    list<any>('/payment-channels'),
    list<any>('/users')
  ])
  stores.value = storePage.results
  designOptions.value = designPage.results
  paymentChannels.value = channelPage.results
  users.value = userPage.results
}

async function createStore() {
  if (!storeForm.name) return ElMessage.warning('请填写店铺名')
  await create('/stores/', storeForm)
  storeForm.name = ''
  ElMessage.success('店铺已创建')
  await loadAll()
}

async function createDesignOption() {
  if (!designForm.name) return ElMessage.warning('请填写名称')
  await create('/design-options/', designForm)
  designForm.name = ''
  ElMessage.success('设计处理方式已创建')
  await loadAll()
}

async function createChannel() {
  if (!channelForm.name || !channelForm.code) return ElMessage.warning('请填写渠道名称和编码')
  await create('/payment-channels/', channelForm)
  Object.assign(channelForm, { name: '', code: '', is_default: false, sort_order: channelForm.sort_order + 10 })
  ElMessage.success('收款渠道已创建')
  await loadAll()
}

onMounted(loadAll)
</script>
