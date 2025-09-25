import axios from 'axios'
import { ElMessage } from 'element-plus'
import { storage } from './storage'

// 防止无限刷新的标志
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })

  failedQueue = []
}

// 创建axios实例
const instance = axios.create({
  baseURL: import.meta.env.DEV ? '/api' : '/api',  // 生产环境也使用相对路径，通过nginx代理
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    // 添加认证令牌
    const token = storage.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 添加请求时间戳
    config.metadata = { startTime: new Date() }
    
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    // 计算请求耗时
    const endTime = new Date()
    const duration = endTime - response.config.metadata.startTime
    console.log(`API请求耗时: ${duration}ms - ${response.config.url}`)
    
    // 返回响应数据
    return response.data
  },
  async (error) => {
    const { response, config } = error
    
    // 网络错误
    if (!response) {
      ElMessage.error('网络连接失败，请检查网络设置')
      return Promise.reject(new Error('网络连接失败'))
    }
    
    const { status, data } = response
    
    // 处理不同的HTTP状态码
    switch (status) {
      case 401:
        // 如果是登录请求失败，不进行自动处理，让业务逻辑处理
        if (config.url.includes('/auth/login')) {
          break
        }

        // 如果是刷新token请求失败，直接跳转登录
        if (config.url.includes('/auth/refresh')) {
          storage.clear()
          window.location.href = '/#/login'
          return Promise.reject(error)
        }

        // 如果正在刷新token，将请求加入队列
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject })
          }).then(token => {
            config.headers.Authorization = `Bearer ${token}`
            return instance(config)
          }).catch(err => {
            return Promise.reject(err)
          })
        }

        // 开始刷新token
        if (!config._retry) {
          config._retry = true
          isRefreshing = true

          const refreshToken = storage.getRefreshToken()
          if (!refreshToken) {
            storage.clear()
            window.location.href = '/#/login'
            return Promise.reject(error)
          }

          try {
            // 直接使用axios发送刷新请求，避免拦截器循环
            const refreshResponse = await axios.post(`${config.baseURL}/auth/refresh`, {}, {
              headers: { Authorization: `Bearer ${refreshToken}` }
            })

            if (refreshResponse.data.success) {
              const { access_token } = refreshResponse.data.data
              storage.setToken(access_token)

              // 处理队列中的请求
              processQueue(null, access_token)

              // 重新发送原请求
              config.headers.Authorization = `Bearer ${access_token}`
              return instance(config)
            } else {
              throw new Error('刷新token失败')
            }
          } catch (refreshError) {
            console.error('刷新令牌失败:', refreshError)
            processQueue(refreshError, null)
            storage.clear()
            window.location.href = '/#/login'
            return Promise.reject(refreshError)
          } finally {
            isRefreshing = false
          }
        }
        break
        
      case 403:
        // 不显示全局错误消息，让业务逻辑处理
        break

      case 404:
        // 不显示全局错误消息，让业务逻辑处理
        break

      case 429:
        // 不显示全局错误消息，让业务逻辑处理
        break

      case 500:
        // 只有在没有具体错误消息时才显示通用错误
        if (!data?.message) {
          ElMessage.error('服务器内部错误')
        }
        break

      default:
        // 不显示全局错误消息，让业务逻辑处理后端返回的具体错误信息
        break
    }
    
    return Promise.reject(error)
  }
)

// API方法封装
export const api = {
  // GET请求
  get(url, params = {}, config = {}) {
    return instance.get(url, { params, ...config })
  },
  
  // POST请求
  post(url, data = {}, config = {}) {
    return instance.post(url, data, config)
  },
  
  // PUT请求
  put(url, data = {}, config = {}) {
    return instance.put(url, data, config)
  },
  
  // DELETE请求
  delete(url, config = {}) {
    return instance.delete(url, config)
  },
  
  // PATCH请求
  patch(url, data = {}, config = {}) {
    return instance.patch(url, data, config)
  },
  
  // 上传文件
  upload(url, formData, config = {}) {
    return instance.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      ...config
    })
  },
  
  // 下载文件
  download(url, params = {}, filename = '') {
    return instance.get(url, {
      params,
      responseType: 'blob'
    }).then(response => {
      const blob = new Blob([response])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    })
  }
}

// 具体API接口
export const authAPI = {
  // 用户登录
  login: (credentials) => api.post('/auth/login', credentials),
  
  // 用户注册
  register: (userData) => api.post('/auth/register', userData),
  
  // 用户登出
  logout: () => api.post('/auth/logout'),
  
  // 刷新令牌
  refresh: () => api.post('/auth/refresh'),
  
  // 获取用户信息
  getUserInfo: () => api.get('/auth/me'),
  
  // 更新用户信息
  updateUserInfo: (userData) => api.put('/auth/me', userData),
  
  // 修改密码
  changePassword: (passwordData) => api.post('/auth/change-password', passwordData)
}

