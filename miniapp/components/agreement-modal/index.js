/**
 * 协议同意弹窗（用户服务协议 / 隐私政策）
 * 用法：<agreement-modal show="{{show}}" bind:agree="onAgree" bind:disagree="onDisagree" />
 */
Component({
  properties: {
    show: {
      type: Boolean,
      value: false,
    },
  },

  methods: {
    noop() {},

    onAgree() {
      this.triggerEvent('agree')
    },

    onDisagree() {
      this.triggerEvent('disagree')
    },

    goUserAgreement() {
      wx.navigateTo({ url: '/pages/agreement/agreement?type=user' })
    },

    goPrivacyPolicy() {
      wx.navigateTo({ url: '/pages/agreement/agreement?type=privacy' })
    },
  },
})
