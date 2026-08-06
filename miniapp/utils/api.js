/**
 * 迈科咖啡 · API 请求封装
 * 统一处理 token 注入、错误拦截、Promise 包装
 */
const app = getApp()

const request = (url, options = {}) => {
  const token = app.globalData.token

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBase}${url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.header,
      },
      success(res) {
        const { statusCode, data } = res

        // 401 → token 失效，清除登录态
        if (statusCode === 401) {
          app.globalData.token = null
          app.globalData.userInfo = null
          wx.removeStorageSync('token')
          reject({ code: 401, msg: '未授权' })
          return
        }

        // 后端统一格式 { code, data, msg }
        if (data && data.code === 0) {
          resolve(data.data)
        } else {
          wx.showToast({ title: data.msg || '请求失败', icon: 'none' })
          reject(data)
        }
      },
      fail(err) {
        wx.showToast({ title: '网络异常', icon: 'none' })
        reject({ code: -1, msg: '网络异常', err })
      },
    })
  })
}

/** 快捷方法 */
const api = {
  get: (url, data) => request(url, { method: 'GET', data }),
  post: (url, data) => request(url, { method: 'POST', data }),
  put: (url, data) => request(url, { method: 'PUT', data }),
  del: (url, data) => request(url, { method: 'DELETE', data }),
}

export default api
