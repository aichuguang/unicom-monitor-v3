<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 主要内容 -->
    <main class="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <!-- 手机号选择 -->
      <div class="mb-6">
        <div class="glass-card p-3">
          <h3 class="text-lg font-semibold text-gray-800 mb-2">选择手机号</h3>
          <div
            v-if="authenticatedAccounts.length === 0"
            class="text-center py-8"
          >
            <el-icon :size="48" class="text-gray-300">
              <Phone />
            </el-icon>
            <h4 class="text-lg font-medium text-gray-900 mt-4">
              {{ accounts.length === 0 ? '暂无手机号' : '暂无已认证手机号' }}
            </h4>
            <p class="text-gray-500 mt-2">
              {{ accounts.length === 0 ? '请先添加手机号' : '请先认证已添加的手机号' }}
            </p>
            <el-button
              type="primary"
              @click="$router.push('/profile')"
              class="mt-4"
            >
              <el-icon class="mr-2"><Plus /></el-icon>
              {{ accounts.length === 0 ? '去添加手机号' : '去认证手机号' }}
            </el-button>
          </div>
          <div v-else>
            <el-select
              v-model="selectedAccountId"
              placeholder="请选择已认证的手机号"
              size="large"
              class="w-full"
              @change="onAccountChange"
            >
              <el-option
                v-for="account in authenticatedAccounts"
                :key="account.id"
                :label="`${account.phone} ${
                  account.phone_alias ? '(' + account.phone_alias + ')' : ''
                }`"
                :value="account.id"
              >
                <div class="flex items-center justify-between w-full">
                  <span>{{ account.phone }}</span>
                  <span
                    v-if="account.phone_alias"
                    class="text-gray-500 text-sm"
                    >{{ account.phone_alias }}</span
                  >
                </div>
              </el-option>
            </el-select>
          </div>
        </div>
      </div>

      <!-- 流量信息展示 -->
      <div v-if="selectedAccount" class="space-y-6">
        <!-- 手机号信息卡片 -->
        <div class="glass-card p-3">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center space-x-3">
              <div
                class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center"
              >
                <el-icon class="text-white" :size="16">
                  <Phone />
                </el-icon>
              </div>
              <div>
                <h3 class="text-sm font-semibold text-gray-900">
                  {{ selectedAccount.phone }}
                </h3>
                <div class="flex items-center space-x-2">
                  <p
                    v-if="selectedAccount.phone_alias"
                    class="text-xs text-gray-500"
                  >
                    {{ selectedAccount.phone_alias }}
                  </p>
                  <el-tag type="success" size="small" class="text-xs"
                    >已认证</el-tag
                  >
                </div>
              </div>
            </div>


          </div>



          <div v-if="lastQueryTime" class="text-xs text-gray-500">
            <div>
              <span class="text-xs text-gray-500"
                >实时查询时间: {{ getQueryTime() }}</span
              >
            </div>
            <span v-if="!canRefresh && refreshCountdown > 0" class="ml-2 text-orange-500">
              ({{ refreshCountdown }}秒后可再次刷新)
            </span>
          </div>
                      <!-- 操作按钮：中等尺寸，避免超出；用包裹元素去掉 Element Plus 默认相邻按钮 margin-left -->
                      <div class="grid grid-cols-2 gap-2 mt-2">
              <div>
                <el-button
                  type="primary"
                  size="medium"
                  class="w-full rounded-lg"
                  :loading="singleQueryLoading"
                  :disabled="!canRefresh"
                  @click="querySingleFlow(true)"
                >
                  <el-icon class="mr-1"><Refresh /></el-icon>
                  {{ singleQueryLoading ? "查询中..." : "实时刷新" }}
                </el-button>
              </div>

              <!-- 统计重置按钮 -->
              <div>
                <el-button
                  type="warning"
                  size="medium"
                  class="w-full rounded-lg"
                  :loading="isResettingBaseline"
                  :disabled="singleQueryLoading || isResettingBaseline"
                  @click="resetFlowBaseline"
                  title="重置流量统计基准点，清空跳点等变化数据"
                >
                  <el-icon class="mr-1"><RefreshLeft /></el-icon>
                  {{ isResettingBaseline ? "重置中..." : "统计重置" }}
                </el-button>
              </div>
            </div>
        </div>

        <!-- 流量数据展示 -->
        <div v-if="singleQueryLoading" class="glass-card p-8">
          <div class="text-center">
            <el-icon class="animate-spin" color="blue" :size="48">
              <Loading />
            </el-icon>
            <p class="text-gray-500 mt-4">正在查询流量信息...</p>
          </div>
        </div>

        <div v-else-if="selectedFlowData" class="space-y-3">
          <!-- 套餐信息：按钮下、流量上方（美化） -->
          <div class="glass-card p-3 shadow-sm hover:shadow-md transition-shadow">
            <div class="flex items-center">
              <div class="w-9 h-9 rounded-lg mr-3 bg-gradient-to-r from-indigo-500 to-blue-500 text-white flex items-center justify-center">
                <el-icon><Document /></el-icon>
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-sm font-semibold text-gray-900 truncate">{{ getPackageDisplayName() || '未知套餐' }}</div>
                <div class="text-xs text-gray-500">套餐ID：{{ getPackageId() || '-' }}</div>
              </div>
              <span class="ml-3 px-2 py-0.5 rounded-full text-[10px] bg-indigo-50 text-indigo-600">当前套餐</span>
            </div>
          </div>

          <!-- 流量概览 -->
          <div class="glass-card p-3">
            <div class="grid grid-cols-2 gap-4">
              <div class="text-center">
                <div class="text-xl font-bold text-red-600">
                  {{ formatMB(selectedFlowData?.flow_info?.used_flow) }}
                </div>
                <div class="text-sm text-gray-600">已用</div>
              </div>
              <div class="text-center">
                <div class="text-xl font-bold text-green-600">
                  {{ formatMB(getFreeFlowUsed()) }}
                </div>
                <div class="text-sm text-gray-600">已免</div>
              </div>
            </div>

            <!-- 流量变化对比 -->
            <div class="mt-3 pt-2 border-t border-gray-100">
              <div class="grid grid-cols-3 gap-2 text-xs">
                <div class="text-center">
                  <div class="text-gray-500 mb-1">距统计重置已用</div>
                  <div class="font-medium text-blue-600">
                    {{ getFlowChangeUsed() }}
                  </div>
                </div>
                <div class="text-center">
                  <div class="text-gray-500 mb-1">已免</div>
                  <div class="font-medium text-green-600">
                    {{ getFlowChangeFree() }}
                  </div>
                </div>
                <div class="text-center">
                  <div class="text-gray-500 mb-1">跳点</div>
                  <div class="font-medium text-red-600">
                    {{ getFlowChangeJump() }}
                  </div>
                </div>
              </div>
              <div v-if="getLastQueryTime()" class="text-center text-xs text-gray-500 mt-2">
              上次统计时间：  {{getLastQueryTime()}}
              
              </div>
            </div>

            <!-- 流量使用分析 -->
            <div class="mt-3 pt-3 border-t border-gray-200">
              <div class="grid grid-cols-2 gap-3 text-xs">
                <div class="bg-blue-50 p-2 rounded">
                  <div class="font-medium text-blue-800">通用流量</div>
                  <div class="text-blue-600 font-bold">
                    已用：{{ formatMB(getGeneralFlowUsed()) }}
                  </div>
                  <div class="text-gray-600">
                    剩余：{{ formatMB(getGeneralFlowRemain()) }}
                  </div>
                </div>
                <div class="bg-green-50 p-2 rounded">
                  <div class="font-medium text-green-800">专属流量</div>
                  <div class="text-green-600 font-bold">
                    已用：{{ formatMB(getFreeFlowUsed()) }}
                  </div>
                  <div class="text-gray-600">
                    剩余：{{ formatMB(getFreeFlowRemain()) }}
                  </div>
                </div>
              </div>
              <div class="mt-2 text-xs text-gray-500 text-center">
                通用流量主要用于日常上网，专属流量主要用于指定应用
              </div>
            </div>

            <!-- 缓存状态 -->
            <div class="mt-3 pt-2 border-t border-gray-100">
              <div class="flex items-center justify-between text-xs">
                <div class="flex items-center space-x-2">
                  <el-tag
                    :type="selectedFlowData?.is_cached ? 'warning' : 'success'"
                    size="small"
                  >
                    {{ selectedFlowData?.is_cached ? "缓存数据" : "实时数据" }}
                  </el-tag>
                </div>
                <div class="text-gray-500">
                  {{ selectedFlowData?.is_cached ?
                    `此数据为${getLastRealtimeQueryTime()}的缓存数据` :
                    `此数据为${getCurrentQueryTime()}的实时数据`
                  }}
                </div>
              </div>
            </div>
          </div>

          <!-- 流量包详情（包含套外流量包） -->
          <div
            v-if="getAllFlowPackages().length > 0"
            class="glass-card p-3"
          >
            <div class="flex items-center justify-between mb-3">
              <h4 class="text-sm font-semibold text-gray-800">流量包详情</h4>
              <span class="text-xs text-gray-600"
                >共 {{ getAllFlowPackages().length }} 个流量包</span
              >
            </div>

            <div class="space-y-2">
              <div
                v-for="(pkg, index) in getAllFlowPackages()"
                :key="index"
                class="border border-gray-200 rounded p-2"
                :class="{ 'border-orange-300 bg-orange-50': pkg.isExtra }"
              >
                <div class="flex justify-between items-center mb-1">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-medium text-gray-700">{{
                      pkg.name
                    }}</span>
                    <el-tag
                      v-if="pkg.isExtra"
                      type="warning"
                      size="small"
                      class="text-xs"
                    >
                      套外
                    </el-tag>
                  </div>
                  <el-tag
                    :type="getPackageStatusType(pkg)"
                    size="small"
                    class="text-xs"
                  >
                    {{ getPackageStatusText(pkg) }}
                  </el-tag>
                </div>
                <div class="flex justify-between text-xs mb-1">
                  <span>已用: {{ formatMB(pkg.used) }}</span>
                  <span v-if="pkg.is_unlimited || pkg.total === 'unlimited'">
                    无限量流量包
                  </span>
                  <span v-else-if="parseFloat(pkg.remaining || 0) <= 0">
                    总量: {{ formatMB(pkg.total) }}
                  </span>
                  <span v-else>
                    剩余: {{ formatMB(pkg.remaining) }} / 总量:
                    {{ formatMB(pkg.total) }}
                  </span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    class="h-1.5 rounded-full"
                    :class="pkg.type === '2' ? 'bg-green-500' : 'bg-blue-500'"
                    :style="{ width: getPackageUsagePercent(pkg) + '%' }"
                  ></div>
                </div>
                <div class="text-xs text-gray-500 mt-1">
                  {{ pkg.type === "2" ? "专属流量" : "通用流量" }}
                </div>
              </div>
            </div>
          </div>

          <!-- 套外流量包 -->
          <div v-if="hasOutOfBundleFlow()" class="glass-card p-3">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-sm font-semibold text-gray-800">套外流量包</h4>
              <span class="text-xs text-gray-500">
                已使用{{ getHistoryOutOfBundleFlow().length }}个，{{
                  getOutOfBundleFlow().length > 0
                    ? "剩余" + getOutOfBundleFlow().length + "个正在使用中"
                    : "无剩余"
                }}
              </span>
            </div>

            <!-- 套外流量包总体统计 -->
            <div class="bg-orange-50 border border-orange-200 rounded p-2 mb-3">
              <div class="flex justify-between items-center text-xs">
                <span class="font-medium text-orange-800">套外流量总计</span>
                <span class="text-orange-600">{{
                  getTotalOutOfBundleUsage()
                }}</span>
              </div>
              <div class="text-xs text-orange-600 mt-1">
                历史已用：{{ formatMB(getHistoryOutOfBundleUsage()) }} +
                当前已用：{{ formatMB(getCurrentOutOfBundleUsage()) }}
              </div>
            </div>

            <!-- 当前使用中的套外流量包 -->
            <div v-if="getOutOfBundleFlow().length > 0" class="space-y-2 mb-3">
              <div
                v-for="(bundle, index) in getOutOfBundleFlow()"
                :key="'current-' + index"
                class="border border-blue-200 bg-blue-50 rounded p-2"
              >
                <div class="flex justify-between items-center mb-1">
                  <span class="text-xs font-medium text-blue-800">{{
                    bundle.name
                  }}</span>
                  <span class="text-xs text-blue-600"
                    >{{ bundle.usedPercent }}%</span
                  >
                </div>
                <div class="w-full bg-blue-200 rounded-full h-1.5 mb-1">
                  <div
                    class="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                    :style="{ width: bundle.usedPercent + '%' }"
                  ></div>
                </div>
                <div class="flex justify-between text-xs text-blue-600">
                  <span>已用：{{ formatMB(bundle.used) }}</span>
                  <span>剩余：{{ formatMB(bundle.remaining) }}</span>
                </div>
                <div class="text-xs text-blue-500 mt-1">
                  总量：{{ formatMB(bundle.total) }} • 使用中
                </div>
              </div>
            </div>

            <!-- 历史套外流量包（可展开） -->
            <div
              v-if="getHistoryOutOfBundleFlow().length > 0"
              class="border-t border-gray-200 pt-2"
            >
              <div
                class="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-2 rounded"
                @click="showHistoryPackages = !showHistoryPackages"
              >
                <div class="flex items-center space-x-2">
                  <span class="text-xs font-medium text-gray-600"
                    >过往使用记录</span
                  >
                  <span class="text-xs text-gray-500"
                    >({{ getHistoryOutOfBundleFlow().length }}个已用完)</span
                  >
                </div>
                <el-icon
                  class="text-gray-400 transition-transform duration-200"
                  :class="{ 'rotate-180': showHistoryPackages }"
                >
                  <ArrowDown />
                </el-icon>
              </div>

              <!-- 展开的历史记录 -->
              <div v-show="showHistoryPackages" class="space-y-2 mt-2">
                <div
                  v-for="(bundle, index) in getHistoryOutOfBundleFlow()"
                  :key="'history-' + index"
                  class="border border-gray-200 bg-gray-50 rounded p-2"
                >
                  <div class="flex justify-between items-center mb-1">
                    <span class="text-xs font-medium text-gray-700">{{
                      bundle.name
                    }}</span>
                    <span class="text-xs text-gray-500">已用完</span>
                  </div>
                  <div class="w-full bg-gray-300 rounded-full h-1.5 mb-1">
                    <div class="bg-gray-500 h-1.5 rounded-full w-full"></div>
                  </div>
                  <div class="flex justify-between text-xs text-gray-600">
                    <span>已用：{{ formatMB(bundle.used) }}</span>
                    <span>总量：{{ formatMB(bundle.total) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div
          v-else-if="!singleQueryLoading && selectedAccount"
          class="glass-card p-8"
        >
          <div class="text-center">
            <el-icon :size="48" class="text-gray-300">
              <DataAnalysis />
            </el-icon>
            <h4 class="text-lg font-medium text-gray-900 mt-4">暂无流量数据</h4>
            <p class="text-gray-500 mt-2">点击"刷新"按钮查询最新流量信息</p>
            <el-button
              type="primary"
              @click="querySingleFlow(false)"
              class="mt-4"
              :loading="singleQueryLoading"
            >
              <el-icon class="mr-2"><Refresh /></el-icon>
              查询流量
            </el-button>
          </div>
        </div>
      </div>
    </main>

    <!-- 缓存配置对话框 -->
    <el-dialog v-model="showCacheConfig" title="缓存设置" width="400px">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >查询间隔时间</label
          >
          <el-input-number
            v-model="cacheDurationMinutes"
            :min="1"
            :max="120"
            :step="1"
            controls-position="right"
            class="w-full"
          />
          <p class="text-xs text-gray-500 mt-1">
            设置查询间隔时间（分钟），避免频繁查询
          </p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >当前状态</label
          >
          <div class="flex items-center space-x-2">
            <el-tag :type="cacheStatus === 'cache' ? 'warning' : 'success'">
              {{ getDataSource() }}
            </el-tag>
            <span class="text-xs text-gray-500">
              {{ getCacheTimeRemaining() }}
            </span>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCacheConfig = false">取消</el-button>
          <el-button type="primary" @click="saveCacheConfig">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { useUserStore } from "@/stores/user";
import { accountAPI } from "@/api/account";
import { flowAPI } from "@/api/flow";
import { settingsAPI } from '@/utils/api'

import { storage } from '@/utils/storage'

import {
  Refresh,
  RefreshLeft,
  Plus,
  Monitor,
  User,
  Phone,
  Check,
  View,
  Loading,
  Document,
  Warning,
  ClockIcon,
  Setting,
  ArrowDown,
  SwitchButton,
  DataAnalysis,
} from "@/utils/icons";

// 路由和状态
const router = useRouter();
const userStore = useUserStore();

// 状态
const loading = ref(false);
const accounts = ref([]);
const selectedAccountId = ref("");
const singleQueryLoading = ref(false);
const lastQueryTime = ref(null);
const nextRefreshTime = ref(0);
const refreshCountdown = ref(0);
const selectedFlowData = ref(null);
const currentRecord = ref(null);
const showCacheConfig = ref(false);
const cacheDurationMinutes = ref(1); // 默认1分钟
const cacheStatus = ref("real");
const showHistoryPackages = ref(false);
const isResettingBaseline = ref(false); // 统计重置状态

// 缓存计算结果，避免重复计算
const flowChangeCache = ref({
  generalFlowChange: null,
  freeFlowChange: null,
  totalFlowChange: null,
  lastQueryTime: null,
  baselineTime: null
});

// 计算属性
const authenticatedAccounts = computed(() => {
  return accounts.value.filter((account) => account.auth_status === 1);
});

const selectedAccount = computed(() => {
  return accounts.value.find(
    (account) => account.id === selectedAccountId.value
  );
});

const canRefresh = computed(() => {
  return Date.now() >= nextRefreshTime.value;
});

// 更新倒计时
const updateCountdown = () => {
  const remaining = Math.ceil((nextRefreshTime.value - Date.now()) / 1000);
  refreshCountdown.value = Math.max(0, remaining);
};

// 定时器
let countdownTimer = null;

// 启动倒计时定时器
const startCountdownTimer = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }

  countdownTimer = setInterval(() => {
    updateCountdown();
    if (refreshCountdown.value <= 0) {
      clearInterval(countdownTimer);
      countdownTimer = null;
      // 倒计时结束时，重置nextRefreshTime，允许刷新
      nextRefreshTime.value = 0;
    }
  }, 1000);
};

// 手机号选择变化
const onAccountChange = () => {
  lastQueryTime.value = null;
  nextRefreshTime.value = 0;
  refreshCountdown.value = 0;
  selectedFlowData.value = null;
  currentRecord.value = null;

  // 清理流量变化缓存
  flowChangeCache.value = {
    generalFlowChange: null,
    freeFlowChange: null,
    lastQueryTime: null
  };

  // 清理定时器
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }

  // 自动查询新选择的账号流量（使用缓存）
  if (selectedAccountId.value) {
    setTimeout(() => {
      querySingleFlow(false); // 使用缓存查询，避免频繁请求
    }, 100);
  }
};

// 重置流量统计基准
const resetFlowBaseline = async () => {
  if (!selectedAccountId.value) {
    ElMessage.warning('请先选择账号');
    return;
  }

  try {
    // 确认对话框
    await ElMessageBox.confirm(
      '重置后将清空当前的流量变化统计，以当前流量为新的基准点开始计算。确定要重置吗？',
      '确认重置统计基准',
      {
        confirmButtonText: '确定重置',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    isResettingBaseline.value = true;

    // 调用重置API
    const response = await flowAPI.resetBaseline(selectedAccountId.value, '手动重置统计基准');

    if (response.success) {
      ElMessage.success('统计基准重置成功');

      // 清空前端缓存
      flowChangeCache.value = {
        generalFlowChange: null,
        freeFlowChange: null,
        totalFlowChange: null,
        lastQueryTime: null,
        baselineTime: null,
        baselineTimeDisplay: null
      };

      // 重新查询流量数据
      await querySingleFlow(false);

      console.log('统计基准重置完成:', response.data);

      // 强制更新时间显示
      if (response.data?.baseline?.baseline_time) {
        const baselineTime = new Date(response.data.baseline.baseline_time);
        flowChangeCache.value.baselineTimeDisplay = '刚刚';
        console.log('重置后基准时间:', baselineTime.toString());
      }
    } else {
      ElMessage.error(`重置失败: ${response.message}`);
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重置统计基准失败:', error);
      ElMessage.error('重置失败，请稍后重试');
    }
  } finally {
    isResettingBaseline.value = false;
  }
};

// 查询单个账号流量
const querySingleFlow = async (forceRefresh = false) => {
  if (!selectedAccountId.value) return;

  // 检查选中的账号是否已认证
  const account = accounts.value.find(a => a.id === selectedAccountId.value);
  if (!account || account.auth_status !== 1) {
    console.warn('选中的账号未认证，跳过查询');
    return;
  }

  try {
    singleQueryLoading.value = true;
    // 根据参数决定是否使用缓存
    const params = forceRefresh
      ? { use_cache: "false", force_refresh: "true" }
      : { use_cache: "true" };
    const response = await flowAPI.queryFlow(selectedAccountId.value, params);

    if (response.success) {
      lastQueryTime.value = new Date();

      // 只有手动刷新时才设置冷却时间，自动查询不设置冷却
      if (forceRefresh) {
        // 获取最新的冷却时间配置，优先从服务器配置，然后从本地存储，最后使用默认值
        let cooldownSec = 60; // 默认值

        if (serverCacheSettings.value?.refreshCooldownSeconds) {
          cooldownSec = serverCacheSettings.value.refreshCooldownSeconds;
        } else {
          // 如果服务器配置还没加载，尝试从本地存储获取
          try {
            const localSettings = JSON.parse(localStorage.getItem('user_settings') || '{}');
            if (localSettings.cache?.refreshCooldownSeconds) {
              cooldownSec = localSettings.cache.refreshCooldownSeconds;
            }
          } catch (e) {
            console.warn('获取本地缓存配置失败:', e);
          }
        }

        console.log('设置刷新冷却时间:', cooldownSec, '秒');
        nextRefreshTime.value = Date.now() + cooldownSec * 1000;
        // 启动倒计时定时器
        updateCountdown();
        startCountdownTimer();
      } else {
        // 自动查询不设置冷却时间，可以立即再次查询
        nextRefreshTime.value = 0;
        refreshCountdown.value = 0;
      }

      // 设置选中的流量数据 - 适配v3版本的数据结构
      selectedFlowData.value = {
        flow_info: response.data.flow_info,
        is_cached: response.data.is_cached,
        query_time: response.data.query_time,
        cached_at: response.data.cached_at,
        raw_data: response.data.raw_data, // 原始联通API数据
        comparison: response.data.comparison, // 对比数据
        baseline_changes: response.data.baseline_changes, // 基准变化数据
      };

      // 计算并缓存流量变化数据
      calculateFlowChanges();
      currentRecord.value = response.data.record;

      ElMessage.success("流量查询成功");
    } else {
      // 对于频率限制，显示后端返回的友好消息
      if (response.code === 'RATE_LIMITED') {
        ElMessage.warning(response.message || "手动刷新限制：请等待冷却时间");
      } else if (response.code === 'ECS000047') {
        // 非联通用户错误
        ElMessage.error(response.message || "此功能只针对联通号码开放，请确认您使用的是联通手机号码");
      } else {
        ElMessage.error(response.message || "流量查询失败，请重试");
      }
    }
  } catch (error) {
    console.error("查询流量失败:", error);
    // 检查是否有后端返回的错误信息
    if (error.response && error.response.data) {
      const errorData = error.response.data;
      if (errorData.code === 'ECS000047') {
        // 非联通用户错误
        ElMessage.error(errorData.message || "此功能只针对联通号码开放，请确认您使用的是联通手机号码");
      } else if (error.response.status === 429) {
        // 频率限制
        ElMessage.warning(errorData.message || "手动刷新限制：请等待冷却时间");
      } else {
        // 其他错误，优先显示后端返回的错误信息
        ElMessage.error(errorData.message || "流量查询失败，请重试");
      }
    } else {
      ElMessage.error("网络请求失败，请重试");
    }
  } finally {
    singleQueryLoading.value = false;
  }
};

// 加载账号列表
const loadAccounts = async () => {
  try {
    loading.value = true;
    const response = await accountAPI.getAccounts();
    if (response.success) {
      accounts.value = response.data;
      // 如果有账号，优先选择“展示与偏好”里设置的默认账号，否则选择第一个已认证账号
      if (accounts.value.length > 0) {
        const s = storage.getSettings ? storage.getSettings() : {};
        const preferId = s?.display?.defaultAccountId;

        let targetAccount = null;

        // 优先使用配置的默认账号（如果已认证）
        if (preferId) {
          targetAccount = accounts.value.find(a => a.id === preferId && a.auth_status === 1);
        }

        // 如果配置的默认账号不存在或未认证，选择第一个已认证账号
        if (!targetAccount) {
          targetAccount = accounts.value.find(a => a.auth_status === 1);
        }

        if (targetAccount) {
          selectedAccountId.value = targetAccount.id;
          // 延迟一下再查询，确保UI更新完成
          setTimeout(() => {
            querySingleFlow(false); // 使用缓存查询
          }, 100);
        } else {
          // 没有已认证的账号，清空选择
          selectedAccountId.value = "";
        }
      }
    }
  } catch (error) {
    console.error("加载账号失败:", error);
    ElMessage.error("加载账号失败");
  } finally {
    loading.value = false;
  }
};

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    await userStore.logout();
    router.push("/login");
    ElMessage.success("已退出登录");
  } catch (error) {
    // 用户取消
  }
};

// 格式化流量 - 完全复刻旧版本
const formatMB = (mb) => {
  if (!mb || mb === "--") return "--";
  const num = parseFloat(mb);
  if (num >= 1024) {
    return (num / 1024).toFixed(2) + "GB";
  }
  return num.toFixed(2) + "MB";
};

// 导入时区工具
import { formatQueryTime as formatQueryTimeUtil, formatTime as formatTimeUtil, formatRelativeTime, parseTime, isToday, now as timeNow } from '@/utils/timezone'

// 格式化查询时间
const formatQueryTime = (time) => {
  return formatQueryTimeUtil(time);
};

// 格式化时间
const formatTime = (time) => {
  return formatTimeUtil(time, 'datetime');
};

// 获取查询时间
const getQueryTime = () => {
  if (!selectedFlowData.value?.raw_data?.time) return "未知";
  return selectedFlowData.value.raw_data.time;
};

// 获取套餐名称（优先后端规范字段，其次原始数据）
const getPackageName = () => (
  selectedFlowData.value?.raw_data?.packageName ||
  selectedFlowData.value?.flow_info?.package_name ||
  ''
)

// 获取套餐ID（兼容不同字段命名）
const getPackageId = () => (
  selectedFlowData.value?.raw_data?.packageId ||
  selectedFlowData.value?.raw_data?.packageID ||
  selectedFlowData.value?.flow_info?.package_id ||
  ''
)


// 规范化展示用套餐名称：去掉价格等尾缀，如“8元”
const getPackageDisplayName = () => {
  const raw = getPackageName()
  if (!raw) return ''
  // 去掉“数字+元”样式（可能带空格）
  let name = raw.replace(/\d+\s*元/g, '').trim()
  // 去掉可能的连字符后说明，如 “- 首月全量全价”
  name = name.replace(/-.*$/, '').trim()
  return name
}

// 计算专属流量（免流）- 优先使用后端解析的分类数据
const getFreeFlowUsed = () => {
  // 优先使用后端解析的分类数据
  if (selectedFlowData.value?.flow_summary?.used_special) {
    return parseFloat(selectedFlowData.value.flow_summary.used_special || 0);
  }

  // 备选：使用flowSumList中的汇总数据
  if (selectedFlowData.value?.raw_data?.flowSumList) {
    let used = 0;
    selectedFlowData.value.raw_data.flowSumList.forEach((item) => {
      if (item.flowtype === "2") {
        // 专属流量
        used += parseFloat(item.xusedvalue || 0);
      }
    });
    return used;
  }

  // 降级方案：使用flow_packages计算
  if (!selectedFlowData.value?.flow_info?.flow_packages) return 0;
  let used = 0;
  selectedFlowData.value.flow_info.flow_packages.forEach((pkg) => {
    if (pkg.type === "2") {
      // 专属流量
      used += parseFloat(pkg.used || 0);
    }
  });
  return used;
};

const getFreeFlowRemain = () => {
  // 优先使用后端解析的分类数据
  if (selectedFlowData.value?.flow_summary?.remain_special) {
    return parseFloat(selectedFlowData.value.flow_summary.remain_special || 0);
  }

  // 备选：使用flowSumList中的汇总数据
  if (selectedFlowData.value?.raw_data?.flowSumList) {
    let remain = 0;
    selectedFlowData.value.raw_data.flowSumList.forEach((item) => {
      if (item.flowtype === "2") {
        // 专属流量
        remain += parseFloat(item.xcanusevalue || 0);
      }
    });
    return remain;
  }

  // 降级方案：使用flow_packages计算
  if (!selectedFlowData.value?.flow_info?.flow_packages) return 0;
  let remain = 0;
  selectedFlowData.value.flow_info.flow_packages.forEach((pkg) => {
    if (pkg.type === "2") {
      // 专属流量
      remain += parseFloat(pkg.remaining || 0);
    }
  });
  return remain;
};

// 计算通用流量 - 优先使用后端解析的分类数据
const getGeneralFlowUsed = () => {
  // 优先使用后端解析的分类数据
  if (selectedFlowData.value?.flow_summary?.used_general) {
    return parseFloat(selectedFlowData.value.flow_summary.used_general || 0);
  }

  // 备选：使用flowSumList中的汇总数据，这包含了历史套外流量包
  if (selectedFlowData.value?.raw_data?.flowSumList) {
    let used = 0;
    selectedFlowData.value.raw_data.flowSumList.forEach((item) => {
      if (item.flowtype === "1") {
        // 通用流量
        used += parseFloat(item.xusedvalue || 0);
      }
    });
    return used;
  }

  // 降级方案：使用flow_packages计算
  if (!selectedFlowData.value?.flow_info?.flow_packages) return 0;
  let used = 0;
  selectedFlowData.value.flow_info.flow_packages.forEach((pkg) => {
    if (pkg.type === "1") {
      // 通用流量
      used += parseFloat(pkg.used || 0);
    }
  });
  return used;
};

const getGeneralFlowRemain = () => {
  // 优先使用flowSumList中的汇总数据
  if (selectedFlowData.value?.raw_data?.flowSumList) {
    let remain = 0;
    selectedFlowData.value.raw_data.flowSumList.forEach((item) => {
      if (item.flowtype === "1") {
        // 通用流量
        remain += parseFloat(item.xcanusevalue || 0);
      }
    });
    return remain;
  }

  // 降级方案：使用flow_packages计算
  if (!selectedFlowData.value?.flow_info?.flow_packages) return 0;
  let remain = 0;
  selectedFlowData.value.flow_info.flow_packages.forEach((pkg) => {
    if (pkg.type === "1") {
      // 通用流量
      remain += parseFloat(pkg.remaining || 0);
    }
  });
  return remain;
};

// 计算流量变化
const getFlowChangeUsed = () => {
  // 已用 = 通用流量变化 + 专属流量变化（总量变化）
  const generalChange = getGeneralFlowChange();
  const freeChange = getFreeFlowChange();

  if (generalChange === null || freeChange === null) return "--";

  const totalChange = generalChange + freeChange;
  // 流量使用量不应该减少，如果是负数可能是数据问题，显示为0
  if (totalChange > 0) {
    return `+${formatMB(totalChange)}`;
  } else if (totalChange < 0) {
    console.warn('流量变化为负数，可能是数据异常:', { generalChange, freeChange, totalChange });
    return "0MB"; // 异常情况显示0而不是负数
  } else {
    return "0MB";
  }
};

const getFlowChangeFree = () => {
  // 已免 = 专属流量变化
  const change = getFreeFlowChange();
  if (change === null) return "--";
  if (change > 0) {
    return `+${formatMB(change)}`;
  } else if (change < 0) {
    console.warn('专属流量变化为负数，可能是数据异常:', change);
    return "0MB"; // 异常情况显示0而不是负数
  } else {
    return "0MB";
  }
};

const getFlowChangeJump = () => {
  // 跳点 = 通用流量变化
  const change = getGeneralFlowChange();
  if (change === null) return "--";
  if (change > 0) {
    return `+${formatMB(change)}`;
  } else if (change < 0) {
    console.warn('通用流量变化为负数，可能是数据异常:', change);
    return "0MB"; // 异常情况显示0而不是负数
  } else {
    return "0MB";
  }
};

// 计算流量包使用百分比
const getPackageUsagePercent = (pkg) => {
  if (!pkg) return 0;

  // 处理无限量流量包
  if (pkg.is_unlimited || pkg.total === 'unlimited') {
    // 无限量流量包显示为满进度条，表示有使用量
    return pkg.used && parseFloat(pkg.used) > 0 ? 100 : 0;
  }

  if (!pkg.total || pkg.total === 0) return 0;
  const used = parseFloat(pkg.used || 0);
  const total = parseFloat(pkg.total || 0);
  if (total === 0) return 0;
  return Math.min(Math.round((used / total) * 100), 100);
};

// 获取流量包状态类型
const getPackageStatusType = (pkg) => {
  if (!pkg) return 'info';

  // 无限量流量包
  if (pkg.is_unlimited || pkg.total === 'unlimited') {
    return pkg.used && parseFloat(pkg.used) > 0 ? 'success' : 'info';
  }

  // 有限量流量包
  return parseFloat(pkg.remaining || 0) > 0 ? 'success' : 'danger';
};

// 获取流量包状态文本
const getPackageStatusText = (pkg) => {
  if (!pkg) return '未知';

  // 无限量流量包
  if (pkg.is_unlimited || pkg.total === 'unlimited') {
    return pkg.used && parseFloat(pkg.used) > 0 ? '无限量' : '未使用';
  }

  // 有限量流量包
  return parseFloat(pkg.remaining || 0) > 0 ? '有余量' : '已用完';
};

// 缓存相关
const getDataSource = () => {
  return cacheStatus.value === "cache" ? "缓存数据" : "实时查询";
};

const getCacheTimeRemaining = () => {
  if (!selectedAccountId.value) return "";
  if (!lastQueryTime.value) return "无缓存数据";

  const remaining =
    cacheDurationMinutes.value * 60 * 1000 -
    (Date.now() - lastQueryTime.value.getTime());
  if (remaining <= 0) return "可立即查询";

  const minutes = Math.floor(remaining / 60000);
  const seconds = Math.floor((remaining % 60000) / 1000);
  return `剩余 ${minutes}分${seconds}秒`;
};

// 保存缓存配置
const saveCacheConfig = async () => {
  const minutes = Number(cacheDurationMinutes.value) || 10;
  try {
    // 优先保存到后端
    const res = await settingsAPI.saveCache({ cacheTtlMinutes: minutes })
    if (!res?.success) throw new Error(res?.message || '保存失败')
  } catch (e) {
    // 后端失败则回落到本地（开发期容错）
    localStorage.setItem("cache_duration_minutes", String(minutes));
  }
  showCacheConfig.value = false;
  ElMessage.success("缓存设置已保存");
};

// 初始化缓存配置
const serverCacheSettings = ref(null)
const initCacheConfig = async () => {
  try {
    const res = await settingsAPI.getCache()
    if (res?.success && res.data) {
      serverCacheSettings.value = res.data
      if (res.data.cacheTtlMinutes) {
        cacheDurationMinutes.value = parseInt(res.data.cacheTtlMinutes)
      }

      // 同步到本地存储，便于离线使用
      try {
        const localSettings = JSON.parse(localStorage.getItem('user_settings') || '{}');
        localSettings.cache = { ...localSettings.cache, ...res.data };
        localStorage.setItem('user_settings', JSON.stringify(localSettings));
      } catch (e) {
        console.warn('保存本地缓存配置失败:', e);
      }

      console.log('缓存配置加载成功:', res.data);
      return
    }
  } catch (e) {
    console.warn('获取服务器缓存配置失败:', e);
  }
  // 回落：本地
  const minutes = Number(localStorage.getItem("cache_duration_minutes") || 0)
  if (minutes) cacheDurationMinutes.value = parseInt(minutes)
};

// 获取套外流量包
const getOutOfBundleFlow = () => {
  if (!selectedFlowData.value?.raw_data?.TwResources) return [];
  const bundles = [];
  selectedFlowData.value.raw_data.TwResources.forEach((resource) => {
    if (resource.type === "flow" && resource.details) {
      resource.details.forEach((detail) => {
        bundles.push({
          name: detail.addUpItemName,
          total: parseFloat(detail.total || 0),
          used: parseFloat(detail.use || 0),
          remaining: parseFloat(detail.remain || 0),
          usedPercent: detail.usedPercent || "0",
        });
      });
    }
  });
  return bundles;
};

// 获取历史套外流量包（已用完的）
const getHistoryOutOfBundleFlow = () => {
  if (!selectedFlowData.value?.raw_data?.s1HistoryFlowDetails) return [];
  const bundles = [];
  selectedFlowData.value.raw_data.s1HistoryFlowDetails.forEach((detail) => {
    bundles.push({
      name: detail.addUpItemName,
      total: parseFloat(detail.total || 0),
      used: parseFloat(detail.use || 0),
      remaining: 0, // 历史套外流量包都是已用完的
      usedPercent: "100",
    });
  });
  return bundles;
};

// 计算历史套外流量包总使用量
const getHistoryOutOfBundleUsage = () => {
  let total = 0;
  getHistoryOutOfBundleFlow().forEach((bundle) => {
    total += bundle.used;
  });
  return total;
};

// 计算当前套外流量包已使用量
const getCurrentOutOfBundleUsage = () => {
  let total = 0;
  getOutOfBundleFlow().forEach((bundle) => {
    total += bundle.used;
  });
  return total;
};

// 获取套外流量包总体使用情况描述
const getTotalOutOfBundleUsage = () => {
  const historyUsed = getHistoryOutOfBundleUsage();
  const currentUsed = getCurrentOutOfBundleUsage();
  const totalUsed = historyUsed + currentUsed;
  const historyCount = getHistoryOutOfBundleFlow().length;
  const currentCount = getOutOfBundleFlow().length;

  return `共${formatMB(totalUsed)} (${historyCount + currentCount}个包)`;
};

// 检查是否有套外流量包（当前或历史）
const hasOutOfBundleFlow = () => {
  return (
    getOutOfBundleFlow().length > 0 || getHistoryOutOfBundleFlow().length > 0
  );
};

// 获取非套外流量包（从flow_packages中过滤掉套外流量包）
const getNonOutOfBundlePackages = () => {
  if (!selectedFlowData.value?.flow_info?.flow_packages) return [];

  // 过滤掉套外流量包，套外流量包的特征：
  // 1. 名称包含"套外流量"
  // 2. 或者来自TwResources的数据
  return selectedFlowData.value.flow_info.flow_packages.filter((pkg) => {
    // 如果包名包含"套外流量"，则排除
    if (pkg.name && pkg.name.includes("套外流量")) {
      return false;
    }

    // 检查是否在TwResources中存在相同的包
    const twResources = selectedFlowData.value?.raw_data?.TwResources || [];
    const isInTwResources = twResources.some((resource) => {
      if (resource.type === "flow" && resource.details) {
        return resource.details.some(
          (detail) =>
            detail.addUpItemName === pkg.name ||
            detail.feePolicyName === pkg.name
        );
      }
      return false;
    });

    // 如果在TwResources中找到，则排除
    return !isInTwResources;
  });
};

// 获取所有流量包详情（包含套外流量包）
const getAllFlowPackages = () => {
  const packages = [];

  // 添加常规流量包
  if (selectedFlowData.value?.flow_info?.flow_packages) {
    selectedFlowData.value.flow_info.flow_packages.forEach((pkg) => {
      packages.push({
        ...pkg,
        used: parseFloat(pkg.used || 0),
        remaining: parseFloat(pkg.remaining || 0),
        total: parseFloat(pkg.total || 0),
        isExtra: pkg.name && pkg.name.includes("套外流量")
      });
    });
  }

  // 添加套外流量包（从flow_summary中获取）
  if (selectedFlowData.value?.flow_summary?.extra_packages) {
    selectedFlowData.value.flow_summary.extra_packages.forEach((pkg) => {
      packages.push({
        ...pkg,
        used: parseFloat(pkg.used || 0),
        remaining: parseFloat(pkg.remaining || 0),
        total: parseFloat(pkg.total || 0),
        isExtra: true
      });
    });
  }

  return packages;
};

// 计算通用流量变化
const getGeneralFlowChange = () => {
  return flowChangeCache.value.generalFlowChange;
};

// 计算专属流量变化
const getFreeFlowChange = () => {
  return flowChangeCache.value.freeFlowChange;
};

// 获取统计重置时间
const getLastQueryTime = () => {
  return flowChangeCache.value.baselineTimeDisplay;
};

// 获取当前查询时间（实时查询时显示）
const getCurrentQueryTime = () => {
  return formatTime(new Date(), 'datetime-seconds');
};

// 获取缓存数据的相对时间（缓存数据时显示）
const getLastRealtimeQueryTime = () => {
  // 优先使用缓存时间，其次使用对比数据中的上次查询时间
  const cacheTime = selectedFlowData.value?.cached_at;
  if (cacheTime) {
    return formatRelativeTime(cacheTime);
  }

  // 如果没有缓存时间，使用对比数据中的上次查询时间
  const lastQueryTime = selectedFlowData.value?.comparison?.last_query_time;
  if (lastQueryTime) {
    return formatRelativeTime(lastQueryTime);
  }

  // 最后使用原始数据中的时间
  const rawTime = selectedFlowData.value?.raw_data?.time;
  if (rawTime) {
    return formatRelativeTime(rawTime);
  }

  return '未知';
};


// 从localStorage恢复流量变化缓存
const restoreFlowChangeCache = () => {
  const accountId = selectedAccountId.value;
  if (!accountId) return;

  const cacheKey = `flow_change_cache_${accountId}`;
  const savedCache = localStorage.getItem(cacheKey);

  if (savedCache) {
    try {
      const parsedCache = JSON.parse(savedCache);
      flowChangeCache.value = parsedCache;
      console.log('恢复流量变化缓存:', parsedCache);
    } catch (e) {
      console.warn('恢复缓存失败:', e);
    }
  }
};

// 保存流量变化缓存到localStorage
const saveFlowChangeCache = () => {
  const accountId = selectedAccountId.value;
  if (!accountId) return;

  const cacheKey = `flow_change_cache_${accountId}`;
  localStorage.setItem(cacheKey, JSON.stringify(flowChangeCache.value));
  console.log('保存流量变化缓存:', flowChangeCache.value);
};

// 计算并缓存流量变化数据（只在查询时调用一次）
const calculateFlowChanges = () => {
  // 检查是否有基准变化数据
  if (!selectedFlowData.value?.baseline_changes) {
    // 没有基准数据，清空缓存
    flowChangeCache.value = {
      generalFlowChange: null,
      freeFlowChange: null,
      totalFlowChange: null,
      lastQueryTime: null,
      baselineTime: null
    };
    return;
  }

  // 使用基准变化数据（而不是上次查询数据）
  const baselineChanges = selectedFlowData.value.baseline_changes;

  flowChangeCache.value.generalFlowChange = baselineChanges.general_change || 0;
  flowChangeCache.value.freeFlowChange = baselineChanges.free_change || 0;
  flowChangeCache.value.totalFlowChange = baselineChanges.total_change || 0;

  // 计算基准时间（统计重置时间）
  if (baselineChanges.baseline_time) {
    const lastTimeStr = baselineChanges.baseline_time;

    // 使用时区工具解析时间
    const lastTime = parseTime(lastTimeStr);
    if (!lastTime) {
      console.error('时间解析失败:', lastTimeStr);
      flowChangeCache.value.baselineTimeDisplay = null;
      flowChangeCache.value.baselineTime = null;
      return;
    }

    const now = timeNow();
    const diffMs = now - lastTime;
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMinutes / 60);

    console.log('基准时间计算调试:', {
      baselineTimeStr: lastTimeStr,
      parsedTime: lastTime.toString(),
      now: now.toString(),
      diffMs,
      diffMinutes,
      diffHours
    });

    // 设置基准重置时间显示
    let baselineTimeDisplay;

    if (isToday(lastTime)) {
      // 今天的话显示相对时间
      if (diffHours > 0) {
        baselineTimeDisplay = `${diffHours}小时前`;
      } else if (diffMinutes > 0) {
        baselineTimeDisplay = `${diffMinutes}分钟前`;
      } else {
        baselineTimeDisplay = '刚刚';
      }
    } else {
      // 不是今天的话显示具体日期时间
      baselineTimeDisplay = formatTimeUtil(lastTime, 'full');
    }

    // 存储基准时间信息
    flowChangeCache.value.baselineTimeDisplay = baselineTimeDisplay;
    flowChangeCache.value.baselineTime = baselineChanges.baseline_time;
  } else {
    flowChangeCache.value.baselineTimeDisplay = null;
    flowChangeCache.value.baselineTime = null;
  }

  // 保存缓存到localStorage
  saveFlowChangeCache();

  // 输出一次调试信息（仅在查询时）
  console.log('基准流量变化计算完成:', {
    hasBaselineData: !!selectedFlowData.value?.baseline_changes,
    generalChange: flowChangeCache.value.generalFlowChange,
    freeChange: flowChangeCache.value.freeFlowChange,
    totalChange: flowChangeCache.value.totalFlowChange,
    baselineTime: flowChangeCache.value.baselineTime,
    baselineTimeDisplay: flowChangeCache.value.baselineTimeDisplay,
    currentTime: new Date().toISOString(),
    baselineChanges: selectedFlowData.value?.baseline_changes
  });
};

// 生命周期
onMounted(() => {
  loadAccounts();
  initCacheConfig();
});

onUnmounted(() => {
  // 清理定时器
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
});
</script>

<style scoped>
/* 组件特定样式 */
</style>
