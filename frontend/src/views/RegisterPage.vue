<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
    <div class="max-w-md w-full">
      <div class="text-center mb-8">
        <div class="mx-auto h-16 w-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mb-4">
          <el-icon :size="32" class="text-white">
            <Monitor />
          </el-icon>
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">用户注册</h1>
        <p class="text-gray-600">创建您的联通流量监控账号</p>
      </div>

      <el-card class="shadow-xl border-0">
        <div class="text-center py-20">
          <el-icon :size="64" class="text-gray-400 mb-4"><UserFilled /></el-icon>
          <h3 class="text-xl font-medium text-gray-900 mb-2">注册页面开发中</h3>
          <p class="text-gray-600 mb-6">请使用登录页面的注册功能</p>
          <el-button type="primary" @click="$router.push('/login')">
            前往登录
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { Monitor, UserFilled } from '@/utils/icons'
</script>
