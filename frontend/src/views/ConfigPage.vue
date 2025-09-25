<template>
  <div class="p-4 md:p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
        配置管理
      </h1>
      <p class="text-gray-600">
        管理您的联通账号和监控配置
      </p>
    </div>

    <!-- 账号管理已迁移至 个人中心（/profile） -->
    <!-- 此处仅保留配置相关内容 -->

    <!-- 1) 缓存与刷新 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="p-6 border-b border-gray-200 flex items-center justify-between cursor-pointer select-none" @click="toggleSection('cache')">
        <div>
          <h2 class="text-lg font-semibold text-gray-900 mb-1">缓存与刷新</h2>
          <p class="text-sm text-gray-600">仅配置手动冷却时间与缓存时间</p>
        </div>
        <el-icon :class="['transition-transform', activeSection==='cache' ? 'rotate-180' : '']"><ArrowDown /></el-icon>
      </div>
      <div class="p-6 space-y-4" v-show="activeSection==='cache'">
        <el-form :model="cacheForm" :label-position="isMobile ? 'top' : 'right'" :label-width="isMobile ? undefined : '150px'">
          <el-form-item label="手动刷新冷却(秒)">
            <div class="flex flex-col sm:flex-row sm:items-center gap-2 w-full">
              <el-input-number v-model="cacheForm.refreshCooldownSeconds" :min="30" :max="3600" :step="10" class="w-full sm:w-56" />
              <div class="text-xs text-gray-500">默认60秒，范围：30秒 ~ 3600秒（1小时）</div>
            </div>
          </el-form-item>
          <el-form-item label="缓存时间(分钟)">
            <div class="flex flex-col sm:flex-row sm:items-center gap-2 w-full">
              <el-input-number v-model="cacheForm.cacheTtlMinutes" :min="5" :max="1440" :step="1" class="w-full sm:w-56" />
              <div class="text-xs text-gray-500">默认10分钟，范围：5分钟 ~ 1440分钟（24小时）</div>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving.cache" @click="saveCacheSettings" class="w-full sm:w-auto h-11">保存</el-button>
          </el-form-item>
        </el-form>
        </div>
    </div>

    <!-- 2) 统计与阈值 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="p-6 border-b border-gray-200 flex items-center justify-between cursor-pointer select-none" @click="toggleSection('alerts')">
        <div>
          <h2 class="text-lg font-semibold text-gray-900 mb-1">统计与阈值</h2>
          <p class="text-sm text-gray-600">配置通用/专用低余量预警、跳点阈值与提醒方式；并设置监控频率</p>
        </div>
        <el-icon :class="['transition-transform', activeSection==='alerts' ? 'rotate-180' : '']"><ArrowDown /></el-icon>
      </div>
      <div class="p-6" v-show="activeSection==='alerts'">
        <el-form :model="alertsForm" :label-position="isMobile ? 'top' : 'right'" :label-width="isMobile ? undefined : '200px'">
          <el-form-item label="监控频率(秒)">
            <div class="flex flex-col sm:flex-row sm:items-center gap-2 w-full">
              <el-input-number v-model="monitorForm.frequencySeconds" :min="60" :max="7200" :step="10" class="w-full sm:w-56" />
              <div class="text-xs text-gray-500">默认300秒（5分钟），范围：60秒 ~ 7200秒（2小时）</div>
            </div>
          </el-form-item>

          <el-form-item label="通用低余量预警">
            <div class="flex flex-col sm:flex-row sm:items-center gap-3 w-full">
              <el-radio-group v-model="alertsForm.general.mode" size="small">
                <el-radio-button label="percent">百分比</el-radio-button>
                <el-radio-button label="gb">GB</el-radio-button>
              </el-radio-group>
              <div class="flex items-center gap-2">
                <el-input-number v-model="alertsForm.general.value"
                                 :min="1"
                                 :max="alertsForm.general.mode==='percent'?100:1000"
                                 :step="alertsForm.general.mode==='percent'?1:0.1"
                                 class="w-full sm:w-28" />
                <span class="text-sm text-gray-500">{{ alertsForm.general.mode === 'percent' ? '%' : 'GB' }}</span>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="专用(免流)低余量预警">
            <div class="flex flex-col sm:flex-row sm:items-center gap-3 w-full">
              <el-radio-group v-model="alertsForm.special.mode" size="small">
                <el-radio-button label="percent">百分比</el-radio-button>
                <el-radio-button label="gb">GB</el-radio-button>
              </el-radio-group>
              <div class="flex items-center gap-2">
                <el-input-number v-model="alertsForm.special.value"
                                 :min="1"
                                 :max="alertsForm.special.mode==='percent'?100:1000"
                                 :step="alertsForm.special.mode==='percent'?1:0.1"
                                 class="w-full sm:w-28" />
                <span class="text-sm text-gray-500">{{ alertsForm.special.mode === 'percent' ? '%' : 'GB' }}</span>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="跳点变化阈值">
            <div class="flex flex-col sm:flex-row sm:items-center gap-3 w-full">
              <div class="flex items-center gap-2 w-full sm:w-auto">
                <el-input-number v-model="alertsForm.jumpDelta.value"
                                 :min="alertsForm.jumpDelta.unit === 'GB' ? 1 : 3"
                                 :step="1"
                                 class="w-full sm:w-28" />
                <el-select v-model="alertsForm.jumpDelta.unit" class="w-24">
                  <el-option label="MB" value="MB" />
                  <el-option label="GB" value="GB" />
                </el-select>
              </div>
              <span class="text-xs text-gray-500">流量跳点累计阈值，最低3MB</span>
            </div>
          </el-form-item>

          <el-form-item>
            <div class="text-xs text-orange-600 bg-orange-50 p-3 rounded-lg border border-orange-200">
              <div class="flex items-start gap-2">
                <el-icon class="text-orange-500 mt-0.5 flex-shrink-0"><Warning /></el-icon>
                <div>
                  <div class="font-medium mb-1">监控通知配置说明：</div>
                  <div>1. 必须在下方"通知方式"中配置并开启至少一种通知方式（如邮件、企业微信等）</div>
                  <div>2. 必须在"个人中心 → 账号管理"中打开对应账号的监控通知开关</div>
                  <div>3. 满足以上条件后，系统会按设定的监控频率自动检测并发送通知</div>
                </div>
              </div>
            </div>
          </el-form-item>

          <el-form-item>
            <div class="flex flex-col sm:flex-row gap-3 w-full">
              <el-button type="primary" :loading="saving.alerts" @click="saveAlertSettings" class="w-full sm:w-auto h-11">保存</el-button>
              <el-button type="warning" plain :loading="saving.clearAlerts" @click="onClearAlertStates" class="w-full sm:w-auto h-11">清空告警状态</el-button>
            </div>
          </el-form-item>
        </el-form>
      </div>
    </div>
    <!-- 通知方式 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="p-6 border-b border-gray-200 flex items-center justify-between cursor-pointer select-none" @click="toggleSection('notifications')">
        <div>
          <h2 class="text-lg font-semibold text-gray-900 mb-1">通知方式</h2>
          <p class="text-sm text-gray-600">配置邮件、企业微信、钉钉、自定义 Webhook、WxPusher 等通知</p>
        </div>
        <el-icon :class="['transition-transform', activeSection==='notifications' ? 'rotate-180' : '']"><ArrowDown /></el-icon>
      </div>
      <div class="p-6" v-show="activeSection==='notifications'">
        <el-form :model="notificationsForm" :label-position="isMobile ? 'top' : 'right'" :label-width="isMobile ? undefined : '180px'">
          <el-collapse>
            <!-- Email SMTP -->
            <el-collapse-item name="email">
              <template #title>
                <div class="flex items-center gap-2">
                  <span>邮件（SMTP）</span>
                  <el-tag v-if="notificationsForm.email.enabled" size="small" type="success" effect="plain">已启用</el-tag>
                </div>
              </template>
              <el-form-item label="启用">
                <el-switch v-model="notificationsForm.email.enabled" />
              </el-form-item>
              <template v-if="notificationsForm.email.enabled">
                <el-form-item label="SMTP服务器">
                  <el-input v-model="notificationsForm.email.smtp_server" placeholder="smtp.qq.com" />
                </el-form-item>
                <el-form-item label="SMTP端口">
                  <el-input-number v-model="notificationsForm.email.smtp_port" :min="1" :max="65535" class="w-full sm:w-56" />
                </el-form-item>
                <el-form-item label="发件邮箱">
                  <el-input v-model="notificationsForm.email.username" placeholder="your_email@qq.com" />
                </el-form-item>
                <el-form-item label="密码/授权码">
                  <el-input v-model="notificationsForm.email.password" type="password" show-password />
                </el-form-item>
                <el-form-item label="收件人">
                  <el-input v-model="notificationsForm.email.to_emails" type="textarea" :rows="2" placeholder="多收件人用逗号或换行分隔" />
                </el-form-item>
              </template>
              <div class="mt-2">
                <el-button size="small" :disabled="!notificationsForm.email.enabled" @click="testNotify('email')">测试发送</el-button>
              </div>
            </el-collapse-item>

            <!-- 企业微信机器人 -->
            <el-collapse-item name="wechat">
              <template #title>
                <div class="flex items-center gap-2">
                  <span>企业微信机器人</span>
                  <el-tag v-if="notificationsForm.wechat.enabled" size="small" type="success" effect="plain">已启用</el-tag>
                </div>
              </template>
              <el-form-item label="启用">
                <el-switch v-model="notificationsForm.wechat.enabled" />
              </el-form-item>
              <template v-if="notificationsForm.wechat.enabled">
                <el-form-item label="Webhook URL">
                  <el-input v-model="notificationsForm.wechat.webhook_url" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
                </el-form-item>
              </template>
              <div class="mt-2">
                <el-button size="small" :disabled="!notificationsForm.wechat.enabled" @click="testNotify('wechat')">测试发送</el-button>
              </div>
            </el-collapse-item>

            <!-- 企业微信应用 -->
            <el-collapse-item name="wechat_app">
              <template #title>
                <div class="flex items-center gap-2">
                  <span>企业微信应用</span>
                  <el-tag v-if="notificationsForm.wechat_app.enabled" size="small" type="success" effect="plain">已启用</el-tag>
                </div>
              </template>
              <el-form-item label="启用">
                <el-switch v-model="notificationsForm.wechat_app.enabled" />
              </el-form-item>
              <template v-if="notificationsForm.wechat_app.enabled">
                <el-form-item label="CorpID">
                  <el-input v-model="notificationsForm.wechat_app.corpid" />
                </el-form-item>
                <el-form-item label="CorpSecret">
                  <el-input v-model="notificationsForm.wechat_app.corpsecret" />
                </el-form-item>
                <el-form-item label="AgentID">
                  <el-input-number v-model="notificationsForm.wechat_app.agentid" :min="1" class="w-full sm:w-56" />
                </el-form-item>
                <el-form-item label="ToUser">
                  <el-input v-model="notificationsForm.wechat_app.touser" placeholder="@all 或 user1|user2" />
                </el-form-item>
              </template>
              <div class="mt-2">
                <el-button size="small" :disabled="!notificationsForm.wechat_app.enabled" @click="testNotify('wechat_app')">测试发送</el-button>
              </div>
            </el-collapse-item>

            <!-- 钉钉机器人 -->
            <el-collapse-item name="dingtalk">
              <template #title>
                <div class="flex items-center gap-2">
                  <span>钉钉机器人</span>
                  <el-tag v-if="notificationsForm.dingtalk.enabled" size="small" type="success" effect="plain">已启用</el-tag>
                </div>
              </template>
              <el-form-item label="启用">
                <el-switch v-model="notificationsForm.dingtalk.enabled" />
              </el-form-item>
              <template v-if="notificationsForm.dingtalk.enabled">
                <el-form-item label="Webhook URL">
                  <el-input v-model="notificationsForm.dingtalk.webhook_url" placeholder="https://oapi.dingtalk.com/robot/send?access_token=..." />
                </el-form-item>
                <el-form-item label="加签Secret">
                  <el-input v-model="notificationsForm.dingtalk.secret" placeholder="可选" />
                </el-form-item>
              </template>
              <div class="mt-2">
                <el-button size="small" :disabled="!notificationsForm.dingtalk.enabled" @click="testNotify('dingtalk')">测试发送</el-button>
              </div>
            </el-collapse-item>

            <!-- 微信电话 -->
            <el-collapse-item name="wechat_call">
              <template #title>
                <div class="flex items-center gap-2">
                  <span>微信电话</span>
                  <el-tag v-if="notificationsForm.wechat_call.enabled" size="small" type="success" effect="plain">已启用</el-tag>
                </div>
              </template>
              <el-form-item label="启用">
                <el-switch v-model="notificationsForm.wechat_call.enabled" />
              </el-form-item>
              <template v-if="notificationsForm.wechat_call.enabled">
                <el-form-item label="API地址">
                  <el-input v-model="notificationsForm.wechat_call.api_url" />
                </el-form-item>
                <el-form-item label="机器人ID">
                  <el-input v-model="notificationsForm.wechat_call.robot_id" />
                </el-form-item>
                <el-form-item label="目标微信ID">
                  <el-input v-model="notificationsForm.wechat_call.target_wxid" />
                </el-form-item>
                <el-form-item label="服务器ID">
                  <el-input v-model="notificationsForm.wechat_call.server_id" placeholder="可留空" />
                </el-form-item>
                <el-form-item label="Token">
                  <el-input v-model="notificationsForm.wechat_call.token" placeholder="JWT token (系统会自动添加Bearer前缀)" />
                </el-form-item>
              </template>
              <div class="mt-2">
                <el-button size="small" :disabled="!notificationsForm.wechat_call.enabled" @click="testNotify('wechat_call')">测试发送</el-button>
              </div>
            </el-collapse-item>

            <!-- 自定义 Webhook -->
            <el-collapse-item name="webhook">
              <template #title>
                <div class="flex items-center gap-2">
                  <span>自定义 Webhook</span>
                  <el-tag v-if="notificationsForm.webhook.enabled" size="small" type="success" effect="plain">已启用</el-tag>
                </div>
              </template>
              <el-form-item label="启用">
                <el-switch v-model="notificationsForm.webhook.enabled" />
              </el-form-item>
              <template v-if="notificationsForm.webhook.enabled">
                <el-form-item label="请求方法">
                  <el-select v-model="notificationsForm.webhook.method" class="w-full sm:w-40">
                    <el-option label="POST" value="POST" />
                    <el-option label="GET" value="GET" />
                  </el-select>
                </el-form-item>
                <el-form-item label="请求URL">
                  <el-input v-model="notificationsForm.webhook.url" />
                </el-form-item>
                <el-form-item label="Headers(JSON)">
                  <el-input v-model="notificationsForm.webhook.headers" type="textarea" :rows="3" placeholder='{"Content-Type":"application/json"}' />
                </el-form-item>
                <el-form-item label="Params(JSON)">
                  <el-input v-model="notificationsForm.webhook.params" type="textarea" :rows="3" placeholder="{}" />
                </el-form-item>
                <el-form-item label="Body(JSON)">
                  <el-input v-model="notificationsForm.webhook.body" type="textarea" :rows="4" placeholder="{}" />
                </el-form-item>
                <div class="text-xs text-gray-500 mb-2">以上 textarea 填写 JSON 字符串，发送前端将原样保存</div>
              </template>
              <div class="mt-2">
                <el-button size="small" :disabled="!notificationsForm.webhook.enabled" @click="testNotify('webhook')">测试发送</el-button>
              </div>
            </el-collapse-item>


            <!-- Bark iOS -->
            <el-collapse-item name="bark">
              <template #title>
                <div class="flex items-center gap-2">
                  <span>Bark（iOS）</span>
                  <el-tag v-if="notificationsForm.bark.enabled" size="small" type="success" effect="plain">已启用</el-tag>
                </div>
              </template>
              <el-form-item label="启用">
                <el-switch v-model="notificationsForm.bark.enabled" />
              </el-form-item>
              <template v-if="notificationsForm.bark.enabled">
                <el-form-item label="服务器">
                  <el-input v-model="notificationsForm.bark.server" placeholder="https://api.day.app" />
                </el-form-item>
                <el-form-item label="Device Keys">
                  <el-input v-model="notificationsForm.bark.device_keys" type="textarea" :rows="2" placeholder="每行一个Key，或用逗号分隔" />
                </el-form-item>
                <el-form-item label="分组">
                  <el-input v-model="notificationsForm.bark.group" placeholder="可选" />
                </el-form-item>
                <el-form-item label="声音">
                  <el-input v-model="notificationsForm.bark.sound" placeholder="可选，示例：alarm" />
                </el-form-item>
                <el-form-item label="存档">
                  <el-switch v-model="notificationsForm.bark.isArchive" />
                </el-form-item>
              </template>
              <div class="mt-2">
                <el-button size="small" :disabled="!notificationsForm.bark.enabled" @click="testNotify('bark')">测试发送</el-button>
              </div>
            </el-collapse-item>

            <!-- WxPusher -->
            <el-collapse-item name="wxpusher">
              <template #title>
                <div class="flex items-center gap-2">
                  <span>WxPusher</span>
                  <el-tag v-if="notificationsForm.wxpusher.enabled" size="small" type="success" effect="plain">已启用</el-tag>
                </div>
              </template>
              <el-form-item label="启用">
                <el-switch v-model="notificationsForm.wxpusher.enabled" />
              </el-form-item>
              <template v-if="notificationsForm.wxpusher.enabled">
                <el-form-item label="扫码绑定UID">
                  <div class="flex flex-col sm:flex-row sm:items-center gap-3 w-full">
                    <div class="flex items-center gap-2">
                      <el-button type="primary" class="h-11" :loading="qrLoading" @click="createWxQr">生成绑定二维码</el-button>
                      <el-button v-if="wxQr.polling" class="h-11" @click="stopWxQrPolling">停止轮询</el-button>
                    </div>
                    <div v-if="wxQr.url" class="flex items-center gap-3">
                      <img :src="wxQr.url" alt="WxPusher二维码" class="w-32 h-32 border rounded" />
                      <div class="text-xs text-gray-500">
                        请使用微信扫码关注；系统将每10秒查询一次是否获取到UID。
                        <div v-if="wxQr.expireTime">有效期至：{{ new Date(wxQr.expireTime).toLocaleString() }}</div>
                      </div>
                    </div>
                    <div v-else class="text-xs text-gray-500">点击“生成绑定二维码”，用户扫码后会自动回填UID。</div>
                  </div>
                </el-form-item>
                <el-form-item label="UID列表">
                  <el-input v-model="notificationsForm.wxpusher.uids" type="textarea" :rows="2" placeholder="每行一个UID，或用逗号分隔" />
                </el-form-item>
                <div class="mt-2">
                  <el-button size="small" :disabled="!notificationsForm.wxpusher.enabled" @click="testNotify('wxpusher')">测试发送</el-button>
                </div>

              </template>
            </el-collapse-item>
          </el-collapse>

          <el-form-item>
            <el-button type="primary" :loading="saving.notifications" @click="saveNotificationsSettings" class="w-full sm:w-auto h-11">保存</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 3) 展示与偏好 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="p-6 border-b border-gray-200 flex items-center justify-between cursor-pointer select-none" @click="toggleSection('display')">
        <div>
          <h2 class="text-lg font-semibold text-gray-900 mb-1">展示与偏好</h2>
          <p class="text-sm text-gray-600">仅配置首页默认账号</p>
        </div>
        <el-icon :class="['transition-transform', activeSection==='display' ? 'rotate-180' : '']"><ArrowDown /></el-icon>
      </div>
      <div class="p-6" v-show="activeSection==='display'">
        <el-form :model="displayForm" :label-position="isMobile ? 'top' : 'right'" :label-width="isMobile ? undefined : '180px'">
          <el-form-item label="首页默认账号">
            <el-select v-model="displayForm.defaultAccountId" placeholder="选择默认账号" clearable class="w-full sm:w-80">
              <el-option v-for="acc in accounts" :key="acc.id" :label="acc.display_name + '（' + acc.phone + '）'" :value="acc.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving.display" @click="saveDisplaySettings" class="w-full sm:w-auto h-11">保存</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>





  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Iphone, Loading, MoreFilled, Refresh, Close, Document, ArrowDown, Warning
} from '@/utils/icons'
import { api, notifyAPI, settingsAPI, unicomAPI } from '@/utils/api'
import MobileSheet from '@/components/MobileSheet.vue'

