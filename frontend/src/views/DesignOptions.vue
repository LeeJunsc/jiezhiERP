<template>
  <section class="panel">
    <div class="panel-head"><h2>设计处理方式</h2><el-button type="primary" @click="createOption">新增选项</el-button></div>
    <el-form inline :model="form">
      <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="生成设计任务"><el-switch v-model="form.requires_design" /></el-form-item>
      <el-form-item label="排序"><el-input-number v-model="form.sort_order" /></el-form-item>
    </el-form>
    <el-table :data="rows" border>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="requires_design" label="需要设计任务">
        <template #default="{ row }">{{ row.requires_design ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" />
      <el-table-column prop="status" label="状态" />
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { create, list } from '../api/client'

const rows = ref<any[]>([])
const form = reactive({ name: '', requires_design: true, sort_order: 50, status: 'enabled', description: '' })

async function load() {
  rows.value = (await list<any>('/design-options')).results
}
async function createOption() {
  if (!form.name) return ElMessage.warning('请填写名称')
  await create('/design-options/', form)
  form.name = ''
  ElMessage.success('设计处理方式已创建')
  await load()
}
onMounted(load)
</script>
