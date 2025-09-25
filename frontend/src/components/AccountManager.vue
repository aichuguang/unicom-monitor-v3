<template>
  <div class="space-y-6">
    <!-- 账号列表 -->
    <div v-if="loading && accounts.length === 0" class="flex flex-col items-center justify-center py-16">
      <div class="relative mb-4">
        <!-- 外圈旋转环 -->
        <div class="w-10 h-10 border-2 border-gray-200 rounded-full animate-spin border-t-blue-400"></div>
        <!-- 内圈反向旋转环 -->
        <div class="absolute inset-1 w-8 h-8 border-2 border-transparent rounded-full animate-spin border-b-blue-500" style="animation-direction: reverse; animation-duration: 1.5s;"></div>
      </div>
      <p class="text-gray-400 text-sm font-medium">加载中...</p>
    </div>
    <div v-else-if="accounts.length === 0" class="text-center py-8">
      <Iphone class="w-12 h-12 text-gray-400 mb-4" />
      <h3 class="text-lg font-medium text-gray-900 mb-2">暂无联通账号</h3>
      <p class="text-gray-600 mb-4">添加您的联通手机号开始使用</p>
      <el-button type="primary" @click="showAddDialog = true">添加第一个账号</el-button>
    </div>

    <div v-else class="space-y-4">
      <div class="flex items-center justify-between">
        <el-button type="primary" @click="showAddDialog = true" :loading="loading">
          <Plus class="w-4 h-4 mr-2" />
          添加账号
        </el-button>
      </div>

      <div class="space-y-2">
        <div v-for="account in accounts" :key="account.id"
             class="relative rounded-xl border border-gray-200/80 bg-white p-3 shadow-[0_1px_2px_rgba(0,0,0,0.04)] hover:shadow-md transition-all"
             :class="!account.is_auth_valid ? 'cursor-pointer hover:border-orange-300' : ''"
             @click="onCardClick(account)"
             :title="!account.is_auth_valid ? '未认证，点击去认证' : ''">
          <!-- 账号信息 -->
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <!-- 顶部：左别名（粗黑），右手机号 + 状态标签 -->
            <div class="flex items-center justify-between gap-3 w-full">
              <div class="font-semibold text-gray-900 truncate">{{ account.display_name || account.phone }}</div>
              <div class="flex items-center gap-2 flex-shrink-0">
                <span class="text-sm text-gray-500">{{ account.phone }}</span>
                <el-tag :type="account.is_auth_valid ? 'success' : 'danger'" size="small">
                  {{ account.is_auth_valid ? '已认证' : '未认证' }}
                </el-tag>
              </div>
            </div>

            <!-- 底部功能区：等距、不拥挤，可换行 -->
            <div class="mt-2 pt-2 border-t border-gray-100 flex items-center justify-between flex-wrap gap-y-2">
              <!-- 左：监控开关 -->
              <div class="flex items-center gap-2" @click.stop>
                <span class="text-xs text-gray-500">监控</span>
                <el-switch
                  :model-value="!!account.monitor_enabled"
                  :loading="toggleLoadingIds.includes(account.id)"
                  @change="(val) => onToggleMonitor(account, val)"
                  size="small"
                />
              </div>

              <!-- 右：图标操作组 -->
              <div class="flex items-center gap-4">
                <template v-if="!account.is_auth_valid">
                  <el-tooltip content="认证账号" placement="top">
                    <button @click.stop="openAuthDialog(account)"
                            class="w-8 h-8 rounded-full bg-amber-100 hover:bg-amber-200 flex items-center justify-center transition-colors">
                      <Lock class="w-4 h-4 text-amber-600" />
                    </button>
                  </el-tooltip>
                </template>
                <template v-else>
                  <el-tooltip content="刷新认证/会话" placement="top">
                    <button @click.stop="refreshAuth(account)" :disabled="refreshingIds.includes(account.id)"
                            class="w-8 h-8 rounded-full bg-emerald-100 hover:bg-emerald-200 flex items-center justify-center transition-colors disabled:opacity-50">
                      <Refresh class="w-4 h-4 text-emerald-600" :class="refreshingIds.includes(account.id) ? 'animate-spin' : ''" />
                    </button>
                  </el-tooltip>
                </template>

                <el-tooltip content="复制信息" placement="top">
                  <button @click.stop="handleAccountAction('copy', account)"
                          class="w-8 h-8 rounded-full bg-blue-100 hover:bg-blue-200 flex items-center justify-center transition-colors">
                    <Document class="w-4 h-4 text-blue-600" />
                  </button>
                </el-tooltip>

                <el-tooltip content="删除账号" placement="top">
                  <button @click.stop="confirmDelete(account)"
                          class="w-8 h-8 rounded-full bg-red-100 hover:bg-red-200 flex items-center justify-center transition-colors">
                    <Delete class="w-4 h-4 text-red-600" />
                  </button>
                </el-tooltip>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加账号对话框 -->
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
          <el-button @click="showAddDialog = false">取消</el-button>
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
            <el-button @click="showAddDialog = false">取消</el-button>
            <el-button type="primary" @click="handleAddAccount" :loading="addLoading">添加账号</el-button>
          </div>
        </template>
      </el-dialog>
    </template>

    <!-- 认证对话框 -->
    <template v-if="isMobile">
      <MobileSheet v-model="showAuthDialog" title="联通账号认证" height="82vh">
        <div v-if="currentAccount" class="mb-3">
          <div class="text-base font-semibold text-gray-900">{{ currentAccount.display_name }}</div>
          <div class="text-xs text-gray-500">{{ currentAccount.phone }}</div>
        </div>
        <el-tabs v-model="authActiveTab" class="demo-tabs">
          <el-tab-pane label="验证码登录" name="sms">
            <el-form :model="authForm" :label-position="'top'">
              <el-form-item label="App ID" required>
                <el-input v-model="authForm.custom_app_id" placeholder="从联通APP抓包获取的AppID" type="textarea" :rows="2" />
                <div class="text-xs text-gray-500 mt-1">
                  必填：从联通APP抓包获取的AppID，用于验证码登录
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
          <el-button @click="showAuthDialog = false">取消</el-button>
          <el-button type="primary" @click="handleAuth" :loading="authLoading">认证</el-button>
        </template>
      </MobileSheet>
    </template>
    <template v-else>
      <el-dialog v-model="showAuthDialog" title="联通账号认证" width="500px">
        <div v-if="currentAccount" class="mb-4">
          <h3 class="text-lg font-medium text-gray-900 mb-2">{{ currentAccount.display_name }}</h3>
          <p class="text-sm text-gray-600">{{ currentAccount.phone }}</p>
        </div>
        <el-tabs v-model="authActiveTab" class="demo-tabs">
          <el-tab-pane label="验证码登录" name="sms">
            <el-form :model="authForm" label-width="120px">
              <el-form-item label="App ID" required>
                <el-input v-model="authForm.custom_app_id" placeholder="从联通APP抓包获取的AppID" type="textarea" :rows="2" />
                <div class="text-xs text-gray-500 mt-1">
                  必填：从联通APP抓包获取的AppID，用于验证码登录
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
            <el-button @click="showAuthDialog = false">取消</el-button>
            <el-button type="primary" @click="handleAuth" :loading="authLoading">认证</el-button>
          </div>
        </template>
      </el-dialog>
    </template>

    <!-- 复制信息对话框 -->
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
      <el-dialog v-model="showCopyDialog" title="复制账号关键信息" width="560px">
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
            <el-button @click="showCopyDialog = false">关闭</el-button>
            <el-button type="primary" @click="copyAll" :loading="copyLoading">复制全部</el-button>
          </div>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Refresh, Document, Lock, Delete, Plus, Iphone } from '@/utils/icons'