// 响应式数据
import { storage } from '@/utils/storage'


const accounts = ref([])
const loading = ref(false)

// H5 自适应：根据窗口宽度切换表单 label 布局
const isMobile = ref(typeof window !== 'undefined' ? window.innerWidth < 640 : true)
const updateIsMobile = () => { if (typeof window !== 'undefined') isMobile.value = window.innerWidth < 640 }
onMounted(() => { updateIsMobile(); if (typeof window !== 'undefined') window.addEventListener('resize', updateIsMobile) })
onBeforeUnmount(() => { if (typeof window !== 'undefined') window.removeEventListener('resize', updateIsMobile) })

// 手风琴：配置页仅允许一个版块展开，可点已展开标题关闭
const activeSection = ref('cache')
const toggleSection = (key) => {
  activeSection.value = activeSection.value === key ? '' : key
}


const toggleLoadingIds = ref([])

const onToggleMonitor = async (account, val) => {
  // 未认证账号不允许开启监控
  if (val && !account.is_auth_valid) {
    ElMessage.error('账号未认证或已过期，无法开启监控')
    account.monitor_enabled = false
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

const showAddDialog = ref(false)
const showAuthDialogVisible = ref(false)
const addLoading = ref(false)
const authLoading = ref(false)
const currentAccount = ref(null)
const authActiveTab = ref('sms')
const refreshingIds = ref([])


// 复制信息弹窗 - 状态
const showCopyDialog = ref(false)
const copyLoading = ref(false)
const copyInfo = reactive({ token_online: '', app_id: '' })

// 工具：复制到剪贴板
const copyText = async (text) => {
  try {
    copyLoading.value = true
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text || '')
    } else {
      const ta = document.createElement('textarea')
      ta.value = text || ''
      document.body.appendChild(ta)
      ta.select(); document.execCommand('copy'); document.body.removeChild(ta)
    }
    ElMessage.success('已复制到剪贴板')
  } catch (e) {
    ElMessage.error('复制失败')
  } finally {
    copyLoading.value = false
  }
}

