import { api } from '@/utils/api'

/**
 * 联通账号相关API
 */
export const accountAPI = {
  // 获取联通账号列表
  getAccounts: () => api.get('/unicom/accounts'),
  
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
  
  // 获取账号详情
  getAccount: (accountId) => api.get(`/unicom/accounts/${accountId}`),
  
  // 更新账号状态
  updateAccountStatus: (accountId, status) => api.put(`/unicom/accounts/${accountId}/status`, { status }),
  
  // 测试账号连接
  testAccount: (accountId) => api.post(`/unicom/accounts/${accountId}/test`)
}

export default accountAPI
