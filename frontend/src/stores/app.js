import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 状态
  const globalLoading = ref(false)
  const loadingText = ref('加载中...')
  const isMobile = ref(false)
  const isOnline = ref(navigator.onLine)
  const sidebarCollapsed = ref(false)
  const theme = ref('light')
  
  // 消息队列
  const messages = ref([])
  
  // 计算属性
  const isDesktop = computed(() => !isMobile.value)
  
  // 设置全局加载状态
  const setGlobalLoading = (loading, text = '加载中...') => {
    globalLoading.value = loading
    loadingText.value = text
  }
  
  // 设置移动端状态
  const setMobile = (mobile) => {
    isMobile.value = mobile
    // 移动端默认收起侧边栏
    if (mobile) {
      sidebarCollapsed.value = true
    }
  }
  
  // 设置网络状态
  const setOnline = (online) => {
    isOnline.value = online
  }
  
  // 切换侧边栏
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  
  // 设置侧边栏状态
  const setSidebarCollapsed = (collapsed) => {
    sidebarCollapsed.value = collapsed
  }
  
  // 切换主题
  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    // 应用主题到document
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
    // 保存到本地存储
    localStorage.setItem('theme', theme.value)
  }
  
  // 设置主题
  const setTheme = (newTheme) => {
    theme.value = newTheme
    document.documentElement.classList.toggle('dark', newTheme === 'dark')
    localStorage.setItem('theme', newTheme)
  }
  
  // 初始化主题
  const initTheme = () => {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      setTheme(savedTheme)
    } else {
      // 检查系统主题偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setTheme(prefersDark ? 'dark' : 'light')
    }
  }
  
  // 添加消息
  const addMessage = (message) => {
    const id = Date.now()
    const messageObj = {
      id,
      type: message.type || 'info',
      title: message.title || '',
      content: message.content || '',
      duration: message.duration || 3000,
      showClose: message.showClose !== false,
      timestamp: new Date()
    }
    
    messages.value.push(messageObj)
    
    // 自动移除消息
    if (messageObj.duration > 0) {
      setTimeout(() => {
        removeMessage(id)
      }, messageObj.duration)
    }
    
    return id
  }
  
  // 移除消息
  const removeMessage = (id) => {
    const index = messages.value.findIndex(msg => msg.id === id)
    if (index > -1) {
      messages.value.splice(index, 1)
    }
  }
  
  // 清空所有消息
  const clearMessages = () => {
    messages.value = []
  }
  
  // 显示成功消息
  const showSuccess = (content, title = '成功') => {
    return addMessage({
      type: 'success',
      title,
      content,
      duration: 3000
    })
  }
  
  // 显示错误消息
  const showError = (content, title = '错误') => {
    return addMessage({
      type: 'error',
      title,
      content,
      duration: 5000
    })
  }
  
  // 显示警告消息
  const showWarning = (content, title = '警告') => {
    return addMessage({
      type: 'warning',
      title,
      content,
      duration: 4000
    })
  }
  
  // 显示信息消息
  const showInfo = (content, title = '提示') => {
    return addMessage({
      type: 'info',
      title,
      content,
      duration: 3000
    })
  }
  
  // 重置应用状态
  const reset = () => {
    globalLoading.value = false
    loadingText.value = '加载中...'
    messages.value = []
  }
  
  return {
    // 状态
    globalLoading,
    loadingText,
    isMobile,
    isOnline,
    sidebarCollapsed,
    theme,
    messages,
    
    // 计算属性
    isDesktop,
    
    // 方法
    setGlobalLoading,
    setMobile,
    setOnline,
    toggleSidebar,
    setSidebarCollapsed,
    toggleTheme,
    setTheme,
    initTheme,
    addMessage,
    removeMessage,
    clearMessages,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    reset
  }
})
