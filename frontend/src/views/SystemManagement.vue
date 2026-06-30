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
          <el-form-item v-if="storeForm.platform === 'other'" label="平台类型">
            <el-input v-model="storeForm.custom_platform" placeholder="填写平台类型" />
          </el-form-item>
          <el-form-item><el-button type="primary" @click="createStore">新建店铺</el-button></el-form-item>
        </el-form>
        <el-table :data="stores" border>
          <el-table-column prop="name" label="店铺" />
          <el-table-column label="平台">
            <template #default="{ row }">{{ storePlatformLabel(row) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">{{ statusLabel(row.status) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" :type="row.status === 'enabled' ? 'warning' : 'success'" plain @click="toggleStore(row)">
                {{ row.status === 'enabled' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="设计流程" name="design">
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
          <el-table-column label="状态" width="120">
            <template #default="{ row }">{{ statusLabel(row.status) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" :type="row.status === 'enabled' ? 'warning' : 'success'" plain @click="toggleDesignOption(row)">
                {{ row.status === 'enabled' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
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
          <el-table-column label="状态" width="120">
            <template #default="{ row }">{{ statusLabel(row.status) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" :type="row.status === 'enabled' ? 'warning' : 'success'" plain @click="togglePaymentChannel(row)">
                {{ row.status === 'enabled' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="用户管理" name="users">
        <el-tabs v-model="userManageTab">
          <el-tab-pane label="角色" name="roles">
            <el-form inline :model="roleForm">
              <el-form-item label="角色名"><el-input v-model="roleForm.name" /></el-form-item>
              <el-form-item><el-button type="primary" @click="createRole">新建角色</el-button></el-form-item>
            </el-form>
            <div class="permission-editor">
              <section class="permission-palette">
                <div class="permission-palette-head">
                  <strong>权限项</strong>
                  <span>{{ activeRole ? `正在编辑：${activeRole.name}` : '先选择下方角色' }}</span>
                </div>
                <div class="permission-groups">
                  <section v-for="group in permissionGroups" :key="group.name">
                    <strong>{{ group.name }}</strong>
                    <div class="permission-tags">
                      <el-tag
                        v-for="permission in group.items"
                        :key="permission.id"
                        :type="activeRoleHasPermission(permission.id) ? 'success' : 'info'"
                        :effect="activeRoleHasPermission(permission.id) ? 'dark' : 'plain'"
                        :class="{ 'permission-tag-clickable': activeRole && !activeRoleHasPermission(permission.id) }"
                        @click="addPermissionToActiveRole(permission.id)"
                      >
                        {{ permission.label }}
                      </el-tag>
                    </div>
                  </section>
                </div>
              </section>

              <section class="role-permission-list">
                <article
                  v-for="role in roles"
                  :key="role.id"
                  class="role-permission-card"
                  :class="{ active: role.id === activeRoleId }"
                  @click="activeRoleId = role.id"
                >
                  <div class="role-card-head">
                    <strong>{{ role.name }}</strong>
                    <el-button size="small" type="primary" @click.stop="saveRole(role)">保存</el-button>
                  </div>
                  <div class="selected-permissions">
                    <el-tag
                      v-for="permission in rolePermissions(role)"
                      :key="permission.id"
                      closable
                      @close="removePermissionFromRole(role, permission.id)"
                    >
                      {{ permission.label }}
                    </el-tag>
                    <span v-if="!rolePermissions(role).length" class="empty-text">暂无权限</span>
                  </div>
                </article>
              </section>
            </div>
          </el-tab-pane>

          <el-tab-pane label="用户" name="user-list">
            <div class="table-toolbar">
              <el-button type="primary" @click="openCreateUser">新建用户</el-button>
            </div>
            <el-table :data="users" border>
              <el-table-column prop="username" label="用户名" width="130" />
              <el-table-column prop="first_name" label="姓名" width="120" />
              <el-table-column label="角色" min-width="240">
                <template #default="{ row }">
                  <el-checkbox-group v-model="row._groupIds">
                    <el-checkbox v-for="role in roles" :key="role.id" :label="role.id">{{ role.name }}</el-checkbox>
                  </el-checkbox-group>
                </template>
              </el-table-column>
              <el-table-column label="合并权限" min-width="260">
                <template #default="{ row }">{{ userPermissionLabels(row) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="90">
                <template #default="{ row }">{{ row.is_active ? '启用' : '停用' }}</template>
              </el-table-column>
              <el-table-column label="操作" width="260">
                <template #default="{ row }">
                  <el-button size="small" type="primary" @click="saveUserRoles(row)">保存</el-button>
                  <el-button size="small" plain @click="openResetPassword(row)">重置密码</el-button>
                  <el-button
                    size="small"
                    :type="row.is_active ? 'warning' : 'success'"
                    plain
                    :disabled="row.id === auth.user?.id && row.is_active"
                    @click="toggleUserStatus(row)"
                  >
                    {{ row.is_active ? '停用' : '启用' }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </el-tab-pane>
    </el-tabs>
  </section>

  <el-dialog v-model="userDialogVisible" title="新建用户" width="min(560px, 94vw)">
    <el-form label-position="top" :model="userForm">
      <el-form-item label="用户名">
        <el-input v-model="userForm.username" placeholder="用于登录，例如 sales02" />
      </el-form-item>
      <el-form-item label="姓名">
        <el-input v-model="userForm.first_name" placeholder="员工姓名" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="userForm.email" placeholder="可选" />
      </el-form-item>
      <el-form-item label="初始密码">
        <el-input v-model="userForm.password" type="password" show-password placeholder="至少 8 位，创建后可再修改" />
      </el-form-item>
      <el-form-item label="角色">
        <el-checkbox-group v-model="userForm.group_ids">
          <el-checkbox v-for="role in roles" :key="role.id" :label="role.id">{{ role.name }}</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      <el-form-item label="账号状态">
        <el-switch v-model="userForm.is_active" active-text="启用" inactive-text="停用" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="userDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="createUser">创建用户</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="resetPasswordVisible" title="重置密码" width="min(460px, 94vw)">
    <el-form label-position="top" :model="passwordForm">
      <el-form-item label="账号">
        <el-input :model-value="currentPasswordUser?.username || ''" disabled />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="passwordForm.password" type="password" show-password placeholder="至少 8 位" />
      </el-form-item>
      <el-form-item label="确认新密码">
        <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="再次输入新密码" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="resetPasswordVisible = false">取消</el-button>
      <el-button type="primary" :loading="resettingPassword" @click="submitResetPassword">确认重置</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, create, list } from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const activeTab = ref('stores')
const userManageTab = ref('roles')
const stores = ref<any[]>([])
const designOptions = ref<any[]>([])
const paymentChannels = ref<any[]>([])
const users = ref<any[]>([])
const roles = ref<any[]>([])
const permissions = ref<any[]>([])
const userDialogVisible = ref(false)
const resetPasswordVisible = ref(false)
const resettingPassword = ref(false)
const currentPasswordUser = ref<any | null>(null)
const activeRoleId = ref<number | null>(null)

const storeForm = reactive({ name: '', platform: 'taobao', custom_platform: '', status: 'enabled' })
const designForm = reactive({ name: '', requires_design: true, sort_order: 50, status: 'enabled', description: '' })
const channelForm = reactive({ name: '', code: '', is_default: false, sort_order: 70, status: 'enabled', description: '' })
const roleForm = reactive({ name: '' })
const userForm = reactive({
  username: '',
  first_name: '',
  email: '',
  password: '',
  group_ids: [] as number[],
  is_active: true
})
const passwordForm = reactive({
  password: '',
  confirmPassword: ''
})
const permissionGroups = computed(() => {
  const grouped: Record<string, any[]> = {}
  for (const permission of permissions.value) {
    if (!grouped[permission.group]) grouped[permission.group] = []
    grouped[permission.group].push(permission)
  }
  return Object.entries(grouped).map(([name, items]) => ({ name, items }))
})
const activeRole = computed(() => roles.value.find((role) => role.id === activeRoleId.value) || null)

function roleNames(groups: Array<{ name: string }>) {
  return groups.map((item) => item.name).join('、') || '未分配'
}

function statusLabel(status: string) {
  return status === 'enabled' ? '启用' : '停用'
}

function storePlatformLabel(store: any) {
  return store.platform_label || (store.platform === 'other' && store.custom_platform ? store.custom_platform : store.platform)
}

async function loadAll() {
  const [storePage, designPage, channelPage, userPage, rolePage, permissionsResponse] = await Promise.all([
    list<any>('/stores'),
    list<any>('/design-options'),
    list<any>('/payment-channels'),
    list<any>('/users'),
    list<any>('/roles'),
    api.get('/roles/permissions/')
  ])
  permissions.value = permissionsResponse.data
  const permissionIdByCode = Object.fromEntries(permissions.value.map((permission) => [permission.code, permission.id]))
  stores.value = storePage.results
  designOptions.value = designPage.results
  paymentChannels.value = channelPage.results
  roles.value = rolePage.results.map((role) => ({
    ...role,
    _permissionIds: (role.permission_codes || []).map((code: string) => permissionIdByCode[code]).filter(Boolean)
  }))
  if (!activeRoleId.value && roles.value.length) activeRoleId.value = roles.value[0].id
  if (activeRoleId.value && !roles.value.some((role) => role.id === activeRoleId.value)) {
    activeRoleId.value = roles.value[0]?.id || null
  }
  users.value = userPage.results.map((user) => ({
    ...user,
    _groupIds: (user.groups || []).map((group: any) => group.id)
  }))
}

async function createStore() {
  if (!storeForm.name) return ElMessage.warning('请填写店铺名')
  if (storeForm.platform === 'other' && !storeForm.custom_platform) return ElMessage.warning('请填写平台类型')
  await create('/stores/', storeForm)
  Object.assign(storeForm, { name: '', platform: 'taobao', custom_platform: '', status: 'enabled' })
  ElMessage.success('店铺已创建')
  await loadAll()
}

async function createDesignOption() {
  if (!designForm.name) return ElMessage.warning('请填写名称')
  await create('/design-options/', designForm)
  designForm.name = ''
  ElMessage.success('设计流程已创建')
  await loadAll()
}

async function createChannel() {
  if (!channelForm.name || !channelForm.code) return ElMessage.warning('请填写渠道名称和编码')
  await create('/payment-channels/', channelForm)
  Object.assign(channelForm, { name: '', code: '', is_default: false, sort_order: channelForm.sort_order + 10 })
  ElMessage.success('收款渠道已创建')
  await loadAll()
}

async function toggleStore(row: any) {
  await api.patch(`/stores/${row.id}/`, { status: row.status === 'enabled' ? 'disabled' : 'enabled' })
  ElMessage.success(`店铺已${row.status === 'enabled' ? '停用' : '启用'}`)
  await loadAll()
}

async function toggleDesignOption(row: any) {
  await api.patch(`/design-options/${row.id}/`, { status: row.status === 'enabled' ? 'disabled' : 'enabled' })
  ElMessage.success(`设计流程已${row.status === 'enabled' ? '停用' : '启用'}`)
  await loadAll()
}

async function togglePaymentChannel(row: any) {
  await api.patch(`/payment-channels/${row.id}/`, { status: row.status === 'enabled' ? 'disabled' : 'enabled' })
  ElMessage.success(`收款渠道已${row.status === 'enabled' ? '停用' : '启用'}`)
  await loadAll()
}

async function createRole() {
  if (!roleForm.name) return ElMessage.warning('请填写角色名')
  await create('/roles/', { name: roleForm.name, permission_ids: [] })
  roleForm.name = ''
  ElMessage.success('角色已创建')
  await loadAll()
}

async function saveRole(row: any) {
  await api.patch(`/roles/${row.id}/`, { name: row.name, permission_ids: row._permissionIds || [] })
  ElMessage.success('角色权限已保存')
  await loadAll()
}

function activeRoleHasPermission(permissionId: number) {
  return Boolean(activeRole.value?._permissionIds?.includes(permissionId))
}

function addPermissionToActiveRole(permissionId: number) {
  if (!activeRole.value) {
    ElMessage.warning('请先选择要编辑的角色')
    return
  }
  if (activeRoleHasPermission(permissionId)) return
  activeRole.value._permissionIds = [...(activeRole.value._permissionIds || []), permissionId]
}

function removePermissionFromRole(role: any, permissionId: number) {
  role._permissionIds = (role._permissionIds || []).filter((id: number) => id !== permissionId)
}

function rolePermissions(role: any) {
  const selected = new Set(role._permissionIds || [])
  return permissions.value.filter((permission) => selected.has(permission.id))
}

function openCreateUser() {
  Object.assign(userForm, {
    username: '',
    first_name: '',
    email: '',
    password: 'ChangeMe123!',
    group_ids: [],
    is_active: true
  })
  userDialogVisible.value = true
}

async function createUser() {
  if (!userForm.username.trim()) return ElMessage.warning('请填写用户名')
  if (!userForm.password || userForm.password.length < 8) return ElMessage.warning('初始密码至少 8 位')
  await create('/users/', {
    username: userForm.username.trim(),
    first_name: userForm.first_name.trim(),
    email: userForm.email.trim(),
    password: userForm.password,
    group_ids: userForm.group_ids,
    is_active: userForm.is_active
  })
  ElMessage.success('用户已创建')
  userDialogVisible.value = false
  await loadAll()
}

async function saveUserRoles(row: any) {
  await api.patch(`/users/${row.id}/`, { group_ids: row._groupIds || [] })
  ElMessage.success('用户角色已保存')
  await loadAll()
}

async function toggleUserStatus(row: any) {
  if (row.id === auth.user?.id && row.is_active) {
    return ElMessage.warning('不能停用当前登录账号')
  }
  if (row.is_active) {
    try {
      await ElMessageBox.confirm(`确认停用账号 ${row.username}？停用后该账号将不能登录。`, '停用账号', {
        confirmButtonText: '停用',
        cancelButtonText: '取消',
        type: 'warning'
      })
    } catch {
      return
    }
  }
  await api.patch(`/users/${row.id}/`, { is_active: !row.is_active })
  ElMessage.success(`账号已${row.is_active ? '停用' : '启用'}`)
  await loadAll()
}

function openResetPassword(row: any) {
  currentPasswordUser.value = row
  passwordForm.password = ''
  passwordForm.confirmPassword = ''
  resetPasswordVisible.value = true
}

async function submitResetPassword() {
  if (!currentPasswordUser.value) return
  if (!passwordForm.password || passwordForm.password.length < 8) return ElMessage.warning('新密码至少 8 位')
  if (passwordForm.password !== passwordForm.confirmPassword) return ElMessage.warning('两次输入的密码不一致')

  resettingPassword.value = true
  try {
    await api.post(`/users/${currentPasswordUser.value.id}/reset-password/`, { password: passwordForm.password })
    ElMessage.success('密码已重置')
    resetPasswordVisible.value = false
  } finally {
    resettingPassword.value = false
  }
}

function userPermissionLabels(user: any) {
  if (user.is_superuser || user.effective_permission_codes?.includes('*')) return '全部权限'
  const selectedRoleIds = new Set(user._groupIds || [])
  const permissionIds = new Set<number>()
  for (const role of roles.value) {
    if (!selectedRoleIds.has(role.id)) continue
    for (const permissionId of role._permissionIds || []) permissionIds.add(permissionId)
  }
  const labels = permissions.value.filter((permission) => permissionIds.has(permission.id)).map((permission) => permission.label)
  return labels.join('、') || '暂无权限'
}

onMounted(loadAll)
</script>
