<template>
  <div class="p-4 md:p-6">
    <!-- 顶部标题 -->
    <div class="mb-6">
      <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">个人中心</h1>
      <p class="text-gray-600">管理您的个人信息与账号</p>
    </div>
    <!-- 基本资料 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="p-6 border-b border-gray-200 flex items-center justify-between cursor-pointer select-none" @click="togglePanel('profile')">
        <div>
          <h2 class="text-lg font-semibold text-gray-900 mb-1">基本资料</h2>
          <p class="text-sm text-gray-600">更新昵称、邮箱与头像地址</p>
        </div>
        <el-icon :class="['transition-transform', activePanel==='profile' ? 'rotate-180' : '']"><ArrowDown /></el-icon>
      </div>
      <div class="p-6" v-show="activePanel==='profile'">
        <el-form :model="profileForm" :label-position="isMobile ? 'top' : 'right'" :label-width="isMobile ? undefined : '120px'">
          <el-form-item label="用户名">
            <el-input :model-value="userStore.userInfo.username" disabled />
          </el-form-item>
          <el-form-item label="昵称">
            <el-input v-model="profileForm.nickname" placeholder="请输入昵称" maxlength="20" show-word-limit />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="profileForm.email" placeholder="请输入邮箱（可选）" />
          </el-form-item>
          <el-form-item label="头像URL">
            <el-input v-model="profileForm.avatar_url" placeholder="请输入头像图片地址（可选）" />
          </el-form-item>
          <el-form-item>
            <div class="flex gap-3 flex-col sm:flex-row w-full">
              <el-button type="primary" class="w-full sm:w-auto h-11" :loading="savingProfile" @click="saveProfile">保存资料</el-button>
              <el-button type="danger" class="w-full sm:w-auto h-11" @click="handleLogout">退出登录</el-button>
            </div>
          </el-form-item>
        </el-form>

        <!-- 危险操作区域 -->
        <div class="mt-8 pt-6 border-t border-gray-200">
          <div class="mb-4 form-align-fix">
            <h3 class="text-lg font-medium text-red-600 mb-2">危险操作</h3>
            <p class="text-sm text-gray-600">注销账号将永久删除您的所有数据，包括联通账号信息、流量记录等，此操作不可恢复。</p>
          </div>
          <div class="flex gap-3 flex-col sm:flex-row w-full form-align-fix">
            <el-button
              type="danger"
              plain
              class="w-full sm:w-auto h-11"
              :loading="deletingAccount"
              @click="handleDeleteAccount"
            >
              <el-icon class="mr-2"><Delete /></el-icon>
              注销账号
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 安全设置 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="p-6 border-b border-gray-200 flex items-center justify-between cursor-pointer select-none" @click="togglePanel('security')">
        <div>
          <h2 class="text-lg font-semibold text-gray-900 mb-1">安全设置</h2>
          <p class="text-sm text-gray-600">修改登录密码</p>
        </div>
        <el-icon :class="['transition-transform', activePanel==='security' ? 'rotate-180' : '']"><ArrowDown /></el-icon>
      </div>
      <div class="p-6" v-show="activePanel==='security'">
        <el-form :model="pwdForm" :label-position="isMobile ? 'top' : 'right'" :label-width="isMobile ? undefined : '120px'">
          <el-form-item label="当前密码">
            <el-input v-model="pwdForm.old_password" type="password" placeholder="请输入当前密码" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="pwdForm.new_password" type="password" placeholder="至少6位，建议包含数字与字母" show-password />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="pwdForm.confirm" type="password" placeholder="再次输入新密码" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" class="w-full sm:w-auto h-11" :loading="savingPwd" @click="changePasswordNow">更新密码</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>


    <!-- 账号管理模块（迁移自配置页） -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="p-6 border-b border-gray-200 flex items-center justify-between cursor-pointer select-none" @click="togglePanel('accounts')">
        <div class="flex items-center gap-3">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 mb-1">联通账号管理</h2>
            <p class="text-sm text-gray-600">添加、认证、开启监控与复制关键信息</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <el-icon :class="['transition-transform', activePanel==='accounts' ? 'rotate-180' : '']"><ArrowDown /></el-icon>
        </div>
      </div>

      <!-- 账号管理（组件化） -->
      <div class="p-6" v-show="activePanel==='accounts'">
        <AccountManager />
      </div>
    </div>



  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Delete } from '@/utils/icons'
import AccountManager from '@/components/AccountManager.vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const router = useRouter()
const userStore = useUserStore()