// 一键复制全部
const copyAll = () => {
  const payload = JSON.stringify({ token_online: copyInfo.token_online, app_id: copyInfo.app_id }, null, 2)
  copyText(payload)
}


// ===== 设置：默认值与表单（顶层，供模板使用） =====
const defaultSettings = {
  cache: { refreshCooldownSeconds: 60, cacheTtlMinutes: 10 },
  monitor: { frequencySeconds: 300 },
  alerts: {
    general: { mode: 'gb', value: 1 },
    special: { mode: 'gb', value: 1 },
    jumpDelta: { unit: 'MB', value: 3 },
    notify: { inPage: true, browser: false, sound: false }
  },
  notifications: {
    email: { enabled: false, smtp_server: '', smtp_port: 587, username: '', password: '', to_emails: '' },

    wechat: { enabled: false, webhook_url: '' },
    wechat_app: { enabled: false, corpid: '', corpsecret: '', agentid: null, touser: '' },
    dingtalk: { enabled: false, webhook_url: '', secret: '' },
    wechat_call: { enabled: false, api_url: '', robot_id: '', target_wxid: '', server_id: '', token: '' },
    webhook: { enabled: false, method: 'POST', url: '', headers: '{}', params: '{}', body: '{}' },
    bark: { enabled: false, server: 'https://api.day.app', device_keys: '', group: '', sound: '', isArchive: true },
    wxpusher: { enabled: false, uids: '', content_type: 1 }
  },
  display: { defaultAccountId: null }
}

