<template>
  <section class="panel">
    <div class="panel-head"><h2>用户管理</h2><el-button @click="load">刷新</el-button></div>
    <el-table :data="rows" border style="margin-top: 14px">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="first_name" label="姓名" />
      <el-table-column label="角色">
        <template #default="{ row }">{{ roleNames(row.groups) }}</template>
      </el-table-column>
      <el-table-column prop="is_active" label="启用">
        <template #default="{ row }">{{ row.is_active ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openResetPassword(row)">重置密码</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>

  <el-dialog v-model="resetVisible" title="重置密码" width="min(460px, 94vw)" destroy-on-close>
    <el-form label-position="top">
      <el-form-item label="用户">
        <el-input :model-value="currentUser?.username || ''" disabled />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="passwordForm.password" type="password" show-password autocomplete="new-password" />
      </el-form-item>
      <el-form-item label="确认新密码">
        <el-input v-model="passwordForm.confirmPassword" type="password" show-password autocomplete="new-password" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="resetVisible = false">取消</el-button>
      <el-button type="primary" :loading="resetting" @click="submitResetPassword">确认重置</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api, list } from '../api/client'

const rows = ref<any[]>([])
const resetVisible = ref(false)
const resetting = ref(false)
const currentUser = ref<any>(null)
const passwordForm = reactive({
  password: '',
  confirmPassword: ''
})

function roleNames(groups: Array<{ name: string }>) {
  return groups.map((item) => item.name).join('、') || '未分配'
}

async function load() {
  rows.value = (await list<any>('/users')).results
}

function openResetPassword(row: any) {
  currentUser.value = row
  passwordForm.password = ''
  passwordForm.confirmPassword = ''
  resetVisible.value = true
}

async function submitResetPassword() {
  if (!currentUser.value || resetting.value) return
  if (passwordForm.password.length < 8) return ElMessage.warning('新密码至少需要 8 位')
  if (passwordForm.password !== passwordForm.confirmPassword) return ElMessage.warning('两次输入的新密码不一致')
  resetting.value = true
  try {
    await api.post(`/users/${currentUser.value.id}/reset-password/`, {
      password: passwordForm.password
    })
    ElMessage.success('密码已重置')
    resetVisible.value = false
  } catch (error: any) {
    const detail = error?.response?.data
    const message = detail?.password?.[0] || detail?.message || detail?.detail || '密码重置失败'
    ElMessage.error(message)
  } finally {
    resetting.value = false
  }
}

onMounted(load)
</script>
