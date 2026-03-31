Page({
  data: {
    userInfo: null
  },

  onLoad() {
    this.loadUserInfo();
  },
  
  onShow() {
    // 每次页面显示时刷新用户信息
    this.loadUserInfo();
  },
  
  loadUserInfo() {
    // 获取用户信息
    const userInfo = wx.getStorageSync('userInfo');
    if (userInfo) {
      this.setData({ userInfo });
    } else {
      // 尝试从全局数据获取
      const app = getApp();
      if (app.globalData.userInfo) {
        this.setData({ userInfo: app.globalData.userInfo });
      } else {
        // 如果没有用户信息，可能需要重新登录
        const token = wx.getStorageSync('token');
        if (!token) {
          wx.redirectTo({
            url: '/pages/login/login'
          });
        }
      }
    }
  },

  navigateToHistory() {
    wx.navigateTo({
      url: '/pages/history/history'
    })
  },

  navigateToSettings() {
    wx.navigateTo({
      url: '/pages/settings/settings'
    })
  },

  navigateToAbout() {
    wx.navigateTo({
      url: '/pages/about/about'
    })
  },

  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          // 清除本地存储的用户信息和token
          wx.removeStorageSync('userInfo')
          wx.removeStorageSync('token')
          
          // 重置用户信息
          this.setData({
            userInfo: null
          })

          // 跳转到登录页
          wx.redirectTo({
            url: '/pages/login/login'
          })
        }
      }
    })
  }
}) 