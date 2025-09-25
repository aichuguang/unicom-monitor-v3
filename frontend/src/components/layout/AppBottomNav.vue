<template>
  <nav class="bg-white border-t border-gray-200 px-4 py-2 shadow-lg">
    <div class="flex justify-around">
      <router-link
        v-for="route in mobileRoutes"
        :key="route.name"
        :to="route.path"
        class="flex flex-col items-center py-2 px-3 rounded-lg transition-colors"
        :class="{
          'text-blue-600': $route.name === route.name,
          'text-gray-600': $route.name !== route.name
        }"
      >
        <el-icon :size="20" class="mb-1">
          <component :is="route.meta.icon" />
        </el-icon>
        <span class="text-xs font-medium">
          {{ route.meta.title }}
        </span>
      </router-link>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { menuRoutes } from '@/router'

// 移动端显示的路由
const mobileRoutes = computed(() => 
  menuRoutes.filter(route => !route.meta?.hideInMobile)
)
</script>

<style scoped>
.router-link-active {
  @apply text-blue-600;
}
</style>
