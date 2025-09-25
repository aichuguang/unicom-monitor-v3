<template>
  <teleport to="body">
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <transition-group name="message" tag="div">
        <div
          v-for="message in appStore.messages"
          :key="message.id"
          class="bg-white rounded-lg shadow-lg border-l-4 p-4 max-w-sm"
          :class="getMessageClass(message.type)"
        >
          <div class="flex items-start">
            <el-icon :size="20" class="flex-shrink-0 mt-0.5 mr-3">
              <component :is="getMessageIcon(message.type)" />
            </el-icon>
            
            <div class="flex-1 min-w-0">
              <div v-if="message.title" class="font-medium text-gray-900 mb-1">
                {{ message.title }}
              </div>
              <div class="text-sm text-gray-600">
                {{ message.content }}
              </div>
            </div>
            
            <el-button
              v-if="message.showClose"
              type="text"
              size="small"
              @click="appStore.removeMessage(message.id)"
              class="ml-2 p-1"
            >
              <el-icon :size="14"><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup>
import {
  Close, SuccessFilled, WarningFilled,
  CircleCloseFilled, InfoFilled
} from '@/utils/icons'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

// 获取消息样式类
const getMessageClass = (type) => {
  const classes = {
    success: 'border-green-400',
    warning: 'border-yellow-400',
    error: 'border-red-400',
    info: 'border-blue-400'
  }
  return classes[type] || classes.info
}

// 获取消息图标
const getMessageIcon = (type) => {
  const icons = {
    success: SuccessFilled,
    warning: WarningFilled,
    error: CircleCloseFilled,
    info: InfoFilled
  }
  return icons[type] || icons.info
}
</script>

<style scoped>
.message-enter-active,
.message-leave-active {
  transition: all 0.3s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.message-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.message-move {
  transition: transform 0.3s ease;
}
</style>
