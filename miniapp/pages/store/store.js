Page({
  data: {
    latitude: 31.2990,       // 苏州工业园区坐标
    longitude: 120.7290,
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

  onLoad() {
    // 获取当前位置
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          latitude: res.latitude,
          longitude: res.longitude,
          'markers[0].latitude': res.latitude,
          'markers[0].longitude': res.longitude,
        })
      },
    })
  },

  /** 拨打电话 */
  onCall() {
    wx.makePhoneCall({ phoneNumber: this.data.store.phone.replace(/-/g, '') })
  },

  /** 打开导航 */
  onNavigate() {
    const { latitude, longitude, store } = this.data
    wx.openLocation({
      latitude, longitude,
      name: store.name,
      address: store.address,
      scale: 16,
    })
  },
})
