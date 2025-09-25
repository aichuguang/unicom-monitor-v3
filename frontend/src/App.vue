<template>
  <div id="app" class="h-full">
    <!-- 登录页面 -->
    <div v-if="!userStore.isLoggedIn" class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <LoginPage />
    </div>
    
    <!-- 主应用界面 -->
    <div v-else class="h-full flex flex-col">
      <!-- 顶部导航栏 (仅桌面端显示) -->
      <AppHeader v-if="!isMobile" />

      <!-- 主内容区域 -->
      <div class="flex-1 flex overflow-hidden">
        <!-- 侧边栏 (桌面端) -->
        <AppSidebar v-if="!isMobile" />

        <!-- 主内容 -->
        <main class="flex-1 overflow-auto bg-gray-50" :class="{ 'pb-16': isMobile }">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </main>
      </div>

      <!-- 底部导航栏 (移动端) - 固定在底部 -->
      <AppBottomNav v-if="isMobile" class="fixed bottom-0 left-0 right-0 z-50" />
    </div>
    
    <!-- 全局加载遮罩 -->
    <div
      v-loading="appStore.globalLoading"
      :element-loading-text="appStore.loadingText"
      element-loading-background="rgba(0, 0, 0, 0.7)"
      class="fixed inset-0 z-50"
      v-if="appStore.globalLoading"
    ></div>
    
    <!-- 全局消息提示 -->
    <GlobalMessage />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

import LoginPage from '@/views/LoginPage.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppBottomNav from '@/components/layout/AppBottomNav.vue'
import GlobalMessage from '@/components/common/GlobalMessage.vue'

const userStore = useUserStore()
const appStore = useAppStore()

// 响应式断点检测
const isMobile = ref(window.innerWidth <= 768)

// 初始化应用
onMounted(async () => {
  // 初始化主题
  appStore.initTheme()

  // 检查本地存储的登录状态
  await userStore.checkLoginStatus()

  // 设置移动端状态
  appStore.setMobile(isMobile.value)

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)

  // 监听网络状态
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})

// 处理窗口大小变化
const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
  appStore.setMobile(isMobile.value)
}

// 处理网络状态变化
const handleOnline = () => {
  appStore.setOnline(true)
  ElMessage.success('网络连接已恢复')
}

const handleOffline = () => {
  appStore.setOnline(false)
  ElMessage.warning('网络连接已断开')
}
</script>

<style scoped>
/* 组件特定样式 */
</style>
