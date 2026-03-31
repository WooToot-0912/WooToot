const app = getApp();

Page({
  data: {
    loading: false
  },

  onLoad() {
    console.log('登录页面加载');
    // 移除自动登录，让用户手动选择登录方式
  },

  // 微信一键登录
  handleLogin() {
    this.setData({ loading: true });
    
    // 获取用户信息
    wx.getUserProfile({
      desc: '用于完善用户资料',
      success: (res) => {
        console.log('获取用户信息成功:', res);
        const userInfo = res.userInfo;
        
        // 保存用户信息
        wx.setStorageSync('userInfo', userInfo);
        app.globalData.userInfo = userInfo;
        
        // 生成登录token (实际项目中应该通过服务器获取)
        const token = 'wx_token_' + Date.now();
        wx.setStorageSync('token', token);
        
        // 标记为非游客模式，允许保存使用记录
        wx.setStorageSync('isGuestMode', false);
        
        // 显示登录成功提示
        wx.showToast({
          title: '登录成功',
          icon: 'success',
          duration: 1500
        });
        
        // 延迟跳转到首页
        setTimeout(() => {
          this.navigateToIndex();
        }, 1500);
      },
      fail: (err) => {
        console.error('获取用户信息失败:', err);
        wx.showModal({
          title: '提示',
          content: '获取用户信息失败，无法完成登录',
          showCancel: false
        });
        this.setData({ loading: false });
      }
    });
  },

  // 游客登录
  handleGuestLogin() {
    this.setData({ loading: true });
    
    // 创建游客账号
    const guestUserInfo = {
      nickName: '游客用户',
      avatarUrl: '/images/default-avatar.png',
      gender: 0
    };
    
    // 保存游客信息
    wx.setStorageSync('userInfo', guestUserInfo);
    app.globalData.userInfo = guestUserInfo;
    
    // 生成游客token
    const guestToken = 'guest_token_' + Date.now();
    wx.setStorageSync('token', guestToken);
    
    // 标记为游客模式，只使用初始假数据
    wx.setStorageSync('isGuestMode', true);
    
    // 清空所有历史记录并重新创建测试数据
    this.resetHistoryData();
    
    // 显示登录成功提示
    wx.showToast({
      title: '游客登录成功',
      icon: 'success',
      duration: 1500
    });
    
    this.setData({ loading: false });
    
    // 延迟跳转到首页
    setTimeout(() => {
      this.navigateToIndex();
    }, 1000);
  },

  // 重置历史数据（只保留测试数据）
  resetHistoryData() {
    // 移除现有数据标记
    wx.removeStorageSync('hasCreatedTestData');
    
    // 清空所有历史记录
    wx.removeStorageSync('chatHistory');
    wx.removeStorageSync('translateHistory');
    wx.removeStorageSync('imageHistory');
    wx.removeStorageSync('voiceHistory');
    
    // 创建测试数据
    this.createTestData();
  },
  
  // 创建测试数据
  createTestData() {
    // 创建聊天历史测试数据
    const chatHistory = [
      {
        id: 'chat1',
        query: '今天天气怎么样？',
        result: '今天天气晴朗，温度适宜，非常适合户外活动。',
        timestamp: Date.now() - 3600000,
        content: '今天天气怎么样？'
      },
      {
        id: 'chat2',
        query: '推荐一本好书',
        result: '我推荐《三体》，这是一部非常优秀的科幻小说，讲述了地球文明与三体文明的接触。',
        timestamp: Date.now() - 7200000,
        content: '推荐一本好书'
      }
    ];
    
    // 创建翻译历史测试数据
    const translateHistory = [
      {
        id: 'translate1',
        query: 'Hello world',
        result: '你好，世界',
        timestamp: Date.now() - 10800000,
        content: 'Hello world'
      }
    ];
    
    // 创建图像历史测试数据
    const imageHistory = [
      {
        id: 'image1',
        query: '识别图片内容',
        result: '图片中包含一只猫和一只狗',
        timestamp: Date.now() - 14400000,
        content: '识别图片内容',
        imagePath: '/images/default-cover.jpg'
      }
    ];
    
    // 创建语音历史测试数据
    const voiceHistory = [
      {
        id: 'voice1',
        text: '这是通过语音识别转换的文字内容',
        time: '12:30',
        timestamp: Date.now() - 18000000
      }
    ];
    
    // 保存到本地存储
    wx.setStorageSync('chatHistory', chatHistory);
    wx.setStorageSync('translateHistory', translateHistory);
    wx.setStorageSync('imageHistory', imageHistory);
    wx.setStorageSync('voiceHistory', voiceHistory);
    wx.setStorageSync('hasCreatedTestData', true);
  },

  // 隐私政策
  showPrivacyPolicy() {
    wx.showModal({
      title: '用户协议和隐私政策',
      content: '本应用尊重并保护所有使用服务用户的个人隐私权。为了给您提供更准确、更有个性化的服务，本应用会按照本隐私权政策的规定使用和披露您的个人信息。\n\n微信一键登录将记录您的使用历史数据，游客模式则仅使用示例数据，不会保存您的使用记录。',
      confirmText: '我同意',
      cancelText: '不同意'
    });
  },

  // 跳转到首页
  navigateToIndex() {
    console.log('正在跳转到首页...');
    wx.switchTab({
      url: '/pages/index/index',
      success: () => {
        console.log('跳转到首页成功');
      },
      fail: (error) => {
        console.error('跳转到首页失败:', error);
        // 显示错误信息
        wx.showModal({
          title: '跳转失败',
          content: '无法跳转到首页: ' + (error.errMsg || '未知错误'),
          showCancel: false
        });
      }
    });
  }
}); 