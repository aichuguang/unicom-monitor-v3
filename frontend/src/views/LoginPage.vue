<template>
  <div class="min-h-screen flex items-start justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-4 overflow-y-auto">
    <div class="max-w-md w-full">
      <!-- Logo和标题 -->
      <div class="text-center mb-8">
        <div class="mx-auto h-16 w-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mb-4">
          <el-icon :size="32" class="text-white">
            <Monitor />
          </el-icon>
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">联通流量监控</h1>
        <p class="text-gray-600">v3.0 智能防风控 · 实时监控</p>
      </div>

      <!-- 登录表单 -->
      <el-card class="shadow-xl border-0">
        <template #header>
          <div class="text-center">
            <h2 class="text-xl font-semibold text-gray-800">
              {{ isLogin ? '用户登录' : '用户注册' }}
            </h2>
          </div>
        </template>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
        >
          <!-- 用户名 -->
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              clearable
            />
          </el-form-item>

          <!-- 邮箱 (仅注册时显示) -->
          <el-form-item v-if="!isLogin" label="邮箱" prop="email">
            <el-input
              v-model="form.email"
              placeholder="请输入邮箱地址"
              :prefix-icon="Message"
              clearable
            />
          </el-form-item>

          <!-- 昵称 (仅注册时显示) -->
          <el-form-item v-if="!isLogin" label="昵称" prop="nickname">
            <el-input
              v-model="form.nickname"
              placeholder="请输入昵称"
              :prefix-icon="Avatar"
              clearable
            />
          </el-form-item>

          <!-- 密码 -->
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>

          <!-- 确认密码 (仅注册时显示) -->
          <el-form-item v-if="!isLogin" label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>

          <!-- 记住我 (仅登录时显示) -->
          <el-form-item v-if="isLogin">
            <el-checkbox v-model="form.remember">记住我</el-checkbox>
          </el-form-item>

          <!-- 提交按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="handleSubmit"
              class="w-full"
            >
              {{ isLogin ? '登录' : '注册' }}
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 切换登录/注册 -->
        <div class="text-center mt-4">
          <el-button type="text" @click="toggleMode">
            {{ isLogin ? '没有账号？立即注册' : '已有账号？立即登录' }}
          </el-button>
        </div>
      </el-card>

      <!-- 功能特色 -->
      <div class="mt-8 text-center">
        <div class="grid grid-cols-2 gap-4 text-sm text-gray-600">
          <div class="flex items-center justify-center">
            <el-icon class="mr-1 text-green-500"><Check /></el-icon>
            智能防风控
          </div>
          <div class="flex items-center justify-center">
            <el-icon class="mr-1 text-blue-500"><Monitor /></el-icon>
            实时监控
          </div>
          <div class="flex items-center justify-center">
            <el-icon class="mr-1 text-purple-500"><User /></el-icon>
            多用户支持
          </div>
          <div class="flex items-center justify-center">
            <el-icon class="mr-1 text-orange-500"><Iphone /></el-icon>
            H5响应式
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Avatar, Monitor, Check, Iphone } from '@/utils/icons'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 状态
const isLogin = ref(true)
const loading = ref(false)
const formRef = ref()

// 表单数据
const form = reactive({
  username: '',
  email: '',
  nickname: '',
  password: '',
  confirmPassword: '',
  remember: false
})

// 表单验证规则
const rules = computed(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: isLogin.value ? [] : [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  nickname: isLogin.value ? [] : [
    { max: 50, message: '昵称长度不能超过 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: isLogin.value ? [] : [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}))

// 切换登录/注册模式
const toggleMode = () => {
  isLogin.value = !isLogin.value
  // 清空表单
  Object.keys(form).forEach(key => {
    if (key !== 'remember') {
      form[key] = ''
    }
  })
  // 清除验证
  formRef.value?.clearValidate()
}

// 处理表单提交
const handleSubmit = async () => {
  try {
    // 表单验证
    await formRef.value.validate()
    
    loading.value = true
    
    if (isLogin.value) {
      // 登录
      const result = await userStore.login({
        username: form.username,
        password: form.password
      })
      
      if (result.success) {
        ElMessage.success('登录成功')
        
        // 跳转到目标页面
        const redirect = route.query.redirect || '/'
        router.push(redirect)
      } else {
        ElMessage.error(result.message || '登录失败')
      }
    } else {
      // 注册
      const result = await userStore.register({
        username: form.username,
        email: form.email || undefined,
        nickname: form.nickname || undefined,
        password: form.password
      })
      
      if (result.success) {
        ElMessage.success('注册成功，请登录')
        isLogin.value = true
        // 保留用户名
        const username = form.username
        Object.keys(form).forEach(key => {
          if (key !== 'remember') {
            form[key] = ''
          }
        })
        form.username = username
      } else {
        ElMessage.error(result.message || '注册失败')
      }
    }
  } catch (error) {
    console.error('表单提交失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 确保页面可以正常滚动 */
.min-h-screen {
  min-height: 100vh;
  min-height: 100dvh; /* 动态视口高度 */
}

.el-card {
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.9);
}

.el-form-item {
  margin-bottom: 20px;
}

.el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.el-button--primary:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
}

/* 移动端优化 */
@media (max-width: 640px) {
  .max-w-md {
    max-width: 100%;
    width: 100%;
  }

  .el-form-item {
    margin-bottom: 16px;
  }

  .el-card {
    margin: 0 0 3rem 0;
    border-radius: 12px;
  }

  /* 确保按钮可见 */
  .el-button {
    min-height: 44px; /* 移动端最小触摸目标 */
  }

  /* 功能特色区域也需要底部边距 */
  .mt-8 {
    margin-top: 2rem;
    margin-bottom: 3rem;
  }

  /* 确保页面底部按钮不被遮挡，留适度空白 */
  .min-h-screen {
    padding-bottom: max(72px, env(safe-area-inset-bottom, 0px) + 24px) !important;
  }
}

/* 深色模式适配 */
html.dark .el-card {
  background: rgba(31, 41, 55, 0.9) !important;
  backdrop-filter: blur(10px);
}

html.dark .text-gray-900 {
  color: #f3f4f6 !important;
}

html.dark .text-gray-600 {
  color: #d1d5db !important;
}

html.dark .text-gray-800 {
  color: #f3f4f6 !important;
}

html.dark .bg-gradient-to-br {
  background: linear-gradient(to bottom right, #111827, #1f2937) !important;
}

/* 安全区域适配 - 处理各种浏览器工具栏（适度留白） */
.min-h-screen {
  padding-bottom: max(72px, env(safe-area-inset-bottom, 0px) + 24px) !important;
}

/* 针对iOS Safari和其他移动浏览器的特殊处理 */
@supports (padding: max(0px)) {
  .min-h-screen {
    padding-bottom: max(72px, env(safe-area-inset-bottom) + 24px) !important;
  }
}

/* 确保内容容器有适度的底部空间 */
.max-w-md {
  margin-bottom: max(16px, env(safe-area-inset-bottom, 0px) + 8px);
}
</style>
