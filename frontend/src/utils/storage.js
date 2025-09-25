// 本地存储工具类
const STORAGE_KEYS = {
  TOKEN: 'unicom_monitor_token',
  REFRESH_TOKEN: 'unicom_monitor_refresh_token',
  USER: 'unicom_monitor_user',
  SETTINGS: 'unicom_monitor_settings',
  THEME: 'unicom_monitor_theme'
}

class Storage {
  constructor() {
    this.isSupported = this.checkSupport()
  }

  // 检查localStorage支持
  checkSupport() {
    try {
      const test = '__storage_test__'
      localStorage.setItem(test, test)
      localStorage.removeItem(test)
      return true
    } catch (e) {
      console.warn('localStorage不支持，将使用内存存储')
      this.memoryStorage = {}
      return false
    }
  }

  // 设置数据
  setItem(key, value) {
    try {
      const data = JSON.stringify(value)
      if (this.isSupported) {
        localStorage.setItem(key, data)
      } else {
        this.memoryStorage[key] = data
      }
    } catch (error) {
      console.error('存储数据失败:', error)
    }
  }

  // 获取数据
  getItem(key) {
    try {
      let data
      if (this.isSupported) {
        data = localStorage.getItem(key)
      } else {
        data = this.memoryStorage[key]
      }
      
      return data ? JSON.parse(data) : null
    } catch (error) {
      console.error('读取数据失败:', error)
      return null
    }
  }

  // 删除数据
  removeItem(key) {
    try {
      if (this.isSupported) {
        localStorage.removeItem(key)
      } else {
        delete this.memoryStorage[key]
      }
    } catch (error) {
      console.error('删除数据失败:', error)
    }
  }

  // 清空所有数据
  clear() {
    try {
      if (this.isSupported) {
        // 只清除应用相关的数据
        Object.values(STORAGE_KEYS).forEach(key => {
          localStorage.removeItem(key)
        })
      } else {
        this.memoryStorage = {}
      }
    } catch (error) {
      console.error('清空数据失败:', error)
    }
  }

  // 获取所有键
  getAllKeys() {
    try {
      if (this.isSupported) {
        return Object.keys(localStorage).filter(key => 
          Object.values(STORAGE_KEYS).includes(key)
        )
      } else {
        return Object.keys(this.memoryStorage)
      }
    } catch (error) {
      console.error('获取键列表失败:', error)
      return []
    }
  }

  // 获取存储大小
  getSize() {
    try {
      let size = 0
      if (this.isSupported) {
        Object.values(STORAGE_KEYS).forEach(key => {
          const value = localStorage.getItem(key)
          if (value) {
            size += value.length
          }
        })
      } else {
        Object.values(this.memoryStorage).forEach(value => {
          size += value.length
        })
      }
      return size
    } catch (error) {
      console.error('计算存储大小失败:', error)
      return 0
    }
  }

  // 令牌相关方法
  setToken(token) {
    this.setItem(STORAGE_KEYS.TOKEN, token)
  }

  getToken() {
    return this.getItem(STORAGE_KEYS.TOKEN)
  }

  removeToken() {
    this.removeItem(STORAGE_KEYS.TOKEN)
  }

  setRefreshToken(token) {
    this.setItem(STORAGE_KEYS.REFRESH_TOKEN, token)
  }

  getRefreshToken() {
    return this.getItem(STORAGE_KEYS.REFRESH_TOKEN)
  }

  removeRefreshToken() {
    this.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
  }

  // 用户信息相关方法
  setUser(user) {
    this.setItem(STORAGE_KEYS.USER, user)
  }

  getUser() {
    return this.getItem(STORAGE_KEYS.USER)
  }

  removeUser() {
    this.removeItem(STORAGE_KEYS.USER)
  }

  // 设置相关方法
  setSettings(settings) {
    this.setItem(STORAGE_KEYS.SETTINGS, settings)
  }

  getSettings() {
    return this.getItem(STORAGE_KEYS.SETTINGS) || {}
  }

  updateSettings(newSettings) {
    const currentSettings = this.getSettings()
    const updatedSettings = { ...currentSettings, ...newSettings }
    this.setSettings(updatedSettings)
    return updatedSettings
  }

  removeSettings() {
    this.removeItem(STORAGE_KEYS.SETTINGS)
  }

  // 主题相关方法
  setTheme(theme) {
    this.setItem(STORAGE_KEYS.THEME, theme)
  }

  getTheme() {
    return this.getItem(STORAGE_KEYS.THEME)
  }

  removeTheme() {
    this.removeItem(STORAGE_KEYS.THEME)
  }
}

// 创建存储实例
export const storage = new Storage()

// 会话存储工具类 (改用localStorage)
class SessionStorage {
  constructor() {
    this.isSupported = this.checkSupport()
  }

  checkSupport() {
    try {
      const test = '__session_test__'
      localStorage.setItem(test, test)
      localStorage.removeItem(test)
      return true
    } catch (e) {
      console.warn('localStorage不支持，将使用内存存储')
      this.memoryStorage = {}
      return false
    }
  }

  setItem(key, value) {
    try {
      const data = JSON.stringify(value)
      if (this.isSupported) {
        localStorage.setItem(key, data)
      } else {
        this.memoryStorage[key] = data
      }
    } catch (error) {
      console.error('会话存储数据失败:', error)
    }
  }

  getItem(key) {
    try {
      let data
      if (this.isSupported) {
        data = localStorage.getItem(key)
      } else {
        data = this.memoryStorage[key]
      }

      return data ? JSON.parse(data) : null
    } catch (error) {
      console.error('读取会话数据失败:', error)
      return null
    }
  }

  removeItem(key) {
    try {
      if (this.isSupported) {
        localStorage.removeItem(key)
      } else {
        delete this.memoryStorage[key]
      }
    } catch (error) {
      console.error('删除会话数据失败:', error)
    }
  }

  clear() {
    try {
      if (this.isSupported) {
        // 只清除我们的数据，不清除整个localStorage
        Object.values(STORAGE_KEYS).forEach(key => {
          localStorage.removeItem(key)
        })
      } else {
        this.memoryStorage = {}
      }
    } catch (error) {
      console.error('清空会话数据失败:', error)
    }
  }
}

// 创建会话存储实例
export const sessionStorage = new SessionStorage()

export default storage
