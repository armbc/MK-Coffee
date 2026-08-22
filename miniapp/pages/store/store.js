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

  onLoad() {
    // 获取当前位置作为地图中心，但 marker 与导航始终使用门店坐标
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          latitude: res.latitude,
          longitude: res.longitude,
        })
      },
      fail: (err) => {
        console.warn('获取当前位置失败', err)
      },
    })
  },

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
