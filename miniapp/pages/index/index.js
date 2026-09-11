import api from '../../utils/api'
const app = getApp()
const swipe = require('../../utils/swipe-tab').bind('/pages/index/index')

/** 协议同意状态：存储 key 与版本号（文本更新时改变版本号会重新提示） */
const AGREEMENT_KEY = 'agreementAccepted'
const AGREEMENT_VERSION = '2026-09-11'

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
    /** 协议同意弹窗（微信审核要求 3.4：收集用户信息前需取得授权同意） */
    showAgreement: false,
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
    this.checkAgreement()
    this.fetchCategories()
    this.fetchProducts()
  },

  /** 首次进入需先同意《用户服务协议》与《隐私政策》 */
  checkAgreement() {
    if (wx.getStorageSync(AGREEMENT_KEY) === AGREEMENT_VERSION) return
    // 隐藏 tabBar，避免原生 tabBar 遮盖弹窗、或被绕过
    wx.hideTabBar({ animation: false, fail: () => {} })
    this.setData({ showAgreement: true })
  },

  onAgree() {
    wx.setStorageSync(AGREEMENT_KEY, AGREEMENT_VERSION)
    wx.showTabBar({ animation: false, fail: () => {} })
    this.setData({ showAgreement: false })
  },

  onDisagree() {
    wx.showModal({
      title: '提示',
      content: '需要同意《用户服务协议》和《隐私政策》后才能使用迈科咖啡小程序。',
      confirmText: '退出',
      cancelText: '再想想',
      success: (res) => {
        if (res.confirm) {
          wx.exitMiniProgram({ fail: () => {} })
        }
      },
    })
  },

  goUserAgreement() {
    wx.navigateTo({ url: '/pages/agreement/agreement?type=user' })
  },

  goPrivacyPolicy() {
    wx.navigateTo({ url: '/pages/agreement/agreement?type=privacy' })
  },

  noop() {},

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
    // 用 index 取值，避免鸿蒙上 dataset 数字类型兼容问题
    const index = e.currentTarget.dataset.index
    if (index === undefined) return
    const cat = this.data.categories[index]
    if (!cat) return
    const id = Number(cat.id) || 0
    console.log('[分类点击]', cat.name, 'id=', id)
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
