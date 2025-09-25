import { api } from '@/utils/api'

/**
 * 流量查询相关API
 */
export const flowAPI = {
  // 查询单个账号流量
  queryFlow: (accountId, params = {}) => api.get(`/flow/query/${accountId}`, params),
  
  // 查询所有账号流量
  queryAllFlows: (params = {}) => api.get('/flow/query-all', params),
  
  // 获取流量历史
  getFlowHistory: (accountId, params = {}) => api.get(`/flow/history/${accountId}`, params),
  
  // 获取流量统计
  getFlowStatistics: (accountId, params = {}) => api.get(`/flow/statistics/${accountId}`, params),
  
  // 刷新流量数据
  refreshFlow: (accountId, force = false) => api.post(`/flow/refresh/${accountId}`, { force }),
  
  // 获取流量缓存状态
  getCacheStatus: (accountId) => api.get(`/flow/cache-status/${accountId}`),
  
  // 清除流量缓存
  clearCache: (accountId) => api.delete(`/flow/cache/${accountId}`),
  
  // 获取流量变化对比
  getFlowComparison: (accountId, params = {}) => api.get(`/flow/comparison/${accountId}`, params),

  // 重置流量统计基准
  resetBaseline: (accountId, note = '手动重置统计基准') => api.post(`/flow/reset-baseline/${accountId}`, { note }),

  // 获取基准历史记录
  getBaselineHistory: (accountId, params = {}) => api.get(`/flow/baseline-history/${accountId}`, params)
}

export default flowAPI
