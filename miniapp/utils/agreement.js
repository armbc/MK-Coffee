/**
 * 协议同意状态（《用户服务协议》《隐私政策》）
 *
 * 微信《小程序平台运营规范常见拒绝情形 3.4》要求：收集、使用和存储用户信息前，
 * 须在小程序内提供协议并取得用户授权同意。
 *
 * 本项目的信息收集入口只有「登录」（wx.login → openid，其余信息均在登录后由用户主动填写），
 * 因此同意校验挂在登录流程前；首页底部同时提供可随时查阅的协议入口与同意按钮。
 */
const KEY = 'agreementAccepted'

/** 协议版本：协议文本有更新时改变此值，用户会被重新提示 */
const VERSION = '2026-09-11'

/** 是否已同意 */
function isAccepted() {
  return wx.getStorageSync(KEY) === VERSION
}

/** 记录同意 */
function accept() {
  wx.setStorageSync(KEY, VERSION)
}

module.exports = {
  KEY,
  VERSION,
  isAccepted,
  accept,
}
