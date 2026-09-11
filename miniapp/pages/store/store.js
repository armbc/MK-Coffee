Page({
  data: {
    latitude: 31.2990,       // 地图中心纬度
    longitude: 120.7290,     // 地图中心经度
    storeLat: 31.2990,       // 门店纬度
    storeLng: 120.7290,      // 门店经度
    markers: [{
      id: 1,
      latitude: 31.2990,
      longitude: 120.7290,
      title: '迈科咖啡',
      iconPath: '/images/marker.png',
      width: 36,
      height: 36,
      callout: {
        content: '苏州迈科咖啡有限公司',
        color: '#2c2416',
        fontSize: 14,
        borderRadius: 8,
        padding: 8,
        display: 'ALWAYS',
      },
    }],
    store: {
      name: '苏州迈科咖啡有限公司',
      address: '苏州市工业园区某某路100号',
      phone: '0512-88888888',
      hours: '周一至周六 8:00 - 18:00',
    },
  },

  // 说明：门店功能未上线（入口在 user 页已注释隐藏），此处不再调用 wx.getLocation。
  // 微信自 2022 年起对位置类接口实行申请制（需在 mp 后台「开发管理 → 接口设置」开通）；
  // 未开通却声明 requiredPrivateInfos 会导致提交审核被拦截。
  // 地图固定以门店坐标为中心；设立对外门店并开通位置接口后再恢复定位。

  /** 拨打电话 */
  onCall() {
    wx.makePhoneCall({ phoneNumber: this.data.store.phone.replace(/-/g, '') })
  },

  /** 打开导航 */
  onNavigate() {
    const { storeLat, storeLng, store } = this.data
    wx.openLocation({
      latitude: storeLat,
      longitude: storeLng,
      name: store.name,
      address: store.address,
      scale: 16,
    })
  },
})
