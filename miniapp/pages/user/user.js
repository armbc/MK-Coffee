const app = getApp()
const swipe = require('../../utils/swipe-tab').bind('/pages/user/user')

Page({
  onSwipeStart: swipe.onSwipeStart,
  onSwipeEnd: swipe.onSwipeEnd,
  data: {
    loggedIn: false,
    userInfo: null,
    maxWidth: 0,
  },

  onShow() {
    const dev = app.globalData.device
    if (dev) this.setData({ maxWidth: dev.maxWidth || 0 })
    this.checkLogin()
  },

  checkLogin() {
    const token = app.globalData.token
    this.setData({ loggedIn: !!token, userInfo: app.globalData.userInfo || null })
  },

  doLogin() {
    wx.showLoading({ title: '登录中...', mask: true })
    app.wxLogin().then(user => {
      wx.hideLoading()
      this.setData({ loggedIn: true, userInfo: user })
      wx.showToast({ title: '登录成功', icon: 'success' })
    }).catch(err => {
      wx.hideLoading()
      wx.showToast({ title: err.msg || '登录失败', icon: 'none' })
    })
  },

  doLogout() {
    wx.showModal({
      title: '确认退出', content: '退出后需要重新登录',
      success: (res) => {
        if (res.confirm) {
          app.globalData.token = ''
          app.globalData.userInfo = null
          wx.removeStorageSync('token')
          wx.removeStorageSync('refresh')
          this.setData({ loggedIn: false, userInfo: null })
        }
      },
    })
  },

  goOrders() { wx.switchTab({ url: '/pages/order/order' }) },
  goAddress() { wx.navigateTo({ url: '/pages/addresses/addresses' }) },
  goCoupons() { wx.navigateTo({ url: '/pages/coupons/coupons' }) },
})
