// index.js
// Import the helper instead of direct plugin
const siHelper = require('../../utils/si-helper');

// Check if plugin loaded
let pluginLoaded = false;
try {
  const plugin = siHelper.getPlugin();
  pluginLoaded = !!plugin;
  console.log('Plugin loading status:', pluginLoaded);
} catch (error) {
  console.error('Failed to load plugin:', error);
  pluginLoaded = false;
}

Page({
  data: {
    pluginLoaded: pluginLoaded
  },
  
  onLoad() {
    console.log('首页加载，插件加载状态:', this.data.pluginLoaded);
  },
  
  navigateToVoice() {
    wx.navigateTo({
      url: '/pages/voice/voice'
    })
  },
  navigateToImage() {
    wx.navigateTo({
      url: '/pages/image/image'
    })
  },
  navigateToChat() {
    wx.switchTab({
      url: '/pages/chat/chat'
    })
  },
  navigateToTranslate() {
    wx.navigateTo({
      url: '/pages/translate/translate'
    })
  },
  startChat() {
    wx.switchTab({
      url: '/pages/chat/chat'
    })
  },
  navigateToMusic() {
    wx.navigateTo({
      url: '/pages/music/music'
    })
  },
  // Test mock plugin
  testPlugin() {
    try {
      const plugin = siHelper.getPlugin();
      console.log('Using mock plugin via helper:', plugin);
      
      wx.showToast({
        title: 'Mock plugin test successful',
        icon: 'success'
      });
    } catch (error) {
      console.error('Mock plugin test failed:', error);
      
      wx.showModal({
        title: 'Plugin Test Failed',
        content: 'Could not load mock plugin: ' + (error.message || 'Unknown error'),
        showCancel: false
      });
    }
  }
})