export const unicomAPI = {
  // 获取联通账号列表
  getAccounts: () => api.get('/unicom/accounts'),

  // 获取单个联通账号详情（含敏感字段）
  getAccount: (accountId) => api.get(`/unicom/accounts/${accountId}`),

  // 添加联通账号
  addAccount: (accountData) => api.post('/unicom/accounts', accountData),

  // 更新联通账号
  updateAccount: (accountId, accountData) => api.put(`/unicom/accounts/${accountId}`, accountData),

  // 删除联通账号
  deleteAccount: (accountId) => api.delete(`/unicom/accounts/${accountId}`),

  // 验证码登录
  smsLogin: (accountId, smsCode) => api.post(`/unicom/accounts/${accountId}/login/sms`, { sms_code: smsCode }),

  // Token登录
  tokenLogin: (accountId, tokenData) => api.post(`/unicom/accounts/${accountId}/login/token`, tokenData),

  // 刷新认证
  refreshAuth: (accountId) => api.post(`/unicom/accounts/${accountId}/refresh`),

  // 切换监控与通知开关
  toggleMonitor: (accountId, enabled) => api.post(`/unicom/accounts/${accountId}/monitor-toggle`, { enabled })
}

// 为了兼容旧版本的导入，添加别名
export const accountAPI = unicomAPI

export const flowAPI = {
  // 查询单个账号流量
  queryFlow: (accountId, params = {}) => api.get(`/flow/query/${accountId}`, params),
  
  // 查询所有账号流量
  queryAllFlows: (params = {}) => api.get('/flow/query-all', params),
  
  // 获取流量历史
  getFlowHistory: (accountId, params = {}) => api.get(`/flow/history/${accountId}`, params),
  
  // 获取流量统计
  getFlowStatistics: (accountId, params = {}) => api.get(`/flow/statistics/${accountId}`, params)
}

export const monitorAPI = {
  // 获取监控配置列表
  getConfigs: () => api.get('/monitor/configs'),

  // 获取指定账号监控配置
  getConfig: (accountId) => api.get(`/monitor/configs/${accountId}`),

  // 保存监控配置
  saveConfig: (accountId, configData) => api.post(`/monitor/configs/${accountId}`, configData),

  // 更新监控配置
  updateConfig: (accountId, configData) => api.put(`/monitor/configs/${accountId}`, configData),

  // 切换监控状态
  toggleMonitor: (accountId) => api.post(`/monitor/configs/${accountId}/toggle`),

  // 删除监控配置
  deleteConfig: (accountId) => api.delete(`/monitor/configs/${accountId}`),

  // 获取监控状态
  getStatus: () => api.get('/monitor/status'),

  // 测试通知
  testNotification: (accountId) => api.post(`/monitor/test-notification/${accountId}`)
}


export const adminAPI = {
  // 获取仪表板统计
  getDashboardStats: () => api.get('/admin/dashboard'),
  
  // 获取用户列表
  getUsers: (params = {}) => api.get('/admin/users', params),
  
  // 更新用户状态
  updateUserStatus: (userId, status) => api.put(`/admin/users/${userId}/status`, { status }),
  
  // 获取系统日志
  getLogs: (params = {}) => api.get('/admin/logs', params),
  
  // 获取代理列表
  getProxies: (params = {}) => api.get('/admin/proxies', params),
  
  // 添加代理
  addProxy: (proxyData) => api.post('/admin/proxies', proxyData),
  
  // 更新代理状态
  updateProxyStatus: (proxyId, status) => api.put(`/admin/proxies/${proxyId}/status`, { status }),
  
  // 清理缓存
  clearCache: (cacheType = 'all') => api.post('/admin/cache/clear', { cache_type: cacheType })
}

export const notifyAPI = {
  createWxPusherQr: (payload = {}) => api.post('/notify/wxpusher/qrcode', payload),
  queryWxPusherScan: (code) => api.get('/notify/wxpusher/scan-result', { code }),
  sendTest: (channel, settings, title = '测试通知', content = '这是一条测试通知') => api.post('/notify/send-test', { channel, settings, title, content })
}

export const settingsAPI = {
  // 缓存
  getCache: () => api.get('/settings/cache'),
  saveCache: (data) => api.post('/settings/cache', data),
  // 监控
  getMonitor: () => api.get('/settings/monitor'),
  saveMonitor: (data) => api.post('/settings/monitor', data),
  // 告警
  getAlerts: () => api.get('/settings/alerts'),
  saveAlerts: (data) => api.post('/settings/alerts', data),
  clearAlerts: (data = {}) => api.post('/settings/alerts/clear', data),
  // 通知渠道
  getNotifications: () => api.get('/settings/notifications'),
  saveNotifications: (data) => api.post('/settings/notifications', data),
  // 展示
  getDisplay: () => api.get('/settings/display'),
  saveDisplay: (data) => api.post('/settings/display', data)
}

export default api
