<template>
  <div class="min-h-screen bg-gray-50">
    <main class="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200">
        <div class="p-6">
          <h1 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
            <el-icon class="mr-3 text-blue-500" :size="28"><Document /></el-icon>
            📖 使用说明
          </h1>
          
          <!-- 教程部分 -->
          <div class="mb-8">
            <h2 class="text-xl font-semibold text-gray-700 mb-4 flex items-center">
              <el-icon class="mr-2 text-blue-500"><Document /></el-icon>
              教程
            </h2>
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <ol class="list-decimal list-inside space-y-3 text-gray-700">
                <li class="font-medium">注册平台账号并登录</li>
                <li class="font-medium">添加联通账号（最多5个）</li>
                <li class="font-medium">使用中国联通APP获取验证码</li>
                <li class="font-medium">输入验证码完成联通账号认证</li>
                <li class="font-medium">在首页选择已认证的手机号查询流量</li>
                <li class="font-medium">可在配置页设置监控规则和通知方式</li>
              </ol>
            </div>
          </div>

          <!-- 常见问题部分 -->
          <div>
            <h2 class="text-xl font-semibold text-gray-700 mb-4 flex items-center">
              <el-icon class="mr-2 text-orange-500"><Warning /></el-icon>
              常见问题
            </h2>
            <div class="space-y-4">
              <el-collapse v-model="activeCollapse" accordion>
                <!-- 问题1 -->
                <el-collapse-item title="1. 联通如何获取Token或Cookie？" name="1">
                  <div class="text-gray-700 space-y-3 p-4 bg-gray-50 rounded-lg">
                    <p><strong class="text-blue-600">方法：</strong>通过抓中国联通APP包获取</p>
                    <ul class="list-disc list-inside ml-4 space-y-2">
                      <li><strong>Cookie：</strong>任一接口都有Cookie信息</li>
                      <li><strong>Token：</strong>抓登录包、切换账号包</li>
                    </ul>
                  </div>
                </el-collapse-item>

                <!-- 问题2 -->
                <el-collapse-item title="2. 联通如何获取AppID？" name="2">
                  <div class="text-gray-700 space-y-4 p-4 bg-gray-50 rounded-lg">
                    <div>
                      <p><strong class="text-green-600">安卓设备：</strong></p>
                      <ul class="list-disc list-inside ml-4 space-y-1 mt-2">
                        <li><code class="bg-gray-200 px-2 py-1 rounded text-sm">/storage/Unicom/appid</code></li>
                        <li><code class="bg-gray-200 px-2 py-1 rounded text-sm">/storage/emulated/0/Documents/Unicom/appid</code></li>
                        <li><code class="bg-gray-200 px-2 py-1 rounded text-sm">/storage/emulated/0/Android/data/com.sinovatech.unicom.ui/files/Documents/Unicom/</code></li>
                        <li>或者直接在本地存储根目录搜索"appid"，找到并打开该文件复制里面的内容</li>
                        <li>也可以从抓包中提取</li>
                      </ul>
                    </div>
                    <div>
                      <p><strong class="text-purple-600">苹果设备：</strong></p>
                      <ul class="list-disc list-inside ml-4 mt-2">
                        <li>使用抓包软件获取</li>
                      </ul>
                    </div>
                    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <p><strong class="text-yellow-700">💡 提示：</strong>注意获取Token和登录需要使用同一个AppID。抓Token时请求参数里的AppID字段值或者返回值。</p>
                    </div>
                  </div>
                </el-collapse-item>

                <!-- 问题3 -->
                <el-collapse-item title="3. 当前账号登录需要图形验证码校验" name="3">
                  <div class="text-gray-700 p-4 bg-gray-50 rounded-lg">
                    <p><strong class="text-blue-600">解决方法：</strong></p>
                    <ol class="list-decimal list-inside ml-4 space-y-2 mt-2">
                      <li>使用中国联通APP输入手机号</li>
                      <li>获取验证码</li>
                      <li>收到验证码后，填写到页面中</li>
                    </ol>
                  </div>
                </el-collapse-item>

                <!-- 问题4 -->
                <el-collapse-item title="4. 提示：尊敬的客户您好，请使用短信验证码登录进行身份验证！" name="4">
                  <div class="text-gray-700 p-4 bg-gray-50 rounded-lg">
                    <p><strong class="text-red-600">可能原因：</strong></p>
                    <ul class="list-disc list-inside ml-4 space-y-1 mt-2">
                      <li>AppID无效</li>
                      <li>与之前操作使用的AppID不一致</li>
                    </ul>
                  </div>
                </el-collapse-item>

                <!-- 问题5 -->
                <el-collapse-item title="5. 系统检测到您的账号绑定列表绑定关系失效" name="5">
                  <div class="text-gray-700 space-y-3 p-4 bg-gray-50 rounded-lg">
                    <div class="bg-red-50 border border-red-200 rounded p-3">
                      <p><strong class="text-red-600">错误信息：</strong>"系统检测到您的账号绑定列表绑定关系失效，为保障您的正常使用，请使用短信验证码重新登录"</p>
                    </div>
                    <p><strong class="text-red-600">可能原因：</strong></p>
                    <ul class="list-disc list-inside ml-4 space-y-1">
                      <li>获取验证码时用的AppID和登录时候用的AppID不是同一个</li>
                      <li>Token或Cookie不正确</li>
                    </ul>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Document, Warning } from '@/utils/icons'

// 折叠面板状态
const activeCollapse = ref('')
</script>

<style scoped>
/* 自定义样式 */
.el-collapse-item :deep(.el-collapse-item__header) {
  font-weight: 600;
  font-size: 16px;
  color: #374151;
}

.el-collapse-item :deep(.el-collapse-item__content) {
  padding-bottom: 0;
}

code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}
</style>
