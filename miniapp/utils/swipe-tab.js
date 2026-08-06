/**
 * Tab 滑动切换工具
 * 在页面中引入后，左右滑动即可循环切换 tab
 *
 * 用法：
 *   const swipe = require('../../utils/swipe-tab').bind('/pages/cart/cart')
 *   Page({
 *     onSwipeStart: swipe.onSwipeStart,
 *     onSwipeEnd: swipe.onSwipeEnd,
 *     // ...
 *   })
 */
const TABS = [
  '/pages/index/index',
  '/pages/cart/cart',
  '/pages/order/order',
  '/pages/user/user',
]

module.exports = {
  bind(currentPath) {
    const idx = TABS.indexOf(currentPath)
    let startX = 0, startY = 0

    return {
      onSwipeStart(e) {
        startX = e.touches[0].clientX
        startY = e.touches[0].clientY
      },

      onSwipeEnd(e) {
        const dx = e.changedTouches[0].clientX - startX
        const dy = e.changedTouches[0].clientY - startY

        // 横向滑动不足 60px 或纵向为主 → 忽略
        if (Math.abs(dx) < 60 || Math.abs(dy) > Math.abs(dx)) return

        if (dx < 0) {
          // 左滑 → 下一个 tab
          wx.switchTab({ url: TABS[(idx + 1) % TABS.length] })
        } else {
          // 右滑 → 上一个 tab
          wx.switchTab({ url: TABS[(idx - 1 + TABS.length) % TABS.length] })
        }
      },
    }
  },
}
