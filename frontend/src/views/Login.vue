<template>
  <div class="login-page">
    <el-form class="login-card" :model="form" label-position="top" @submit.prevent="submit">
      <img class="login-logo" :src="logo" alt="介知包装" />
      <h1>JiezhiERP</h1>
      <p>使用初始化账号登录：admin / admin123456</p>
      <el-form-item label="用户名">
        <el-input v-model="form.username" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="form.password" type="password" show-password />
      </el-form-item>
      <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">登录</el-button>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import logo from '../assets/jiezhi-logo-square.png'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123456' })

async function submit() {
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    router.push('/')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || '登录失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}
</script>
