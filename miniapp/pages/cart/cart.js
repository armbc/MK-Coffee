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
    coupons: [],
    selectedCoupon: null,
    couponDiscount: '0.00',
    payable: '0.00',
  },

  onShow() {
    const dev = app.globalData.device
    if (dev) this.setData({ maxWidth: dev.maxWidth || 0 })
    this.fetchCart()
    this.fetchCoupons()
  },

  /** 拉取当前用户可用优惠券（未使用且未过期） */
  fetchCoupons() {
    api.get('/my-coupons/').then(data => {
      const list = data.results || data
      const now = Date.now()
      const usable = (list || []).filter(c =>
        c.status === 'unused' && new Date(c.end_date).getTime() > now)
      this.setData({ coupons: usable })
    }).catch(() => {})
  },

  /** 选择优惠券 */
  onCouponTap() {
    const coupons = this.data.coupons
    if (!coupons.length) {
      wx.showToast({ title: '暂无可用优惠券', icon: 'none' })
      return
    }
    const itemList = ['不使用优惠券', ...coupons.map(c =>
      `${c.coupon_value_text}（满${Number(c.coupon_min_amount).toFixed(0)}可用）`)]
    wx.showActionSheet({
      itemList,
      success: (res) => {
        if (res.tapIndex === 0) {
          this._setCoupon(null)
          return
        }
        const coupon = coupons[res.tapIndex - 1]
        const total = Number(this.data.total)
        if (total < Number(coupon.coupon_min_amount)) {
          wx.showToast({ title: `未达门槛（满${coupon.coupon_min_amount}可用）`, icon: 'none' })
          return
        }
        this._setCoupon(coupon)
      },
    })
  },

  _setCoupon(coupon) {
    this.setData({ selectedCoupon: coupon }, () => this._recalc())
  },

  fetchCart() {
    const token = wx.getStorageSync('token') || app.globalData.token
    if (!token) {
      this.setData({ items: [], loading: false })
      return
    }
    api.get('/cart/').then(data => {
      const oldItems = this.data.items
      const firstLoad = oldItems.length === 0
      const items = (data.results || data).map(item => ({
        ...item,
        unit_price_text: Number(item.unit_price).toFixed(2),
        subtotal_text: Number(item.subtotal).toFixed(2),
        // 首次进入默认全选（避免“有商品但应付 0.00”的困惑）；之后记忆勾选状态
        isSelected: firstLoad ? true : this._wasSelected(oldItems, item.id),
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
    // 勾选变化后必须重算 payable（应付=原价-优惠），否则底部金额不刷新
    this.setData(upd, () => this._recalc())
  },

  onToggleAll() {
    const items = this.data.items
    const wasAll = items.length > 0 && items.every(i => i.isSelected)
    const newVal = !wasAll
    const upd = {}
    for (let j = 0; j < items.length; j++) upd[`items[${j}].isSelected`] = newVal
    upd.allSelected = newVal && items.length > 0
    upd.total = newVal ? items.reduce((s, i) => s + Number(i.subtotal), 0).toFixed(2) : '0.00'
    // 全选/取消全选后同步重算应付金额
    this.setData(upd, () => this._recalc())
  },

  _recalc() {
    const items = this.data.items
    let sum = 0, all = items.length > 0
    for (const i of items) { if (i.isSelected) sum += Number(i.subtotal); else all = false }
    const total = sum.toFixed(2)

    // 优惠券抵扣：金额变化后若不再满足门槛，自动取消已选券
    let coupon = this.data.selectedCoupon
    let discount = 0
    if (coupon) {
      if (Number(total) >= Number(coupon.coupon_min_amount)) {
        if (coupon.coupon_type === 'full_reduce') {
          discount = Math.min(Number(coupon.coupon_value), Number(total))
        } else if (coupon.coupon_type === 'discount') {
          discount = Number(total) - Number((Number(total) * Number(coupon.coupon_value) / 10).toFixed(2))
        }
      } else {
        coupon = null
      }
    }
    const payable = (Number(total) - discount).toFixed(2)
    this.setData({
      total,
      allSelected: all,
      selectedCoupon: coupon,
      couponDiscount: discount.toFixed(2),
      payable,
    })
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
    // 先获取默认收货地址
    api.get('/addresses/').then(data => {
      const list = data.results || data
      const addr = list.find(a => a.is_default) || list[0]
      if (!addr) {
        wx.showModal({
          title: '需要收货地址',
          content: '下单需要收货地址，请先添加',
          confirmText: '去添加',
          cancelText: '暂不',
          success: (res) => {
            if (res.confirm) wx.navigateTo({ url: '/pages/addresses/addresses' })
          },
        })
        return
      }
      const addrText = `${addr.province}${addr.city}${addr.district}${addr.detail}`
      const coupon = this.data.selectedCoupon
      const discountText = coupon ? `\n优惠券：-¥${this.data.couponDiscount}（${coupon.coupon_value_text}）` : ''
      wx.showModal({
        title: '确认下单',
        content: `收货人：${addr.name} ${addr.phone}\n${addrText}${discountText}\n\n应付 ¥${this.data.payable}，确认提交订单？`,
        success: (res) => {
          if (res.confirm) {
            api.post('/orders/', {
              item_ids: selected.map(i => i.id),
              address_id: addr.id,
              coupon_id: coupon ? coupon.id : null,
            }).then(data => {
              wx.showToast({ title: '下单成功', icon: 'success' })
              // 下单即清购物车（后端已删除）：立即清空本地显示，
              // 用户切回购物车 tab 时不再看到旧数据（无需等待重新拉取）
              this.setData({
                items: [],
                total: '0.00',
                allSelected: false,
                selectedCoupon: null,
                couponDiscount: '0.00',
                payable: '0.00',
                coupons: [],
              })
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
    }).catch(() => {
      wx.showToast({ title: '获取地址失败', icon: 'none' })
    })
  },
})
