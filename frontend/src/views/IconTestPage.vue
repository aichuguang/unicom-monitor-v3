<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">🎨 图标测试页面</h1>
    
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      <div 
        v-for="(icon, name) in iconMap" 
        :key="name"
        class="flex flex-col items-center p-4 border rounded-lg hover:bg-gray-50"
      >
        <component :is="icon" class="w-8 h-8 mb-2 text-blue-600" />
        <span class="text-xs text-gray-600 text-center">{{ name }}</span>
      </div>
    </div>
    
    <div class="mt-8 p-4 bg-green-50 border border-green-200 rounded-lg">
      <h3 class="text-lg font-medium text-green-800 mb-2">✅ 图标库更新成功！</h3>
      <p class="text-green-700">
        现在使用 Heroicons 图标库，所有图标都应该正常显示。
      </p>
    </div>
  </div>
</template>

<script setup>
import { iconMap } from '@/utils/icons'
</script>
