<template>
  <section class="panel">
    <div class="panel-head"><h2>店铺管理</h2><el-button type="primary" @click="createStore">新建店铺</el-button></div>
    <el-form inline :model="form">
      <el-form-item label="店铺名"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="平台">
        <el-select v-model="form.platform" style="width: 160px">
          <el-option label="淘宝" value="taobao" />
          <el-option label="拼多多" value="pinduoduo" />
          <el-option label="抖音" value="douyin" />
          <el-option label="小红书" value="xiaohongshu" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>
    </el-form>
    <el-table :data="rows" border>
      <el-table-column prop="name" label="店铺" />
      <el-table-column prop="platform" label="平台" />
      <el-table-column prop="status" label="状态" />
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { create, list } from '../api/client'

const rows = ref<any[]>([])
const form = reactive({ name: '', platform: 'taobao', status: 'enabled' })

async function load() {
  rows.value = (await list<any>('/stores')).results
}
async function createStore() {
  if (!form.name) return ElMessage.warning('请填写店铺名')
  await create('/stores/', form)
  form.name = ''
  ElMessage.success('店铺已创建')
  await load()
}
onMounted(load)
</script>
