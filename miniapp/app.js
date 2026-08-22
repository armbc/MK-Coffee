/**
 * 迈科咖啡 · 小程序入口
 * 基础库版本要求：≥ 2.18.0
 */
App({
  onLaunch() {
    // 设备检测（使用新版 API，兼容旧版）
    let width, height, pixelRatio
    if (wx.getWindowInfo) {
      const win = wx.getWindowInfo()
      width = win.windowWidth
      height = win.windowHeight
      pixelRatio = win.pixelRatio
    } else {
      const info = wx.getSystemInfoSync()
      width = info.windowWidth
      height = info.windowHeight
      pixelRatio = info.pixelRatio
    }

    let deviceType = 'phone'
    if (width >= 768) {
      deviceType = 'desktop'
    } else if (width >= 420) {
      deviceType = 'tablet'
    }

    this.globalData.device = {
      type: deviceType,
      width,
      height,
      pixelRatio,
      isPhone: deviceType === 'phone',
      isTablet: deviceType === 'tablet',
      isDesktop: deviceType === 'desktop',
      /** 商品网格列数 */
      gridCols: deviceType === 'phone' ? 2 : deviceType === 'tablet' ? 3 : 4,
      /** 页面最大宽度（桌面端居中） */
      maxWidth: deviceType === 'desktop' ? 960 : 0,
      /** 字体缩放因子 */
      fontScale: deviceType === 'desktop' ? 1.1 : 1,
    }

    // Token & userInfo 恢复
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    if (token) {
      this.globalData.token = token
      if (userInfo) {
        this.globalData.userInfo = userInfo
      }
      this.checkLoginStatus()
      this.fetchUserProfile()
    }
  },

  globalData: {
    token: '',
    refresh: '',
    userInfo: null,
    apiBase: 'https://api.mk-coffee.cn/api',
    device: null,
  },

  /** 微信登录：code → 后端换取 JWT */
  wxLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (loginRes) => {
          if (!loginRes.code) {
            reject({ msg: 'wx.login 失败' })
            return
          }
          wx.request({
            url: `${this.globalData.apiBase}/auth/wx-login/`,
            method: 'POST',
            data: { code: loginRes.code },
            success: (res) => {
              const { data } = res
              if (data && data.code === 0) {
                const { access, refresh, user } = data.data
                this.globalData.token = access
                this.globalData.refresh = refresh
                this.globalData.userInfo = user
                wx.setStorageSync('token', access)
                wx.setStorageSync('refresh', refresh)
                resolve(user)
              } else {
                reject(data)
              }
            },
            fail: (err) => {
              reject({ msg: '网络异常', err })
            },
          })
        },
        fail: (err) => {
          reject({ msg: 'wx.login 失败', err })
        },
      })
    })
  },

  /** 拉取当前用户信息 */
  fetchUserProfile() {
    const token = this.globalData.token
    if (!token) return
    wx.request({
      url: `${this.globalData.apiBase}/user/me/`,
      method: 'GET',
      header: { Authorization: `Bearer ${token}` },
      success: (res) => {
        const { data } = res
        if (data && data.code === 0 && data.data) {
          this.globalData.userInfo = data.data
          wx.setStorageSync('userInfo', data.data)
        }
      },
      fail: (err) => {
        console.warn('拉取用户信息失败', err)
      },
    })
  },

  /** 检查 session_key 有效性，失效时清理登录态 */
  checkLoginStatus() {
    wx.checkSession({
      success: () => {},
      fail: () => {
        this.globalData.token = ''
        this.globalData.userInfo = null
        wx.removeStorageSync('token')
        wx.removeStorageSync('userInfo')
      },
    })
  },
})
