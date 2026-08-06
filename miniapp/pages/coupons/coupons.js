import api from '../../utils/api'

Page({
  data: {
    activeTab: 0,
    coupons: [],      // 可领取
    myCoupons: [],    // 我的
    loading: true,
  },

  onShow() {
    const token = wx.getStorageSync('token') || app.globalData.token
    if (!token) {
      this.setData({ coupons: [], myCoupons: [], loading: false })
      return
    }
    this.fetchAvailable()
    this.fetchMy()
  },

  fetchAvailable() {
    api.get('/coupons/').then(data => {
      this.setData({ coupons: data.results || data, loading: false })
    })
      .catch(() => this.setData({ loading: false }))
  },

  fetchMy() {
    api.get('/my-coupons/').then(data => {
      this.setData({ myCoupons: data.results || data })
    })
      .catch(() => {})
  },

  onTabTap(e) {
    this.setData({ activeTab: Number(e.currentTarget.dataset.index) })
  },

  /** 领取优惠券 */
  onClaim(e) {
    const id = e.currentTarget.dataset.id
    api.post(`/coupons/${id}/claim/`).then(() => {
      wx.showToast({ title: '领取成功', icon: 'success' })
      this.fetchAvailable()
      this.fetchMy()
    })
      .catch(() => {})
  },

  /** 状态标签样式 */
  getStatusInfo(status) {
    const map = {
      unused: { text: '可使用', color: '#4caf50', bg: '#f0f9eb' },
      used: { text: '已使用', color: '#909399', bg: '#f4f4f5' },
      expired: { text: '已过期', color: '#e74c3c', bg: '#fef0f0' },
    }
    return map[status] || { text: status, color: '#999', bg: '#f5f5f5' }
  },
})