import { api, unicomAPI } from '@/utils/api'
import MobileSheet from '@/components/MobileSheet.vue'

// 响应式检测（可随窗口变化）
const isMobile = ref(typeof window !== 'undefined' ? window.innerWidth < 768 : true)
const updateIsMobile = () => { if (typeof window !== 'undefined') isMobile.value = window.innerWidth < 768 }
onMounted(() => { if (typeof window !== 'undefined') window.addEventListener('resize', updateIsMobile) })
onUnmounted(() => { if (typeof window !== 'undefined') window.removeEventListener('resize', updateIsMobile) })

// 数据状态
const loading = ref(false)
const accounts = ref([])

// 添加账号
const showAddDialog = ref(false)
const addLoading = ref(false)
const addFormRef = ref()
const addForm = reactive({ phone: '', phone_alias: '' })
const addRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
  ]
}

// 认证
const currentAccount = ref(null)
const authActiveTab = ref('sms')
const showAuthDialog = ref(false)
const authLoading = ref(false)
const authForm = reactive({ sms_code: '', token_online: '', app_id: '', custom_app_id: '' })

// 复制信息
const showCopyDialog = ref(false)
const copyLoading = ref(false)
const copyInfo = reactive({ token_online: '', app_id: '' })

// 状态切换
const refreshingIds = ref([])

// 监控开关加载状态
const toggleLoadingIds = ref([])

// 切换监控（账号维度）
const onToggleMonitor = async (account, val) => {
  // 未认证账号不允许开启监控
  if (val && !account.is_auth_valid) {
    ElMessage.error('账号未认证或已过期，无法开启监控')
    return
  }
  toggleLoadingIds.value.push(account.id)
  try {
    const res = await unicomAPI.toggleMonitor(account.id, val)
    if (res?.success) {
      account.monitor_enabled = !!(res.data && res.data.monitor_enabled)
      ElMessage.success(val ? '已开启监控与通知' : '已关闭监控与通知')
    } else {
      throw new Error(res?.message || '操作失败')
    }
  } catch (e) {
    // 回滚开关状态
    account.monitor_enabled = !val
    ElMessage.error(e.message || '操作失败')
  } finally {
    toggleLoadingIds.value = toggleLoadingIds.value.filter(id => id !== account.id)
  }
}