// 基本资料
const profileForm = reactive({ nickname: '', email: '', avatar_url: '' })
const savingProfile = ref(false)
const saveProfile = async () => {
  try {
    savingProfile.value = true
    const payload = {
      nickname: profileForm.nickname || '',
      email: profileForm.email || null,
      avatar_url: profileForm.avatar_url || null
    }
    const res = await userStore.updateUserInfo(payload)
    if (res?.success) ElMessage.success('资料已更新')
    else ElMessage.error(res?.message || '更新失败')
  } catch (e) {
    ElMessage.error('更新失败，请检查网络连接')
  } finally {
    savingProfile.value = false
  }
}

// 修改密码
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })
const savingPwd = ref(false)
const changePasswordNow = async () => {
  if (!pwdForm.old_password || !pwdForm.new_password) { ElMessage.error('请输入完整'); return }
  if (pwdForm.new_password.length < 6) { ElMessage.error('新密码至少6位'); return }
  if (pwdForm.new_password !== pwdForm.confirm) { ElMessage.error('两次输入不一致'); return }
  try {
    savingPwd.value = true
    const res = await userStore.changePassword({ old_password: pwdForm.old_password, new_password: pwdForm.new_password })
    if (res?.success) {
      ElMessage.success('密码已更新，请使用新密码登录')
      Object.assign(pwdForm, { old_password: '', new_password: '', confirm: '' })
    } else {
      ElMessage.error(res?.message || '修改失败')
    }
  } catch (e) {
    ElMessage.error('修改失败，请检查网络连接')
  } finally {
    savingPwd.value = false
  }
}

const handleLogout = async () => {
  try { await userStore.logout() } finally { router.push('/login') }
}

// 注销账号
const deletingAccount = ref(false)
const handleDeleteAccount = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将永久删除您的账号及所有相关数据，包括：\n• 个人资料信息\n• 所有联通账号信息\n• 历史流量记录\n• 监控配置\n\n此操作不可恢复，确定要继续吗？',
      '确认注销账号',
      {
        confirmButtonText: '确认注销',
        cancelButtonText: '取消',
        type: 'error',
        dangerouslyUseHTMLString: false,
        confirmButtonClass: 'el-button--danger'
      }
    )

    // 二次确认
    await ElMessageBox.confirm(
      '最后确认：您真的要注销账号吗？\n注销后将无法恢复任何数据！',
      '最后确认',
      {
        confirmButtonText: '确认注销',
        cancelButtonText: '我再想想',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    )

    deletingAccount.value = true
    const res = await userStore.deleteAccount()

    if (res?.success) {
      ElMessage.success('账号已注销')
      // 清除所有本地数据并跳转到登录页
      await userStore.logout()
      router.push('/login')
    } else {
      ElMessage.error(res?.message || '注销失败，请重试')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('注销失败，请重试')
    }
  } finally {
    deletingAccount.value = false
  }
}



onMounted(() => {
  const u = userStore.userInfo
  profileForm.nickname = u.nickname || ''
  profileForm.email = u.email || ''
  profileForm.avatar_url = u.avatar_url || ''
})


// H5 自适应
const isMobile = ref(typeof window !== 'undefined' ? window.innerWidth < 640 : true)
const updateIsMobile = () => { if (typeof window !== 'undefined') isMobile.value = window.innerWidth < 640 }
onMounted(() => { updateIsMobile(); if (typeof window !== 'undefined') window.addEventListener('resize', updateIsMobile) })
onBeforeUnmount(() => { if (typeof window !== 'undefined') window.removeEventListener('resize', updateIsMobile) })

// 手风琴：个人中心仅允许一个版块展开（默认展开账号管理）
const activePanel = ref('accounts')
const togglePanel = (key) => {
  activePanel.value = activePanel.value === key ? '' : key
}


</script>

<style scoped>
.copy-header { display:flex; align-items:center; gap:10px; padding: 6px 4px 0; }
.copy-header .icon-wrap { width:32px; height:32px; border-radius:9999px; background:linear-gradient(180deg,#eff6ff,#dbeafe); display:flex; align-items:center; justify-content:center; color:#2563eb; }
.copy-header .title { font-weight:600; color:#111827; }
.copy-header .subtitle { font-size:12px; color:#6b7280; margin-top:2px; }
.copy-header .close-btn { margin-left:auto; }
.copy-dialog :deep(.el-dialog__body) { padding-top: 8px; }
.copy-dialog .label { width:110px; min-width:110px; color:#6b7280; font-size:12px; padding-top:6px; }
.copy-dialog .code-row { display:flex; gap:8px; align-items:flex-start; }
.copy-dialog .mono :deep(textarea) { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }
.copy-dialog .tip { font-size:12px; color:#6b7280; }
.copy-dialog .footer-actions { display:flex; justify-content:flex-end; gap:8px; }
@media (max-width: 640px) {
  .copy-dialog .code-row { flex-direction: column; }
  .copy-dialog .label { width:auto; min-width:unset; padding-top:0; }
}
</style>
