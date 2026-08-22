import api from '../../utils/api'
const app = getApp()
const swipe = require('../../utils/swipe-tab').bind('/pages/index/index')

Page({
  onSwipeStart: swipe.onSwipeStart,
  onSwipeEnd: swipe.onSwipeEnd,
  data: {
    banners: [
      { id: 1, image: '/images/banner-placeholder.png', title: '迈科臻选 · 手工烘焙咖啡豆' },
      { id: 2, image: '/images/banner-placeholder.png', title: '新用户首单享 9 折优惠' },
    ],
    categories: [],
    products: [],
    activeCategory: 0,
    loading: true,
    /** 响应式 */
    gridCols: 2,
    maxWidth: 0,
    cardGap: 20,
  },

  onLoad() {
    const dev = app.globalData.device
    if (dev) {
      const cols = dev.gridCols || 2
      this.setData({
        gridCols: cols,
        maxWidth: dev.maxWidth || 0,
        cardGap: cols >= 4 ? 24 : 20,
      })
    }
    this.fetchCategories()
    this.fetchProducts()
  },

  fetchCategories() {
    api.get('/categories/').then(data => {
      const cats = data.results || data
      this.setData({ categories: [{ id: 0, name: '全部' }, ...cats] })
    })
      .catch(() => {})
  },

  fetchProducts(categoryId) {
    const params = categoryId ? { category: categoryId } : {}
    api.get('/products/', params).then(data => {
      const list = data.results || data
      this.setData({ products: list, loading: false })
    })
      .catch(() => this.setData({ loading: false }))
  },

  onCategoryTap(e) {
    const id = Number(e.currentTarget.dataset.id)
    this.setData({ activeCategory: id })
    this.fetchProducts(id || null)
  },

  onProductTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/product/product?id=${id}` })
  },

  /** 图片加载失败 → 该商品回退占位图 */
  onImageError(e) {
    const idx = e.currentTarget.dataset.index
    if (idx === undefined) return
    this.setData({ [`products[${idx}].image`]: '' })
  },
})