// 点击卡片：未认证跳转到认证
const onCardClick = (account) => {
  if (!account?.is_auth_valid) {
    openAuthDialog(account)
  }
}


// 获取账号列表
const fetchAccounts = async () => {
  loading.value = true
  try {
    const res = await api.get('/unicom/accounts')
    if (res?.success) {
      accounts.value = res.data || []
    } else {
      throw new Error(res?.message || '获取失败')
    }
  } catch (e) {
    ElMessage.error(e.message || '获取账号列表失败')
  } finally {
    loading.value = false
  }
}

// 添加账号
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
      const message = e.response?.data?.message || e.message || '添加失败，请检查网络连接'
      ElMessage.error(message)
    }
  } finally {
    addLoading.value = false
  }
}

// 打开认证对话框
const openAuthDialog = (account) => {
  currentAccount.value = account
  authActiveTab.value = 'sms'
  Object.assign(authForm, { sms_code: '', token_online: '', app_id: '', custom_app_id: '' })
  showAuthDialog.value = true
}

// 处理认证
const handleAuth = async () => {
  if (!currentAccount.value) return
  authLoading.value = true
  try {
    let res
    if (authActiveTab.value === 'sms') {
      // 验证码登录 - 让后端进行完整验证
      res = await api.post(`/unicom/accounts/${currentAccount.value.id}/login/sms`, {
        sms_code: authForm.sms_code,
        custom_app_id: authForm.custom_app_id
      })
    } else {
      // Token登录 - 让后端进行完整验证
      res = await api.post(`/unicom/accounts/${currentAccount.value.id}/login/token`, {
        token_online: authForm.token_online,
        app_id: authForm.app_id
      })
    }

    // 使用后端返回的消息
    if (res?.success) {
      ElMessage.success(res.message || '认证成功！')
      showAuthDialog.value = false
      await fetchAccounts()
    } else {
      ElMessage.error(res?.message || '认证失败')
    }
  } catch (e) {
    // 处理网络错误或其他异常
    const errorMsg = e.response?.data?.message || e.message || '认证失败，请检查AppID是否正确'
    ElMessage.error(errorMsg)
  } finally {
    authLoading.value = false
  }
}

// 刷新认证
const refreshAuth = async (account) => {
  refreshingIds.value.push(account.id)
  try {
    const res = await api.post(`/unicom/accounts/${account.id}/refresh`)
    if (res?.success) {
      ElMessage.success('认证刷新成功！')
      await fetchAccounts()
    } else {
      ElMessage.error(res?.message || '刷新失败')
    }
  } catch (e) {
    ElMessage.error('刷新失败，请检查网络连接')
  } finally {
    refreshingIds.value = refreshingIds.value.filter(id => id !== account.id)
  }
}

// 账号操作
const handleAccountAction = async (command, account) => {
  if (command === 'copy') {
    try {
      const res = await unicomAPI.getAccount(account.id)
      if (!res?.success) throw new Error(res?.message || '获取账号信息失败')
      copyInfo.token_online = res.data?.token_online || ''
      copyInfo.app_id = res.data?.app_id || res.data?.effective_app_id || ''
      // 延迟打开，避免下拉菜单的点击事件冒泡导致抽屉立即关闭
      setTimeout(() => { showCopyDialog.value = true }, 0)
    } catch (e) {
      ElMessage.error(e.message || '获取失败')
    }
  } else if (command === 'delete') {
    await confirmDelete(account)
  }
}

// 确认删除（公用）
const confirmDelete = async (account) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除账号 ${account.display_name} 吗？`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger'
      }
    )
    const res = await api.delete(`/unicom/accounts/${account.id}`)
    if (res?.success) { ElMessage.success('删除成功'); await fetchAccounts() }
    else { ElMessage.error(res?.message || '删除失败') }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败，请检查网络连接')
  }
}

// 复制功能
const copyText = async (text) => {
  if (!text) return ElMessage.warning('内容为空')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const copyAll = async () => {
  copyLoading.value = true
  try {
    const text = JSON.stringify(copyInfo, null, 2)
    await navigator.clipboard.writeText(text)
    ElMessage.success('全部已复制')
  } catch {
    ElMessage.error('复制失败')
  } finally {
    copyLoading.value = false
  }
}

// 暴露给父组件的方法
defineExpose({
  fetchAccounts
})

// 初始化
onMounted(() => {
  fetchAccounts()
})
</script>

<style scoped>
.code-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  min-width: 100px;
  padding-top: 8px;
}

.mono {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.tip {
  font-size: 12px;
  color: #6b7280;
  background: #f9fafb;
  padding: 12px;
  border-radius: 8px;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