const cacheForm = reactive({ refreshCooldownSeconds: 60, cacheTtlMinutes: 10 })
const monitorForm = reactive({ frequencySeconds: 300 })
const alertsForm = reactive({
  general: { mode: 'gb', value: 1 },
  special: { mode: 'gb', value: 1 },
  jumpDelta: { unit: 'MB', value: 3 },
  notify: reactive({ inPage: true, browser: false, sound: false })
})
const notificationsForm = reactive(JSON.parse(JSON.stringify(defaultSettings.notifications)))
const alertsEnabled = reactive({
  low: { general: true, special: true },
  jump: { general: true, special: true }
})

const displayForm = reactive({ defaultAccountId: null })

const saving = reactive({ cache: false, monitor: false, alerts: false, notifications: false, display: false, clearAlerts: false })

// WxPusher 扫码绑定逻辑
const qrLoading = ref(false)
const wxQr = reactive({ code: '', url: '', expireTime: null, polling: false, timer: null })

const stopWxQrPolling = () => {
  if (wxQr.timer) { clearInterval(wxQr.timer); wxQr.timer = null }
  wxQr.polling = false
}

const pollWxScan = async () => {
  if (!wxQr.code) return
  try {
    const res = await notifyAPI.queryWxPusherScan(wxQr.code)
    if (res?.success && Array.isArray(res.uids) && res.uids.length > 0) {
      const existing = (notificationsForm.wxpusher.uids || '').split(/[\n,]+/).map(s => s.trim()).filter(Boolean)
      const set = new Set(existing)
      res.uids.forEach(u => { if (u) set.add(u) })
      notificationsForm.wxpusher.uids = Array.from(set).join('\n')
      ElMessage.success('已获取UID，已加入列表')
      stopWxQrPolling()
    }
  } catch (e) {
    // 静默失败，继续轮询
  }
}

