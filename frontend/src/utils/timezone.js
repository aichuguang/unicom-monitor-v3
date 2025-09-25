/**
 * 前端时区处理工具
 * 统一处理前端的时间显示问题
 */

/**
 * 解析后端返回的时间字符串为本地时间
 * @param {string|Date} timeStr - 时间字符串或Date对象
 * @returns {Date|null} - 本地时间Date对象
 */
export function parseTime(timeStr) {
  if (!timeStr) return null
  
  try {
    // 如果已经是Date对象，直接返回
    if (timeStr instanceof Date) {
      return timeStr
    }
    
    // 解析时间字符串
    let date = new Date(timeStr)
    
    // 如果解析失败，尝试其他格式
    if (isNaN(date.getTime())) {
      // 处理格式: 2025-09-22T10:08:41 或 2025-09-22 10:08:41
      const cleanTimeStr = timeStr.replace(' ', 'T')
      date = new Date(cleanTimeStr)
    }
    
    return isNaN(date.getTime()) ? null : date
  } catch (error) {
    console.error('时间解析失败:', error, timeStr)
    return null
  }
}

/**
 * 格式化时间为本地时间字符串
 * @param {string|Date} time - 时间
 * @param {string} format - 格式类型: 'full', 'date', 'time', 'datetime', 'datetime-seconds'
 * @returns {string} - 格式化后的时间字符串
 */
export function formatTime(time, format = 'datetime') {
  const date = parseTime(time)
  if (!date) return '未知'
  
  const options = {
    timeZone: 'Asia/Shanghai', // 强制使用中国时区
  }
  
  switch (format) {
    case 'full':
      return date.toLocaleString('zh-CN', {
        ...options,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).replace(/\//g, '-')
    case 'date':
      return date.toLocaleDateString('zh-CN', {
        ...options,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      }).replace(/\//g, '-')
    case 'time':
      return date.toLocaleTimeString('zh-CN', {
        ...options,
        hour: '2-digit',
        minute: '2-digit'
      })
    case 'datetime-seconds':
      return date.toLocaleString('zh-CN', {
        ...options,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).replace(/\//g, '-')
    case 'datetime':
    default:
      return date.toLocaleString('zh-CN', {
        ...options,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }).replace(/\//g, '-')
  }
}

/**
 * 格式化为相对时间（如：3分钟前）
 * @param {string|Date} time - 时间
 * @returns {string} - 相对时间字符串
 */
export function formatRelativeTime(time) {
  const date = parseTime(time)
  if (!date) return '未知'
  
  const now = new Date()
  const diff = now - date
  const diffSeconds = Math.floor(diff / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffSeconds < 10) {
    return '刚刚'
  } else if (diffSeconds < 60) {
    return `${diffSeconds}秒前`
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return formatTime(date, 'date')
  }
}

/**
 * 获取当前本地时间
 * @returns {Date} - 当前时间
 */
export function now() {
  return new Date()
}

/**
 * 检查时间是否是今天
 * @param {string|Date} time - 时间
 * @returns {boolean} - 是否是今天
 */
export function isToday(time) {
  const date = parseTime(time)
  if (!date) return false
  
  const today = new Date()
  return date.getFullYear() === today.getFullYear() &&
         date.getMonth() === today.getMonth() &&
         date.getDate() === today.getDate()
}

/**
 * 计算时间差（毫秒）
 * @param {string|Date} time1 - 时间1
 * @param {string|Date} time2 - 时间2，默认为当前时间
 * @returns {number} - 时间差（毫秒）
 */
export function timeDiff(time1, time2 = new Date()) {
  const date1 = parseTime(time1)
  const date2 = parseTime(time2)
  
  if (!date1 || !date2) return 0
  
  return Math.abs(date2 - date1)
}

/**
 * 格式化查询时间显示
 * @param {string|Date} time - 时间
 * @returns {string} - 格式化后的时间字符串
 */
export function formatQueryTime(time) {
  if (!time) return "未知"

  const queryTime = parseTime(time)
  if (!queryTime) {
    console.warn('时间解析失败:', time)
    return "未知"
  }

  const now = new Date()
  const diffMs = now - queryTime
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)

  if (diffMins < 1) return "刚刚"
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`

  // 超过24小时显示具体时间
  return formatTime(queryTime)
}
