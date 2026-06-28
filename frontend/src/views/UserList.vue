<template>
  <section class="panel">
    <div class="panel-head"><h2>用户权限</h2><el-button @click="load">刷新</el-button></div>
    <el-alert title="第一轮先支持查看用户和角色；创建用户可通过 API 或 Django 管理后台完成。" type="info" show-icon :closable="false" />
    <el-table :data="rows" border style="margin-top: 14px">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="first_name" label="姓名" />
      <el-table-column label="角色">
        <template #default="{ row }">{{ roleNames(row.groups) }}</template>
      </el-table-column>
      <el-table-column prop="is_active" label="启用">
        <template #default="{ row }">{{ row.is_active ? '是' : '否' }}</template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { list } from '../api/client'

const rows = ref<any[]>([])

function roleNames(groups: Array<{ name: string }>) {
  return groups.map((item) => item.name).join('、') || '未分配'
}

async function load() {
  rows.value = (await list<any>('/users')).results
}
onMounted(load)
</script>
