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
          <el-button type="primary" @click.stop="showAddDialog = true" :loading="loading">
            <el-icon class="mr-2"><Plus /></el-icon>
            添加账号
          </el-button>
        </div>
      </div>

      <!-- 列表（手风琴：仅当 activePanel==='accounts' 时展示） -->
      <div class="p-6" v-show="activePanel==='accounts'">
        <div v-if="loading && accounts.length===0" class="text-center py-8">
          <el-icon class="animate-spin text-2xl text-gray-400 mb-2"><Loading /></el-icon>
          <p class="text-gray-500">加载中...</p>
        </div>
        <div v-else-if="accounts.length===0" class="text-center py-8">
          <el-icon :size="48" class="text-gray-400 mb-4"><Iphone /></el-icon>
          <h3 class="text-lg font-medium text-gray-900 mb-2">暂无联通账号</h3>
          <p class="text-gray-600 mb-4">添加您的联通手机号开始使用</p>
          <el-button type="primary" @click="showAddDialog = true">添加第一个账号</el-button>
        </div>

        <div v-else class="space-y-4">
          <div v-for="account in accounts" :key="account.id" class="relative rounded-xl border border-gray-200/80 bg-white p-4 sm:p-5 shadow-[0_1px_2px_rgba(0,0,0,0.04)] hover:shadow-md transition-all">
            <!-- 右上角：认证状态 -->
            <div class="absolute top-3 right-3">
              <el-tag :type="account.is_auth_valid ? 'success' : 'danger'" size="small" effect="light">
                {{ account.is_auth_valid ? '已认证' : '未认证' }}
              </el-tag>
            </div>

            <div class="grid grid-cols-[auto,1fr] gap-4 sm:gap-6 items-center">
              <div class="flex-shrink-0">
                <div class="w-11 h-11 sm:w-12 sm:h-12 rounded-full bg-gradient-to-b from-blue-50 to-blue-100 flex items-center justify-center ring-1 ring-blue-200/50">
                  <el-icon class="text-blue-600"><Iphone /></el-icon>
                </div>
              </div>

              <div class="min-w-0">
                <div class="flex items-baseline gap-3 flex-wrap">
                  <h3 class="text-base sm:text-lg font-semibold text-gray-900 tracking-tight">{{ account.display_name }}</h3>
                  <span class="text-xs sm:text-sm text-gray-500">{{ account.phone }}</span>
                </div>

                <!-- 中部动作：监控开关、刷新、更多 -->
                <div class="mt-3 flex items-center justify-center gap-3 sm:gap-4">
                  <el-tooltip content="开启后：系统将定时查询该账号并按‘通知方式’推送告警" placement="top">
                    <span class="text-xs text-gray-600">监控与通知</span>
                  </el-tooltip>
                  <el-switch
                    v-model="account.monitor_enabled"
                    :disabled="!account.is_auth_valid"
                    :loading="toggleLoadingIds.includes(account.id)"
                    @change="(val)=>onToggleMonitor(account,val)"
                  />
                  <template v-if="!account.is_auth_valid">
                    <el-button type="primary" size="small" @click="openAuthDialog(account)">认证</el-button>
                  </template>
                  <template v-else>
                    <el-tooltip content="刷新认证/会话" placement="top">
                      <el-button type="success" circle @click="refreshAuth(account)" :loading="refreshingIds.includes(account.id)">
                        <el-icon><Refresh /></el-icon>
                      </el-button>
                    </el-tooltip>
                  </template>
                  <el-dropdown @command="(cmd)=>handleAccountAction(cmd,account)">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="copy">复制信息</el-dropdown-item>
                        <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>

                <!-- 底部信息 -->
                <div class="mt-3 flex items-center justify-between text-xs">
                  <span class="text-blue-500/90">{{ account.login_method === 'sms' ? '验证码登录' : 'Token登录' }}</span>
                  <span :class="account.monitor_enabled ? 'text-green-600' : 'text-gray-400'">{{ account.monitor_enabled ? '已开启' : '未开启' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加账号（Mobile Sheet / PC Dialog） -->
    <template v-if="isMobile">
      <MobileSheet v-model="showAddDialog" title="添加联通账号" height="70vh">
        <el-form ref="addFormRef" :model="addForm" :rules="addRules" :label-position="'top'">
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="addForm.phone" placeholder="请输入11位联通手机号" maxlength="11" show-word-limit />
          </el-form-item>
          <el-form-item label="别名">
            <el-input v-model="addForm.phone_alias" placeholder="如：工作号、生活号（可选）" maxlength="20" show-word-limit />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddDialog=false">取消</el-button>
          <el-button type="primary" @click="handleAddAccount" :loading="addLoading">添加账号</el-button>
        </template>
      </MobileSheet>
    </template>
    <template v-else>
      <el-dialog v-model="showAddDialog" title="添加联通账号" width="500px">
        <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="100px">
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="addForm.phone" placeholder="请输入11位联通手机号" maxlength="11" show-word-limit />
          </el-form-item>
          <el-form-item label="别名">
            <el-input v-model="addForm.phone_alias" placeholder="如：工作号、生活号（可选）" maxlength="20" show-word-limit />
          </el-form-item>
        </el-form>
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="showAddDialog=false">取消</el-button>
            <el-button type="primary" @click="handleAddAccount" :loading="addLoading">添加账号</el-button>
          </div>
        </template>
      </el-dialog>
    </template>

    <!-- 认证（Mobile Sheet / PC Dialog） -->
    <template v-if="isMobile">
      <MobileSheet v-model="showAuthDialogVisible" title="联通账号认证" height="82vh">
        <div v-if="currentAccount" class="mb-3">
          <div class="text-base font-semibold text-gray-900">{{ currentAccount.display_name }}</div>
          <div class="text-xs text-gray-500">{{ currentAccount.phone }}</div>
        </div>
        <el-tabs v-model="authActiveTab" class="demo-tabs">
          <el-tab-pane label="验证码登录" name="sms">
            <el-form :model="authForm" :label-position="'top'">
              <el-form-item label="自定义AppID" required>
                <el-input v-model="authForm.custom_app_id" placeholder="请输入自定义AppID（必填）" type="textarea" :rows="2" />
                <div class="text-xs text-gray-500 mt-1">
                  <strong>必填项：</strong>请手动获取并输入自定义AppID，用于认证和流量查询
                </div>
              </el-form-item>
              <el-form-item label="验证码" required>
                <el-input v-model="authForm.sms_code" placeholder="请输入6位验证码" maxlength="6" show-word-limit />
                <div class="text-xs text-gray-500 mt-1">
                  <strong>步骤：</strong><br>1. 打开联通APP<br>2. 进入"我的" → "登录/注册"<br>3. 输入手机号 {{ currentAccount?.phone }}<br>4. 点击"获取验证码"<br>5. 将验证码填入上方
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="Token登录" name="token">
            <el-form :model="authForm" :label-position="'top'">
              <el-form-item label="Token Online" required>
                <el-input v-model="authForm.token_online" placeholder="请输入token_online" type="textarea" :rows="3" />
              </el-form-item>
              <el-form-item label="App ID" required>
                <el-input v-model="authForm.app_id" placeholder="请输入app_id" type="textarea" :rows="2" />
                <div class="text-xs text-gray-500 mt-1"><strong>获取方法：</strong><br>1. 抓包联通APP的网络请求<br>2. 找到包含appId的请求<br>3. 复制token_online和appId参数</div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
        <template #footer>
          <el-button @click="showAuthDialogVisible=false">取消</el-button>
          <el-button type="primary" @click="handleAuth" :loading="authLoading">认证</el-button>
        </template>
      </MobileSheet>
    </template>
    <template v-else>
      <el-dialog v-model="showAuthDialogVisible" title="联通账号认证" width="500px">
        <div v-if="currentAccount" class="mb-4">
          <h3 class="text-lg font-medium text-gray-900 mb-2">{{ currentAccount.display_name }}</h3>
          <p class="text-sm text-gray-600">{{ currentAccount.phone }}</p>
        </div>
        <el-tabs v-model="authActiveTab" class="demo-tabs">
          <el-tab-pane label="验证码登录" name="sms">
            <el-form :model="authForm" label-width="120px">
              <el-form-item label="自定义AppID" required>
                <el-input v-model="authForm.custom_app_id" placeholder="请输入自定义AppID（必填）" type="textarea" :rows="2" />
                <div class="text-xs text-gray-500 mt-1">
                  <strong>必填项：</strong>请手动获取并输入自定义AppID，用于认证和流量查询
                </div>
              </el-form-item>
              <el-form-item label="验证码" required>
                <el-input v-model="authForm.sms_code" placeholder="请输入6位验证码" maxlength="6" show-word-limit />
                <div class="text-xs text-gray-500 mt-1"><strong>步骤：</strong><br>1. 打开联通APP<br>2. 进入"我的" → "登录/注册"<br>3. 输入手机号 {{ currentAccount?.phone }}<br>4. 点击"获取验证码"<br>5. 将验证码填入上方</div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="Token登录" name="token">
            <el-form :model="authForm" label-width="120px">
              <el-form-item label="Token Online" required>
                <el-input v-model="authForm.token_online" placeholder="请输入token_online" type="textarea" :rows="3" />
              </el-form-item>
              <el-form-item label="App ID" required>
                <el-input v-model="authForm.app_id" placeholder="请输入app_id" type="textarea" :rows="2" />
                <div class="text-xs text-gray-500 mt-1"><strong>获取方法：</strong><br>1. 抓包联通APP的网络请求<br>2. 找到包含appId的请求<br>3. 复制token_online和appId参数</div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="showAuthDialogVisible=false">取消</el-button>
            <el-button type="primary" @click="handleAuth" :loading="authLoading">认证</el-button>
          </div>
        </template>
      </el-dialog>
    </template>

    <!-- 复制信息（Mobile Sheet / PC Dialog） -->
    <template v-if="isMobile">
      <MobileSheet v-model="showCopyDialog" title="复制账号关键信息" height="60vh">
        <div class="space-y-4">
          <div>
            <div class="text-xs text-gray-500 mb-2">仅用于导入或备份，请妥善保管，避免泄露</div>
            <div class="mb-3">
              <div class="text-[12px] text-gray-500 mb-1">token_online</div>
              <el-input v-model="copyInfo.token_online" type="textarea" :autosize="{minRows:2,maxRows:5}" readonly class="mono" />
            </div>
            <div>
              <div class="text-[12px] text-gray-500 mb-1">app_id</div>
              <el-input v-model="copyInfo.app_id" type="textarea" :autosize="{minRows:2,maxRows:4}" readonly class="mono" />
            </div>
          </div>

        </div>
        <template #footer>
          <el-button @click="() => copyText(copyInfo.token_online)">复制 token</el-button>
          <el-button @click="() => copyText(copyInfo.app_id)">复制 app_id</el-button>
          <el-button type="primary" @click="copyAll" :loading="copyLoading">复制全部</el-button>
        </template>
      </MobileSheet>
    </template>
    <template v-else>
      <el-dialog v-model="showCopyDialog" :class="['copy-dialog', { mobile: isMobile }]" :show-close="false" width="560px" top="15vh">
        <template #header>
          <div class="copy-header">
            <div class="icon-wrap"><el-icon><Document /></el-icon></div>
            <div class="titles">
              <div class="title">复制账号关键信息</div>
              <div class="subtitle">仅用于导入或备份，请妥善保管，避免泄露</div>
            </div>
            <el-button link class="close-btn" @click="showCopyDialog=false"><el-icon><Close /></el-icon></el-button>
          </div>
        </template>
        <div class="space-y-4">
          <div class="code-row">
            <label class="label">token_online</label>
            <div class="grow flex items-start gap-2">
              <el-input v-model="copyInfo.token_online" type="textarea" :autosize="{minRows:2, maxRows:5}" readonly class="mono" />
              <el-button @click="() => copyText(copyInfo.token_online)" :loading="copyLoading">复制</el-button>
            </div>
          </div>
          <div class="code-row">
            <label class="label">app_id</label>
            <div class="grow flex items-start gap-2">
              <el-input v-model="copyInfo.app_id" type="textarea" :autosize="{minRows:2, maxRows:4}" readonly class="mono" />
              <el-button @click="() => copyText(copyInfo.app_id)" :loading="copyLoading">复制</el-button>
            </div>
          </div>
          <p class="tip">仅用于导入到其它工具或备份，请注意保管，避免泄露。</p>
        </div>
        <template #footer>
          <div class="footer-actions">
            <el-button @click="showCopyDialog=false">关闭</el-button>
            <el-button type="primary" @click="copyAll" :loading="copyLoading">复制全部</el-button>
          </div>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Loading, Refresh, MoreFilled, Iphone, Close, Document, ArrowDown, Delete } from '@/utils/icons'
import { api, unicomAPI } from '@/utils/api'
import MobileSheet from '@/components/MobileSheet.vue'
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

// 列表与加载
const accounts = ref([])
const loading = ref(false)

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

// 添加账号
const showAddDialog = ref(false)
const addLoading = ref(false)
const addFormRef = ref()
const addForm = reactive({ phone: '', phone_alias: '' })
const addRules = { phone: [ { required: true, message: '请输入手机号', trigger: 'blur' }, { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' } ] }

// 认证
const currentAccount = ref(null)
const authActiveTab = ref('sms')
const showAuthDialogVisible = ref(false)
const authLoading = ref(false)
const authForm = reactive({ sms_code: '', token_online: '', app_id: '', custom_app_id: '' })

// 复制信息
const showCopyDialog = ref(false)
const copyLoading = ref(false)
const copyInfo = reactive({ token_online: '', app_id: '' })

// 状态切换与刷新
const toggleLoadingIds = ref([])
const refreshingIds = ref([])

const fetchAccounts = async () => {
  loading.value = true
  try {
    const res = await api.get('/unicom/accounts')
    if (res?.success) accounts.value = res.data
    else ElMessage.error(res?.message || '获取账号列表失败')
  } catch (e) {
    ElMessage.error('获取账号列表失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

const handleAddAccount = async () => {
  if (!addFormRef.value) return
  try {
    await addFormRef.value.validate()
    addLoading.value = true
    const res = await api.post('/unicom/accounts', addForm)
    if (res?.success) {
      ElMessage.success('联通账号添加成功！请进行认证以开始使用。')
      showAddDialog.value = false
      Object.assign(addForm, { phone: '', phone_alias: '' })
      await fetchAccounts()
      const newAccount = res.data
      if (newAccount) setTimeout(() => openAuthDialog(newAccount), 400)
    } else {
      ElMessage.error(res?.message || '添加失败')
    }
  } catch (e) {
    if (!e?.errors) {
      // 优先使用后端返回的错误信息
      const message = e.response?.data?.message || e.message || '添加失败，请检查网络连接'
      ElMessage.error(message)
    }
  } finally {
    addLoading.value = false
  }
}

const openAuthDialog = (account) => {
  currentAccount.value = account
  authActiveTab.value = 'sms'
  Object.assign(authForm, { sms_code: '', token_online: '', app_id: '', custom_app_id: '' })
  showAuthDialogVisible.value = true
}

const handleAuth = async () => {
  if (!currentAccount.value) return
  authLoading.value = true
  try {
    let res
    if (authActiveTab.value === 'sms') {
      if (!authForm.custom_app_id.trim()) { ElMessage.error('请输入自定义AppID'); return }
      if (!authForm.sms_code.trim()) { ElMessage.error('请输入验证码'); return }
      res = await api.post(`/unicom/accounts/${currentAccount.value.id}/login/sms`, {
        sms_code: authForm.sms_code,
        custom_app_id: authForm.custom_app_id
      })
    } else {
      if (!authForm.token_online.trim() || !authForm.app_id.trim()) { ElMessage.error('请输入Token Online和App ID'); return }
      res = await api.post(`/unicom/accounts/${currentAccount.value.id}/login/token`, { token_online: authForm.token_online, app_id: authForm.app_id })
    }
    if (res?.success) { ElMessage.success('认证成功！'); showAuthDialogVisible.value = false; await fetchAccounts() }
    else { ElMessage.error(res?.message || '认证失败') }
  } catch (e) {
    ElMessage.error('认证失败，请检查网络连接')
  } finally {
    authLoading.value = false
  }
}

const refreshAuth = async (account) => {
  refreshingIds.value.push(account.id)
  try {
    const res = await api.post(`/unicom/accounts/${account.id}/refresh`)
    if (res?.success) { ElMessage.success('认证刷新成功！'); await fetchAccounts() }
    else { ElMessage.error(res?.message || '刷新失败') }
  } catch (e) {
    ElMessage.error('刷新失败，请检查网络连接')
  } finally {
    refreshingIds.value = refreshingIds.value.filter(id => id !== account.id)
  }
}

const onToggleMonitor = async (account, val) => {
  if (val && !account.is_auth_valid) { ElMessage.error('账号未认证或已过期，无法开启监控'); account.monitor_enabled = false; return }
  toggleLoadingIds.value.push(account.id)
  try {
    const res = await unicomAPI.toggleMonitor(account.id, val)
    if (res?.success) { account.monitor_enabled = !!(res.data && res.data.monitor_enabled); ElMessage.success(val ? '已开启监控与通知' : '已关闭监控与通知') }
    else throw new Error(res?.message || '操作失败')
  } catch (e) {
    account.monitor_enabled = !val
    ElMessage.error(e.message || '操作失败')
  } finally {
    toggleLoadingIds.value = toggleLoadingIds.value.filter(id => id !== account.id)
  }
}

const handleAccountAction = async (command, account) => {
  if (command === 'copy') {
    try {
      const res = await unicomAPI.getAccount(account.id)
      if (!res?.success) throw new Error(res?.message || '获取账号信息失败')
      copyInfo.token_online = res.data?.token_online || ''
      copyInfo.app_id = res.data?.app_id || res.data?.effective_app_id || ''
      showCopyDialog.value = true
    } catch (e) {
      ElMessage.error(e.message || '获取失败')
    }
  } else if (command === 'delete') {
    try {
      await ElMessageBox.confirm(`确定要删除联通账号 ${account.display_name} 吗？`, '确认删除', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
      const res = await api.delete(`/unicom/accounts/${account.id}`)
      if (res?.success) { ElMessage.success('删除成功！'); await fetchAccounts() }
      else { ElMessage.error(res?.message || '删除失败') }
    } catch (e) {
      if (e !== 'cancel') ElMessage.error('删除失败，请检查网络连接')
    }
  }
}

const copyText = async (text) => {
  if (!text) return ElMessage.warning('内容为空')
  try { await navigator.clipboard.writeText(text); ElMessage.success('已复制到剪贴板') } catch { ElMessage.error('复制失败') }
}

const copyAll = async () => {
  copyLoading.value = true
  try {
    const text = JSON.stringify(copyInfo, null, 2)
    await navigator.clipboard.writeText(text)
    ElMessage.success('全部已复制')
  } catch { ElMessage.error('复制失败') } finally { copyLoading.value = false }
}

onMounted(() => { fetchAccounts() })
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
