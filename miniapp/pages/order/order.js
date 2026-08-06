import api from '../../utils/api'
const app = getApp()
const swipe = require('../../utils/swipe-tab').bind('/pages/order/order')

const STATUS_TABS = [
  { key: '', label: '全部' },
  { key: 'pending', label: '待支付' },
  { key: 'paid', label: '已支付' },
  { key: 'shipped', label: '已发货' },
  { key: 'completed', label: '已完成' },
  { key: 'cancelled', label: '已取消' },
]

const STATUS_MAP = {
  pending: { text: '待支付', color: '#e8873a', bg: '#fff8f2' },
  paid: { text: '已支付', color: '#4caf50', bg: '#f0f9eb' },
  shipped: { text: '已发货', color: '#409eff', bg: '#ecf5ff' },
  completed: { text: '已完成', color: '#909399', bg: '#f4f4f5' },
  cancelled: { text: '已取消', color: '#e74c3c', bg: '#fef0f0' },
}

Page({
  onSwipeStart: swipe.onSwipeStart,
  onSwipeEnd: swipe.onSwipeEnd,
  data: {
    tabs: STATUS_TABS,
    activeTab: 0,
    orders: [],
    filteredOrders: [],
    loading: true,
    detailOrder: null,
    maxWidth: 0,
  },

  onLoad(opts) {
    const dev = app.globalData.device
    if (dev) this.setData({ maxWidth: dev.maxWidth || 0 })
    if (opts.id) this.fetchDetail(opts.id)
  },

  onShow() { if (!this.data.detailOrder) this.fetchOrders() },

  fetchOrders() {
    const token = wx.getStorageSync('token') || app.globalData.token
    if (!token) {
      this.setData({ orders: [], loading: false })
      return
    }
    this.setData({ loading: true })
    api.get('/orders/').then(data => {
      const orders = (data.results || data).map(o => ({
        ...o, total_text: Number(o.total).toFixed(2),
        status_info: STATUS_MAP[o.status] || {},
      }))
      this.setData({ orders, loading: false }, () => this.applyFilter())
    })
      .catch(() => this.setData({ loading: false }))
  },

  fetchDetail(id) {
    api.get(`/orders/${id}/`).then(data => {
      const detail = {
        ...data, total_text: Number(data.total).toFixed(2),
        status_info: STATUS_MAP[data.status] || {},
        items: (data.items || []).map(it => ({
          ...it, price_text: Number(it.price).toFixed(2),
          subtotal_text: Number(it.subtotal).toFixed(2),
        })),
      }
      this.setData({ detailOrder: detail })
    })
      .catch(() => {})
  },

  applyFilter() {
    const { orders, activeTab } = this.data
    const key = STATUS_TABS[activeTab].key
    this.setData({ filteredOrders: key ? orders.filter(o => o.status === key) : orders })
  },

  onTabTap(e) {
    this.setData({ activeTab: Number(e.currentTarget.dataset.index) }, () => this.applyFilter())
  },

  onCancel(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认取消', content: '确定要取消此订单吗？',
      success: (res) => {
        if (res.confirm) {
          api.post(`/orders/${id}/cancel/`).then(() => {
            wx.showToast({ title: '已取消', icon: 'success' })
            this.fetchOrders()
          })
            .catch(() => {})
        }
      },
    })
  },

  onPay(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认支付', content: '模拟支付，确认后将标记为已支付',
      success: (res) => {
        if (res.confirm) {
          api.post(`/orders/${id}/pay/`).then(() => {
            wx.showToast({ title: '支付成功', icon: 'success' })
            this.fetchOrders()
          })
            .catch(() => {})
        }
      },
    })
  },

  onDetail(e) {
    wx.navigateTo({ url: `/pages/order/order?id=${e.currentTarget.dataset.id}` })
  },

  backToList() { this.setData({ detailOrder: null }, () => this.fetchOrders()) },
})
