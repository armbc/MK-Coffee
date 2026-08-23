const app = getApp()
const swipe = require('../../utils/swipe-tab').bind('/pages/user/user')

Page({
  onSwipeStart: swipe.onSwipeStart,
  onSwipeEnd: swipe.onSwipeEnd,
  data: {
    loggedIn: false,
    userInfo: null,
    maxWidth: 0,
    /** 编辑资料弹窗 */
    showEdit: false,
    editNickname: '',
    editAvatar: '',
    saving: false,
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
  goStore() { wx.navigateTo({ url: '/pages/store/store' }) },

  // ---- 编辑资料 ----

  openEdit() {
    const u = this.data.userInfo || {}
    this.setData({
      showEdit: true,
      editNickname: u.nickname || '',
      editAvatar: u.avatar || '',
      saving: false, // 重置，避免上次保存卡死导致按钮失效
    })
  },

  closeEdit() {
    // 取消不依赖 saving：保存中关闭弹窗也允许（保存结果会异步刷新）
    this.setData({ showEdit: false, saving: false })
  },

  noop() {},

  /** 选择头像（微信返回本地临时路径） */
  onChooseAvatar(e) {
    this.setData({ editAvatar: e.detail.avatarUrl })
  },

  onNicknameInput(e) {
    this.setData({ editNickname: e.detail.value })
  },

  /** 保存资料：昵称 POST 更新；头像上传 */
  saveProfile() {
    if (this.data.saving) return
    const nickname = (this.data.editNickname || '').trim()
    if (!nickname) {
      wx.showToast({ title: '请输入昵称', icon: 'none' })
      return
    }
    this.setData({ saving: true })

    const u = this.data.userInfo || {}
    const tasks = []
    if (nickname !== (u.nickname || '')) {
      tasks.push(api.post('/user/me/update/', { nickname }))
    }
    if (this.data.editAvatar && this.data.editAvatar !== (u.avatar || '')) {
      tasks.push(this._uploadAvatar(this.data.editAvatar))
    }
    if (tasks.length === 0) {
      this.setData({ saving: false, showEdit: false })
      return
    }
    Promise.all(tasks)
      .then(() => {
        wx.showToast({ title: '已保存', icon: 'success' })
        this.setData({ saving: false, showEdit: false })
        this._refreshProfile()
      })
      .catch(() => {
        this.setData({ saving: false })
        wx.showToast({ title: '保存失败，请重试', icon: 'none' })
      })
  },

  /** 上传头像文件到服务器 */
  _uploadAvatar(filePath) {
    const app = getApp()
    const token = wx.getStorageSync('token')
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${app.globalData.apiBase}/user/me/avatar/`,
        filePath,
        name: 'avatar',
        header: { Authorization: `Bearer ${token}` },
        success: (res) => {
          try {
            const data = JSON.parse(res.data)
            if (data.code === 0) resolve(data.data)
            else reject(data)
          } catch (e) { reject(e) }
        },
        fail: reject,
      })
    })
  },

  /** 保存后重新拉取用户信息（更新页面 + 全局） */
  _refreshProfile() {
    const app = getApp()
    const token = wx.getStorageSync('token')
    wx.request({
      url: `${app.globalData.apiBase}/user/me/`,
      method: 'GET',
      header: { Authorization: `Bearer ${token}` },
      success: (res) => {
        if (res.data && res.data.code === 0 && res.data.data) {
          const user = res.data.data
          this.setData({ userInfo: user })
          app.globalData.userInfo = user
          wx.setStorageSync('userInfo', user)
        }
      },
    })
  },
})