const createWxQr = async () => {
  qrLoading.value = true
  try {
    const res = await notifyAPI.createWxPusherQr({ extra: `bind_${Date.now()}`, validTime: 600 })
    if (res?.success) {
      wxQr.code = res.code
      wxQr.url = res.url
      wxQr.expireTime = res.expireTime || null
      ElMessage.success('二维码已生成，请使用微信扫码关注')
      stopWxQrPolling()
      wxQr.polling = true
      wxQr.timer = setInterval(pollWxScan, 10000) // 文档要求≥10秒
    } else {
      ElMessage.error(res?.message || '生成二维码失败')
    }
  } catch (e) {
    ElMessage.error('生成二维码失败')
  } finally {
    qrLoading.value = false
  }
}

onBeforeUnmount(() => { stopWxQrPolling() })

// 实时保存（防抖）
const debounce = (fn, delay = 500) => {
  let t
  return (...args) => {
    clearTimeout(t)
    t = setTimeout(() => fn(...args), delay)
  }
}

const saveCacheDebounced = debounce(() => {
  storage.updateSettings({ cache: { ...cacheForm } })
}, 500)
const saveMonitorDebounced = debounce(() => {
  storage.updateSettings({ monitor: { ...monitorForm } })
}, 500)
const saveAlertsDebounced = debounce(() => {
  const plain = JSON.parse(JSON.stringify(alertsForm))
  storage.updateSettings({ alerts: plain })
}, 500)
const saveNotificationsDebounced = debounce(() => {
  const plain = JSON.parse(JSON.stringify(notificationsForm))
  storage.updateSettings({ notifications: plain })
}, 500)
const saveDisplayDebounced = debounce(() => {
  storage.updateSettings({ display: { ...displayForm } })
}, 500)

