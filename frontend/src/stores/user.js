import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/utils/api'
import { storage } from '@/utils/storage'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref(null)
  const token = ref(storage.getToken())
  const refreshToken = ref(storage.getRefreshToken())

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userInfo = computed(() => user.value || {})

  // 登录
  const login = async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials)
      
      if (response.success) {
        const { user: userData, access_token, refresh_token } = response.data
        
        // 保存用户信息和令牌
        user.value = userData
        token.value = access_token
        refreshToken.value = refresh_token
        
        // 持久化存储
        storage.setToken(access_token)
        storage.setRefreshToken(refresh_token)
        storage.setUser(userData)
        
        return { success: true }
      } else {
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('登录失败:', error)
      // 优先使用后端返回的错误信息
      const message = error.response?.data?.message || error.message || '登录失败'
      return { success: false, message }
    }
  }

  // 注册
  const register = async (userData) => {
    try {
      const response = await api.post('/auth/register', userData)
      return response
    } catch (error) {
      console.error('注册失败:', error)
      // 优先使用后端返回的错误信息
      const message = error.response?.data?.message || error.message || '注册失败'
      return { success: false, message }
    }
  }

  // 登出
  const logout = async () => {
    try {
      // 调用登出API
      await api.post('/auth/logout')
    } catch (error) {
      console.error('登出API调用失败:', error)
    } finally {
      // 清除本地状态
      user.value = null
      token.value = null
      refreshToken.value = null
      
      // 清除存储
      storage.clear()
    }
  }

  // 刷新令牌
  const refreshAccessToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('没有刷新令牌')
      }

      const response = await api.post('/auth/refresh', {}, {
        headers: {
          Authorization: `Bearer ${refreshToken.value}`
        }
      })

      if (response.success) {
        const { access_token } = response.data
        token.value = access_token
        storage.setToken(access_token)
        return true
      } else {
        throw new Error(response.message)
      }
    } catch (error) {
      console.error('刷新令牌失败:', error)
      await logout()
      return false
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    // 如果没有token，直接返回
    if (!token.value) {
      return false
    }

    try {
      const response = await api.get('/auth/me')

      if (response.success) {
        user.value = response.data
        storage.setUser(response.data)
        return response.data
      } else {
        throw new Error(response.message)
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      await logout()
      throw error
    }
  }

  // 更新用户信息
  const updateUserInfo = async (userData) => {
    try {
      const response = await api.put('/auth/me', userData)
      
      if (response.success) {
        user.value = response.data
        storage.setUser(response.data)
        return { success: true, data: response.data }
      } else {
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('更新用户信息失败:', error)
      return { success: false, message: error.message || '更新失败' }
    }
  }

  // 修改密码
  const changePassword = async (passwordData) => {
    try {
      const response = await api.post('/auth/change-password', passwordData)
      return response
    } catch (error) {
      console.error('修改密码失败:', error)
      return { success: false, message: error.message || '修改密码失败' }
    }
  }

  // 注销账号
  const deleteAccount = async () => {
    try {
      const response = await api.delete('/auth/delete-account')
      if (response.success) {
        // 清除所有本地数据
        await logout()
      }
      return response
    } catch (error) {
      console.error('注销账号失败:', error)
      return { success: false, message: error.message || '注销账号失败' }
    }
  }

  // 检查登录状态
  const checkLoginStatus = async () => {
    try {
      // 从本地存储恢复用户信息
      const storedUser = storage.getUser()
      const storedToken = storage.getToken()

      if (storedUser && storedToken) {
        user.value = storedUser
        token.value = storedToken

        // 只有在有token的情况下才验证令牌有效性
        if (storedToken) {
          try {
            await fetchUserInfo()
          } catch (error) {
            // 令牌无效，尝试刷新
            const refreshed = await refreshAccessToken()
            if (refreshed) {
              await fetchUserInfo()
            } else {
              // 刷新失败，清除登录状态
              await logout()
            }
          }
        }
      }
    } catch (error) {
      console.error('检查登录状态失败:', error)
      await logout()
    }
  }

  // 重置状态
  const reset = () => {
    user.value = null
    token.value = null
    refreshToken.value = null
  }

  return {
    // 状态
    user,
    token,
    refreshToken,
    
    // 计算属性
    isLoggedIn,
    isAdmin,
    userInfo,
    
    // 方法
    login,
    register,
    logout,
    refreshAccessToken,
    fetchUserInfo,
    updateUserInfo,
    changePassword,
    deleteAccount,
    checkLoginStatus,
    reset
  }
})
