import api from '../../utils/api'
const app = getApp()
const swipe = require('../../utils/swipe-tab').bind('/pages/cart/cart')

Page({
  onSwipeStart: swipe.onSwipeStart,
  onSwipeEnd: swipe.onSwipeEnd,
  data: {
    items: [],
    total: '0.00',
    loading: true,
    maxWidth: 0,
  },

  onShow() {
    const dev = app.globalData.device
    if (dev) this.setData({ maxWidth: dev.maxWidth || 0 })
    this.fetchCart()
  },

  fetchCart() {
    const token = wx.getStorageSync('token') || app.globalData.token
    if (!token) {
      this.setData({ items: [], loading: false })
      return
    }
    api.get('/cart/').then(data => {
      const oldItems = this.data.items
      const items = (data.results || data).map(item => ({
        ...item,
        unit_price_text: Number(item.unit_price).toFixed(2),
        subtotal_text: Number(item.subtotal).toFixed(2),
        isSelected: this._wasSelected(oldItems, item.id),
      }))
      const allSelected = items.length > 0 && items.every(i => i.isSelected)
      this.setData({ items, loading: false, allSelected }, () => this._recalc())
    }).catch(() => this.setData({ loading: false }))
  },

  _wasSelected(oldItems, id) {
    const found = oldItems.find(i => i.id === id)
    return found ? !!found.isSelected : false
  },

  onToggleSelect(e) {
    const id = Number(e.currentTarget.dataset.id)
    const items = this.data.items
    const idx = items.findIndex(i => i.id === id)
    if (idx === -1) return

    const newVal = !items[idx].isSelected
    const upd = { [`items[${idx}].isSelected`]: newVal }
    if (!newVal) upd.allSelected = false
    else upd.allSelected = items.every((it, j) => j === idx || it.isSelected)

    let sum = 0
    for (let j = 0; j < items.length; j++) {
      if ((j === idx ? newVal : items[j].isSelected)) sum += Number(items[j].subtotal)
    }
    upd.total = sum.toFixed(2)
    this.setData(upd)
  },

  onToggleAll() {
    const items = this.data.items
    const wasAll = items.length > 0 && items.every(i => i.isSelected)
    const newVal = !wasAll
    const upd = {}
    for (let j = 0; j < items.length; j++) upd[`items[${j}].isSelected`] = newVal
    upd.allSelected = newVal && items.length > 0
    upd.total = newVal ? items.reduce((s, i) => s + Number(i.subtotal), 0).toFixed(2) : '0.00'
    this.setData(upd)
  },

  _recalc() {
    const items = this.data.items
    let sum = 0, all = items.length > 0
    for (const i of items) { if (i.isSelected) sum += Number(i.subtotal); else all = false }
    this.setData({ total: sum.toFixed(2), allSelected: all })
  },

  onQuantityChange(e) {
    const id = Number(e.currentTarget.dataset.id)
    const delta = Number(e.currentTarget.dataset.delta)
    const item = this.data.items.find(i => i.id === id)
    if (!item) return
    const newQty = item.quantity + delta
    if (newQty < 1) return
    api.post(`/cart/${id}/update-qty/`, { quantity: newQty }).then(() => this.fetchCart()).catch(() => {})
  },

  onDelete(e) {
    const id = Number(e.currentTarget.dataset.id)
    wx.showModal({
      title: '确认删除',
      content: '确定要移除此商品吗？',
      success: (res) => {
        if (res.confirm) {
          api.post(`/cart/${id}/remove/`)
            .then(() => { wx.showToast({ title: '已删除', icon: 'success' }) })
            .catch(() => {})
            .finally(() => this.fetchCart())
        }
      },
    })
  },

  goShop() { wx.switchTab({ url: '/pages/index/index' }) },

  createOrder() {
    const selected = this.data.items.filter(i => i.isSelected)
    if (selected.length === 0) {
      wx.showToast({ title: '请先选择商品', icon: 'none' })
      return
    }
    wx.showModal({
      title: '确认下单',
      content: `合计 ¥${this.data.total}，确认提交订单？`,
      success: (res) => {
        if (res.confirm) {
          api.post('/orders/', { item_ids: selected.map(i => i.id) }).then(data => {
            wx.showToast({ title: '下单成功', icon: 'success' })
            // order 是 tabBar 页面，switchTab 不支持传参
            // 通过 app 全局变量传递最新订单 ID
            app.globalData.newOrderId = data.id
            setTimeout(() => {
              wx.switchTab({ url: '/pages/order/order' })
            }, 1000)
          }).catch(() => {})
        }
      },
    })
  },
})