watch(cacheForm, saveCacheDebounced, { deep: true })
watch(monitorForm, saveMonitorDebounced, { deep: true })
watch(alertsForm, saveAlertsDebounced, { deep: true })
watch(notificationsForm, saveNotificationsDebounced, { deep: true })
watch(displayForm, saveDisplayDebounced, { deep: true })


const loadSettings = () => {
  const s = storage.getSettings() || {}
  const merged = {
    cache: { ...defaultSettings.cache, ...(s.cache || {}) },
    monitor: { ...defaultSettings.monitor, ...(s.monitor || {}) },
    alerts: {
      general: { ...defaultSettings.alerts.general, ...(((s.alerts || {}).general) || {}) },
      special: { ...defaultSettings.alerts.special, ...(((s.alerts || {}).special) || {}) },
      jumpDelta: { ...defaultSettings.alerts.jumpDelta, ...(((s.alerts || {}).jumpDelta) || {}) },
      notify: { ...defaultSettings.alerts.notify, ...(((s.alerts || {}).notify) || {}) }
    },
    notifications: { ...defaultSettings.notifications, ...(s.notifications || {}) },
    display: { ...defaultSettings.display, ...(s.display || {}) }
  }
  Object.assign(cacheForm, merged.cache)
  Object.assign(monitorForm, merged.monitor)


  Object.assign(alertsForm.general, merged.alerts.general)
  Object.assign(alertsForm.special, merged.alerts.special)
  Object.assign(alertsForm.jumpDelta, merged.alerts.jumpDelta)
  Object.assign(alertsForm.notify, merged.alerts.notify)

  Object.assign(notificationsForm, merged.notifications)
  Object.assign(displayForm, merged.display)
}

// 从服务端读取缓存配置并回显
const fetchServerCache = async () => {
  try {
    const res = await settingsAPI.getCache()
    if (res?.success && res.data) {
      if (typeof res.data.refreshCooldownSeconds === 'number') {
        cacheForm.refreshCooldownSeconds = res.data.refreshCooldownSeconds
      }
      if (typeof res.data.cacheTtlMinutes === 'number') {
        cacheForm.cacheTtlMinutes = res.data.cacheTtlMinutes
      }
      // 同步一份到本地存储，便于离线/回退
      storage.updateSettings({ cache: { ...cacheForm } })
    }
  } catch (e) {
    // 忽略错误，保持本地默认/缓存
  }
}


const saveCacheSettings = async () => {
  saving.cache = true
  try {
    // 前端约束：冷却30秒~3600秒，TTL 5分钟~1440分钟
    const payload = {
      refreshCooldownSeconds: Math.min(3600, Math.max(30, Number(cacheForm.refreshCooldownSeconds) || 60)),
      cacheTtlMinutes: Math.min(1440, Math.max(5, Number(cacheForm.cacheTtlMinutes) || 10))
    }
    const res = await settingsAPI.saveCache(payload)
    if (res?.success) {
      // 以服务端返回为准进行回显
      if (res.data?.refreshCooldownSeconds) cacheForm.refreshCooldownSeconds = res.data.refreshCooldownSeconds
      if (res.data?.cacheTtlMinutes) cacheForm.cacheTtlMinutes = res.data.cacheTtlMinutes
      // 同步到本地存储，便于离线/回退
      storage.updateSettings({ cache: { ...cacheForm } })
      ElMessage.success('缓存设置已保存')
    } else {
      ElMessage.error(res?.message || '保存失败')
    }
  } catch (e) {
    // 忽略错误
  } finally {
    saving.cache = false
  }
}

const fetchServerMonitor = async () => {
  try {
    const res = await settingsAPI.getMonitor()
    if (res?.success && res.data) {
      const fs = Number(res.data.frequencySeconds)
      if (!isNaN(fs)) {
        monitorForm.frequencySeconds = Math.min(7200, Math.max(60, fs))
      }
      storage.updateSettings({ monitor: { ...monitorForm } })
    }
  } catch (e) {
    // 忽略错误，保留本地默认
  }
}

const fetchServerAlerts = async () => {
  try {
    const res = await settingsAPI.getAlerts()
    // 如果服务端返回空对象（{}），视为无变更，不覆盖本地/默认
    if (!(res?.success)) return
    const hasServerData = res && res.data && (res.data.low || res.data.jump)
    if (!hasServerData) return

    const low = res.data.low || {}
    const jmp = res.data.jump || {}
    const lg = low.general || {}
    const ls = low.special || {}
    alertsEnabled.low.general = lg.enabled !== false
    alertsEnabled.low.special = !!ls.enabled
    alertsForm.general.mode = (lg.mode || 'gb')
    alertsForm.general.value = typeof lg.value === 'number' ? lg.value : 1
    alertsForm.special.mode = (ls.mode || 'gb')
    alertsForm.special.value = typeof ls.value === 'number' ? ls.value : 1
    const jg = jmp.general || {}
    const js = jmp.special || {}
    alertsEnabled.jump.general = jg.enabled !== false
    alertsEnabled.jump.special = js.enabled !== false
    let thMB = Number(jg.thresholdMB || js.thresholdMB || 3)
    if (!isNaN(thMB) && thMB >= 1024 && thMB % 1024 === 0) {
      alertsForm.jumpDelta.unit = 'GB'
      alertsForm.jumpDelta.value = thMB / 1024
    } else {
      alertsForm.jumpDelta.unit = 'MB'
      alertsForm.jumpDelta.value = isNaN(thMB) ? 3 : thMB
    }
    storage.updateSettings({ alerts: JSON.parse(JSON.stringify(alertsForm)) })
  } catch (e) {
    // 忽略错误
  }
}

