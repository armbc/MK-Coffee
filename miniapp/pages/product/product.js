import api from '../../utils/api'
const app = getApp()

Page({
  data: {
    product: null,
    specs: [],
    selectedSpec: null,
    currentPrice: 0,
    currentPriceText: '0.00',
    quantity: 1,
    totalPrice: '0.00',
    /** 响应式 */
    maxWidth: 0,
    imageHeight: 500,
  },

  onLoad(opts) {
    const dev = app.globalData.device
    if (dev) {
      this.setData({
        maxWidth: dev.maxWidth || 0,
        imageHeight: dev.isDesktop ? 600 : dev.isTablet ? 540 : 500,
      })
    }
    if (opts.id) this.fetchDetail(opts.id)
  },

  calcTotal() {
    this.setData({ totalPrice: (this.data.currentPrice * this.data.quantity).toFixed(2) })
  },

  /** 图片加载失败 → 回退占位图 */
  onImageError() {
    this.setData({ 'product.image': '' })
  },

  fetchDetail(id) {
    api.get(`/products/${id}/`).then(data => {
      const specs = (data.specs || []).map(s => ({
        ...s,
        priceText: `¥${Number(s.price).toFixed(2)}`,
      }))
      this.setData({
        product: data,
        specs,
        currentPrice: Number(data.price),
        currentPriceText: Number(data.price).toFixed(2),
      }, () => this.calcTotal())
    })
      .catch(() => {})
  },

  onSpecTap(e) {
    const index = Number(e.currentTarget.dataset.index)
    const spec = this.data.specs[index]
    this.setData({
      selectedSpec: index,
      currentPrice: Number(spec.price),
      currentPriceText: Number(spec.price).toFixed(2),
    })
    this.calcTotal()
  },

  onQuantityMinus() {
    if (this.data.quantity <= 1) return
    this.setData({ quantity: this.data.quantity - 1 })
    this.calcTotal()
  },
  onQuantityPlus() {
    this.setData({ quantity: this.data.quantity + 1 })
    this.calcTotal()
  },

  addToCart() {
    const token = wx.getStorageSync('token') || app.globalData.token
    if (!token) {
      wx.showModal({
        title: '请先登录',
        content: '加入购物车需要登录',
        confirmText: '去登录',
        success: (res) => { if (res.confirm) wx.switchTab({ url: '/pages/user/user' }) },
      })
      return
    }
    const { product, specs, selectedSpec, quantity } = this.data
    if (!product || !product.id) {
      wx.showToast({ title: '商品信息加载中', icon: 'none' })
      return
    }
    const payload = { product: product.id, quantity }
    if (selectedSpec !== null && specs[selectedSpec]) {
      payload.spec = specs[selectedSpec].id
    }
    api.post('/cart/', payload).then(() => {
      wx.showToast({ title: '已加入购物车', icon: 'success' })
      this.setData({ quantity: 1 })
    })
      .catch(() => {})
  },
})
