<template>
  <aside 
    class="bg-white shadow-sm border-r border-gray-200 transition-all duration-300"
    :class="{
      'w-64': !appStore.sidebarCollapsed,
      'w-16': appStore.sidebarCollapsed
    }"
  >
    <div class="h-full flex flex-col">
      <!-- 侧边栏头部 -->
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div v-if="!appStore.sidebarCollapsed" class="flex items-center">
            <div class="h-8 w-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3">
              <el-icon :size="18" class="text-white"><Monitor /></el-icon>
            </div>
            <span class="text-lg font-semibold text-gray-900">流量监控</span>
          </div>
          
          <el-button
            type="text"
            @click="appStore.toggleSidebar"
            class="p-1"
          >
            <el-icon :size="16">
              <Fold v-if="!appStore.sidebarCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
        </div>
      </div>

      <!-- 导航菜单 -->
      <nav class="flex-1 p-4">
        <ul class="space-y-2">
          <li v-for="route in menuRoutes" :key="route.name">
            <router-link
              :to="route.path"
              class="flex items-center px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
              :class="{
                'bg-blue-50 text-blue-600 border-r-2 border-blue-600': $route.name === route.name
              }"
            >
              <el-icon :size="20" class="flex-shrink-0">
                <component :is="route.meta.icon" />
              </el-icon>
              
              <span 
                v-if="!appStore.sidebarCollapsed"
                class="ml-3 font-medium"
              >
                {{ route.meta.title }}
              </span>
            </router-link>
          </li>
        </ul>
      </nav>

      <!-- 侧边栏底部 -->
      <div class="p-4 border-t border-gray-200">
        <div class="flex items-center">
          <el-avatar :size="32">
            <el-icon><User /></el-icon>
          </el-avatar>
          
          <div v-if="!appStore.sidebarCollapsed" class="ml-3 flex-1">
            <div class="text-sm font-medium text-gray-900 truncate">
              {{ userStore.userInfo.nickname || userStore.userInfo.username }}
            </div>
            <div class="text-xs text-gray-500 truncate">
              {{ userStore.userInfo.email || '未设置邮箱' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import {
  Monitor, Fold, Expand, User, House,
  Setting, View
} from '@/utils/icons'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { menuRoutes } from '@/router'

const userStore = useUserStore()
const appStore = useAppStore()
</script>

<style scoped>
.router-link-active {
  @apply bg-blue-50 text-blue-600;
}
</style>
