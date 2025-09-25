<template>
  <header class="bg-white shadow-sm border-b border-gray-200 h-16 flex items-center px-4 md:px-6">
    <div class="flex items-center justify-between w-full">
      <!-- 左侧：Logo和标题 -->
      <div class="flex items-center">
        <!-- 移动端菜单按钮 -->
        <el-button
          v-if="appStore.isMobile"
          type="text"
          @click="appStore.toggleSidebar"
          class="mr-3"
        >
          <el-icon :size="20"><Menu /></el-icon>
        </el-button>
        
        <!-- Logo -->
        <div class="flex items-center">
          <div class="h-8 w-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3">
            <el-icon :size="18" class="text-white"><Monitor /></el-icon>
          </div>
          <h1 class="text-xl font-bold text-gray-900 hidden md:block">
            联通流量监控
          </h1>
        </div>
      </div>

      <!-- 右侧：用户信息和操作 -->
      <div class="flex items-center space-x-4">
        <!-- 网络状态指示器 -->
        <div class="flex items-center">
          <span 
            class="status-dot"
            :class="appStore.isOnline ? 'success' : 'danger'"
          ></span>
          <span class="text-sm text-gray-600 hidden md:inline">
            {{ appStore.isOnline ? '在线' : '离线' }}
          </span>
        </div>

        <!-- 主题切换 -->
        <el-button
          type="text"
          @click="appStore.toggleTheme"
          class="hidden md:inline-flex"
        >
          <el-icon :size="18">
            <Sunny v-if="appStore.theme === 'light'" />
            <Moon v-else />
          </el-icon>
        </el-button>

        <!-- 用户菜单 -->
        <el-dropdown @command="handleUserCommand">
          <div class="flex items-center cursor-pointer hover:bg-gray-50 rounded-lg px-2 py-1">
            <el-avatar :size="32" class="mr-2">
              <el-icon><User /></el-icon>
            </el-avatar>
            <div class="hidden md:block">
              <div class="text-sm font-medium text-gray-900">
                {{ userStore.userInfo.nickname || userStore.userInfo.username }}
              </div>
              <div class="text-xs text-gray-500">
                {{ userStore.userInfo.email || '未设置邮箱' }}
              </div>
            </div>
            <el-icon class="ml-2 text-gray-400"><ArrowDown /></el-icon>
          </div>
          
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon class="mr-2"><User /></el-icon>
                个人中心
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon class="mr-2"><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  Menu, Monitor, User, ArrowDown, Setting, Tools,
  SwitchButton, Sunny, Moon
} from '@/utils/icons'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

// 处理用户菜单命令
const handleUserCommand = async (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '确认退出',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )

        await userStore.logout()
        appStore.showSuccess('已退出登录')
        router.push('/login')
      } catch (error) {
        // 用户取消
      }
      break
  }
}
</script>

<style scoped>
.el-dropdown {
  outline: none;
}
</style>
