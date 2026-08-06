import api from '../../utils/api'

Page({
  data: {
    addresses: [],
    loading: true,
    /** 编辑状态 */
    editing: false,
    editId: null,
    form: { name: '', phone: '', province: '', city: '', district: '', detail: '' },
  },

  onShow() {
    this.fetchList()
  },

  fetchList() {
    api.get('/addresses/').then(data => {
      this.setData({ addresses: data.results || data, loading: false })
    })
      .catch(() => this.setData({ loading: false }))
  },

  /** 打开新增表单 */
  onAdd() {
    this.setData({
      editing: true, editId: null,
      form: { name: '', phone: '', province: '江苏省', city: '苏州市', district: '工业园区', detail: '' },
    })
  },

  /** 打开编辑表单 */
  onEdit(e) {
    const addr = this.data.addresses.find(a => a.id === Number(e.currentTarget.dataset.id))
    if (!addr) return
    this.setData({
      editing: true, editId: addr.id,
      form: { name: addr.name, phone: addr.phone, province: addr.province, city: addr.city, district: addr.district, detail: addr.detail },
    })
  },

  /** 取消编辑 */
  onCancel() {
    this.setData({ editing: false, editId: null })
  },

  /** 输入绑定 */
  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  /** 保存 */
  onSave() {
    const { form, editId } = this.data
    const phoneReg = /^1[3-9]\d{9}$/
    if (!phoneReg.test(form.phone)) {
      wx.showToast({ title: '请输入正确的手机号码', icon: 'none' })
      return
    }
    if (!form.name || !form.phone || !form.province || !form.city || !form.district || !form.detail) {
      wx.showToast({ title: '请填写完整信息', icon: 'none' })
      return
    }
    if (editId) {
      api.post(`/addresses/${editId}/update/`, form).then(() => {
        wx.showToast({ title: '保存成功', icon: 'success' })
        this.onCancel()
        this.fetchList()
      })
        .catch(() => {})
    } else {
      api.post('/addresses/', form).then(() => {
        wx.showToast({ title: '添加成功', icon: 'success' })
        this.onCancel()
        this.fetchList()
      })
        .catch(() => {})
    }
  },

  /** 删除 */
  onDelete(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除', content: '确定要删除此地址吗？',
      success: (res) => {
        if (res.confirm) {
          api.post(`/addresses/${id}/remove/`)
            .then(() => { wx.showToast({ title: '已删除', icon: 'success' }) })
            .catch(() => {})
            .finally(() => this.fetchList())
        }
      },
    })
  },

  /** 设置默认 */
  onSetDefault(e) {
    const id = e.currentTarget.dataset.id
    api.post(`/addresses/${id}/set-default/`).then(() => {
      wx.showToast({ title: '已设为默认', icon: 'success' })
      this.fetchList()
    })
      .catch(() => {})
  },
})