// 服务端：读取通知方式配置
const fetchServerNotifications = async () => {
  try {
    const res = await settingsAPI.getNotifications()
    if (res?.success && res.data) {
      Object.assign(notificationsForm, res.data)
      storage.updateSettings({ notifications: JSON.parse(JSON.stringify(notificationsForm)) })
    }
  } catch (e) {}
}

// 服务端：读取展示偏好配置
const fetchServerDisplay = async () => {
  try {
    const res = await settingsAPI.getDisplay()
    if (res?.success && res.data) {
      if (typeof res.data.defaultAccountId !== 'undefined') {
        displayForm.defaultAccountId = res.data.defaultAccountId
      }
      storage.updateSettings({ display: { ...displayForm } })
    }
  } catch (e) {}
}



const saveAlertSettings = async () => {
  saving.alerts = true
  try {
    // 1) 保存监控频率
    const freq = Math.min(7200, Math.max(60, Number(monitorForm.frequencySeconds) || 300))
    const mRes = await settingsAPI.saveMonitor({ frequencySeconds: freq })
    if (mRes?.success && mRes.data?.frequencySeconds) {
      monitorForm.frequencySeconds = mRes.data.frequencySeconds
    }

    // 2) 组装并保存告警
    // 跳点阈值验证：GB最低1，MB最低3
    const jumpValue = Number(alertsForm.jumpDelta.value) || 0
    const minValue = alertsForm.jumpDelta.unit === 'GB' ? 1 : 3
    const validatedJumpValue = Math.max(minValue, jumpValue)

    const thMB = alertsForm.jumpDelta.unit === 'GB'
      ? validatedJumpValue * 1024
      : validatedJumpValue

    // 余量预警值验证：最低1，最高100%或1000GB
    const generalValue = Math.max(1, Math.min(
      alertsForm.general.mode === 'percent' ? 100 : 1000,
      Number(alertsForm.general.value) || 1
    ))
    const specialValue = Math.max(1, Math.min(
      alertsForm.special.mode === 'percent' ? 100 : 1000,
      Number(alertsForm.special.value) || 1
    ))

    const alertsPayload = {
      low: {
        general: { enabled: alertsEnabled.low.general, mode: alertsForm.general.mode, value: generalValue },
        special: { enabled: alertsEnabled.low.special, mode: alertsForm.special.mode, value: specialValue }
      },
      jump: {
        general: { enabled: alertsEnabled.jump.general, thresholdMB: thMB },
        special: { enabled: alertsEnabled.jump.special, thresholdMB: thMB }
      }
    }
    const aRes = await settingsAPI.saveAlerts(alertsPayload)
    if (aRes?.success) {
      ElMessage.success('统计与阈值设置已保存')
      storage.updateSettings({
        monitor: { ...monitorForm },
        alerts: JSON.parse(JSON.stringify(alertsForm))
      })
    } else {
      ElMessage.error(aRes?.message || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.alerts = false
  }
}

const onClearAlertStates = async () => {
  try {
    await ElMessageBox.confirm('将清空本用户的“低余量已通知”和“跳点基线”，确认继续？', '确认操作', { type: 'warning', confirmButtonText: '清空', cancelButtonText: '取消' })
  } catch (e) {
    return
  }
  saving.clearAlerts = true
  try {
    const res = await settingsAPI.clearAlerts({})
    if (res?.success) {
      const cnt = (res.data && (res.data.deleted ?? 0)) || 0
      ElMessage.success(`已清空（删除键：${cnt}）`)
    } else {
      ElMessage.error(res?.message || '清空失败')
    }
  } catch (e) {
    ElMessage.error('清空失败')
  } finally {
    saving.clearAlerts = false
  }
}


const saveNotificationsSettings = async () => {
  saving.notifications = true
  try {
    const plain = JSON.parse(JSON.stringify(notificationsForm))
    const res = await settingsAPI.saveNotifications(plain)
    if (res?.success) {
      storage.updateSettings({ notifications: plain })
      ElMessage.success('通知方式设置已保存')
    } else {
      ElMessage.error(res?.message || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.notifications = false
  }
}





const saveDisplaySettings = async () => {
  saving.display = true
  try {
    const payload = { ...displayForm }
    const res = await settingsAPI.saveDisplay(payload)
    if (res?.success) {
      storage.updateSettings({ display: { ...displayForm } })
      ElMessage.success('展示与偏好设置已保存')
    } else {
      ElMessage.error(res?.message || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.display = false
  }
}

// 表单引用
const addFormRef = ref()


// 测试发送入口（后端统一接口）
const testNotify = async (channel) => {
  try {
    let settings = {}
    const title = '测试通知'
    const content = `这是一条测试通知 - ${channel}`
    switch (channel) {
      case 'email': settings = notificationsForm.email; break
      case 'wechat': settings = notificationsForm.wechat; break
      case 'wechat_app': settings = notificationsForm.wechat_app; break
      case 'dingtalk': settings = notificationsForm.dingtalk; break
      case 'webhook': settings = notificationsForm.webhook; break
      case 'bark': settings = notificationsForm.bark; break
      case 'wxpusher': settings = { uids: notificationsForm.wxpusher.uids }; break
      case 'wechat_call': settings = notificationsForm.wechat_call; break
      default:
        ElMessage.warning('暂不支持的测试渠道')
        return
    }
    const res = await notifyAPI.sendTest(channel, JSON.parse(JSON.stringify(settings)), title, content)
    if (res?.success) {
      ElMessage.success('测试发送成功')
    } else {
      ElMessage.error(res?.message || '测试发送失败')
    }
  } catch (e) {
    ElMessage.error('测试发送异常')
  }
}

// 添加表单
const addForm = reactive({
  phone: '',
  phone_alias: '',
  custom_app_id: ''
})

// 认证表单
const authForm = reactive({
  sms_code: '',
  token_online: '',
  app_id: ''
})

// 表单验证规则
const addRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
  ]
}

// 获取账号列表
const fetchAccounts = async () => {
  loading.value = true
  try {
    const response = await api.get('/unicom/accounts')
    if (response.success) {
      accounts.value = response.data
    } else {
      ElMessage.error(response.message || '获取账号列表失败')
    }
  } catch (error) {
    console.error('获取联通账号列表失败:', error)
    ElMessage.error('获取账号列表失败，请检查网络连接')
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

    const response = await api.post('/unicom/accounts', addForm)
    if (response.success) {
      ElMessage.success('联通账号添加成功！请进行认证以开始使用。')
      showAddDialog.value = false
      // 重置表单
      Object.assign(addForm, {
        phone: '',
        phone_alias: '',
        custom_app_id: ''
      })
      // 重新获取列表
      await fetchAccounts()

      // 自动打开认证对话框
      const newAccount = response.data
      if (newAccount) {
        setTimeout(() => {
          openAuthDialog(newAccount)
        }, 500)
      }
    } else {
      ElMessage.error(response.message || '添加失败')
    }
  } catch (error) {
    if (error.errors) {
      // 表单验证失败
      console.error('表单验证失败:', error)
    } else {
      console.error('添加联通账号失败:', error)
      ElMessage.error('添加失败，请检查网络连接')
    }
  } finally {
    addLoading.value = false
  }
}

// 打开认证对话框
const openAuthDialog = (account) => {
  currentAccount.value = account
  authActiveTab.value = 'sms'
  // 重置表单
  Object.assign(authForm, {
    sms_code: '',
    token_online: '',
    app_id: ''
  })
  showAuthDialogVisible.value = true
}

// 处理认证
const handleAuth = async () => {
  if (!currentAccount.value) return

  authLoading.value = true
  try {
    let response

    if (authActiveTab.value === 'sms') {
      if (!authForm.sms_code.trim()) {
        ElMessage.error('请输入验证码')
        return
      }
      response = await api.post(`/unicom/accounts/${currentAccount.value.id}/login/sms`, {
        sms_code: authForm.sms_code
      })
    } else {
      if (!authForm.token_online.trim() || !authForm.app_id.trim()) {
        ElMessage.error('请输入Token Online和App ID')
        return
      }
      response = await api.post(`/unicom/accounts/${currentAccount.value.id}/login/token`, {
        token_online: authForm.token_online,
        app_id: authForm.app_id
      })
    }

    if (response.success) {
      ElMessage.success('认证成功！')
      showAuthDialogVisible.value = false
      await fetchAccounts()
    } else {
      ElMessage.error(response.message || '认证失败')
    }
  } catch (error) {
    console.error('认证失败:', error)
    ElMessage.error('认证失败，请检查网络连接')
  } finally {
    authLoading.value = false
  }
}

// 刷新认证
const refreshAuth = async (account) => {
  refreshingIds.value.push(account.id)
  try {
    const response = await api.post(`/unicom/accounts/${account.id}/refresh`)
    if (response.success) {
      ElMessage.success('认证刷新成功！')
      await fetchAccounts()
    } else {
      ElMessage.error(response.message || '刷新失败')
    }
  } catch (error) {
    console.error('刷新认证失败:', error)
    ElMessage.error('刷新失败，请检查网络连接')
  } finally {
    refreshingIds.value = refreshingIds.value.filter(id => id !== account.id)
  }
}

// 处理账号操作
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
      await ElMessageBox.confirm(
        `确定要删除联通账号 ${account.display_name} 吗？`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )

      const response = await api.delete(`/unicom/accounts/${account.id}`)
      if (response.success) {
        ElMessage.success('删除成功！')
        await fetchAccounts()
      } else {
        ElMessage.error(response.message || '删除失败')
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除联通账号失败:', error)
        ElMessage.error('删除失败，请检查网络连接')
      }
    }
  }
}

// 页面加载时获取数据
onMounted(() => {


  fetchAccounts()
})

// 加载本地设置并从服务端回显真实时间
onMounted(() => {
  loadSettings()
  fetchServerCache()
  fetchServerMonitor()
  fetchServerAlerts()
  fetchServerNotifications()
  fetchServerDisplay()
})

</script>

<style scoped>
.vertical-label { writing-mode: vertical-rl; text-orientation: mixed; font-size: 12px; letter-spacing: 0.15em; }

/* 复制信息弹窗美化 */
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

/* H5 自适配 */
@media (max-width: 640px) {
  .copy-dialog .code-row { flex-direction: column; }
  .copy-dialog .label { width:auto; min-width:unset; padding-top:0; }
}
</style>

