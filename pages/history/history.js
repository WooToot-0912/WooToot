// history.js
const historyManager = require('../../utils/history-manager');
const configManager = require('../../utils/config-manager');
const apiService = require('../../utils/api-service');

Page({
  data: {
    historyList: [],
    loading: true,
    activeTab: 'all', // 'all', 'chat', 'translate', 'image', 'voice'
    tabs: [
      { id: 'all', name: '全部', count: 0 },
      { id: 'chat', name: '对话', count: 0 },
      { id: 'translate', name: '翻译', count: 0 },
      { id: 'image', name: '图像', count: 0 },
      { id: 'voice', name: '语音', count: 0 }
    ],
    isEmpty: false,
    isGuestMode: false, // 是否是游客模式
    animation: {},
    lastRefreshTime: '刚刚更新',
    currentTabName: '全部', // 当前标签名称
    networkStatus: {
      type: 'unknown',
      available: true
    }
  },

  onLoad() {
    // 检查是否是游客模式
    const isGuestMode = wx.getStorageSync('isGuestMode') || false;
    this.setData({ isGuestMode });
    
    // 加载历史数据
    this.loadHistoryData();
    
    // 创建动画实例
    this.animation = wx.createAnimation({
      duration: 300,
      timingFunction: 'ease',
    });
    
    // 监听网络状态变化
    apiService.onNetworkStatusChange(this.handleNetworkStatusChange);
    
    // 获取当前网络状态
    const networkStatus = apiService.getNetworkStatus();
    this.setData({ networkStatus });
  },

  onShow() {
    // 每次显示页面时重新检查游客模式
    const isGuestMode = wx.getStorageSync('isGuestMode') || false;
    if (isGuestMode !== this.data.isGuestMode) {
      this.setData({ isGuestMode });
    }
    
    // 每次显示页面时重新加载数据
    this.loadHistoryData();
    
    // 更新最后刷新时间
    this.updateRefreshTime();
    
    // 更新网络状态
    const networkStatus = apiService.getNetworkStatus();
    this.setData({ networkStatus });
  },
  
  // 处理网络状态变化
  handleNetworkStatusChange(res) {
    this.setData({
      networkStatus: {
        type: res.networkType,
        available: res.isConnected
      }
    });
    
    // 网络恢复时自动刷新数据
    if (res.isConnected && !this.data.networkStatus.available) {
      this.loadHistoryData();
      wx.showToast({
        title: '网络已恢复',
        icon: 'success',
        duration: 1500
      });
    }
    
    // 网络断开时提示
    if (!res.isConnected && this.data.networkStatus.available) {
      wx.showToast({
        title: '网络已断开',
        icon: 'none',
        duration: 2000
      });
    }
  },

  onPullDownRefresh() {
    this.loadHistoryData();
    this.updateRefreshTime();
    wx.stopPullDownRefresh();
    
    // 显示刷新成功提示
    wx.showToast({
      title: '刷新成功',
      icon: 'success',
      duration: 1000
    });
  },
  
  // 更新最后刷新时间
  updateRefreshTime() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const formattedTime = `${hours < 10 ? '0' + hours : hours}:${minutes < 10 ? '0' + minutes : minutes}`;
    this.setData({
      lastRefreshTime: `${formattedTime} 更新`
    });
  },
  
  // 获取当前标签名称
  getTabName() {
    const { tabs, activeTab } = this.data;
    for (let i = 0; i < tabs.length; i++) {
      if (tabs[i].id === activeTab) {
        return tabs[i].name;
      }
    }
    return '全部';
  },

  loadHistoryData(tab = this.data.activeTab) {
    console.log('加载历史数据，标签:', tab);
    this.setData({ loading: true, isEmpty: false });
    
    // 使用历史记录管理器获取数据
    setTimeout(() => {
      // 创建测试数据（如果本地存储中没有数据）
      if (this.data.isGuestMode) {
        historyManager.createTestData();
      }
      
      // 获取历史记录数据
      const historyData = historyManager.getAllHistory(tab);
      
      // 处理历史记录数据，确保所有必要字段都有值
      const processedHistoryList = historyData.historyList.map(item => {
        // 设置类型文本
        if (!item.typeText) {
          item.typeText = this.getTypeText(item.type);
        }
        
        // 确保查询和结果不是undefined
        if (item.query === undefined) item.query = '';
        if (item.content === undefined) item.content = '';
        if (item.result === undefined) item.result = '';
        
        // 确保时间格式正确
        if (!item.time) {
          item.time = '未知时间';
        }
        
        // 小程序兼容的模型标签处理逻辑
        if (item.model) {
          try {
            // 使用正则表达式清理HTML标签
            let cleanModel = item.model.replace(/<[^>]*>/g, '');
            
            // 移除可能存在的特殊字符和属性
            cleanModel = cleanModel.replace(/&[^;]+;/g, '');
            cleanModel = cleanModel.replace(/\s+/g, ' ').trim();
            
            // 限制长度
            if (cleanModel.length > 20) {
              cleanModel = cleanModel.substring(0, 20) + '...';
            }
            
            // 如果清理后为空，使用默认值
            item.model = cleanModel || '未知模型';
          } catch (e) {
            console.error('处理模型标签出错:', e);
            item.model = '未知模型';
          }
        }
        
        return item;
      });
      
      // 使用动画效果更新列表
      this.setData({
        historyList: processedHistoryList,
        tabs: historyData.tabs,
        loading: false,
        isEmpty: processedHistoryList.length === 0,
        currentTabName: historyData.currentTabName
      });
    }, 300);
  },
  
  // 获取类型文本
  getTypeText(type) {
    switch(type) {
      case 'chat': return '对话';
      case 'translate': return '翻译';
      case 'image': return '图像';
      case 'voice': return '语音';
      default: return '未知';
    }
  },
  
  // 处理图片加载错误
  handleImageError(e) {
    const { index } = e.currentTarget.dataset;
    const historyList = this.data.historyList;
    
    // 替换为默认图片
    historyList[index].imagePath = '/images/default-avatar.png';
    
    this.setData({ historyList });
    
    console.error(`图片加载失败，索引: ${index}`);
    
    // 如果不是游客模式，尝试更新历史记录中的图片路径
    if (!this.data.isGuestMode) {
      const item = historyList[index];
      historyManager.updateHistory(item.type, item.id, {
        imagePath: '/images/default-avatar.png'
      });
    }
  },
  
  // 切换标签
  switchTab(e) {
    const { tab } = e.currentTarget.dataset;
    if (tab !== this.data.activeTab) {
      console.log('切换到标签:', tab);
      
      // 添加过渡动画
      this.setData({
        loading: true,
        activeTab: tab // 立即更新激活的标签
      });
      
      // 延迟加载数据，显示过渡效果
      setTimeout(() => {
        this.loadHistoryData(tab);
      }, 200);
    }
  },
  
  // 查看详细记录
  viewDetail(e) {
    const { index } = e.currentTarget.dataset;
    const item = this.data.historyList[index];
    
    // 如果是游客模式，提示不能查看详情
    if (this.data.isGuestMode && item.type !== 'image') {
      wx.showToast({
        title: '游客模式下无法查看详情',
        icon: 'none',
        duration: 2000
      });
      return;
    }
    
    switch (item.type) {
      case 'chat':
        wx.navigateTo({
          url: `/pages/chat/chat?history=${item.id}`
        });
        break;
      case 'translate':
        wx.navigateTo({
          url: `/pages/translate/translate?history=${item.id}`
        });
        break;
      case 'image':
        // 对于图像记录，直接显示图片和结果
        if (item.imagePath) {
          wx.previewImage({
            urls: [item.imagePath],
            current: item.imagePath,
            showmenu: true
          });
        } else {
          wx.showToast({
            title: '图片不存在',
            icon: 'none'
          });
        }
        break;
      case 'voice':
        wx.navigateTo({
          url: `/pages/voice/voice?history=${item.id}`
        });
        break;
    }
  },
  
  // 删除历史记录项
  deleteItem(e) {
    // 如果是游客模式，提示不能删除
    if (this.data.isGuestMode) {
      wx.showModal({
        title: '提示',
        content: '游客模式下不能删除历史记录',
        showCancel: false
      });
      return;
    }
    
    const { index } = e.currentTarget.dataset;
    const item = this.data.historyList[index];
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条历史记录吗？',
      success: (res) => {
        if (res.confirm) {
          // 使用历史记录管理器删除记录
          const success = historyManager.deleteHistory(item.type, item.id);
          
          if (success) {
            // 更新视图（带动画效果）
            const newList = [...this.data.historyList];
            newList.splice(index, 1);
            
            this.setData({
              historyList: newList,
              isEmpty: newList.length === 0
            });
            
            // 更新标签页计数
            this.updateTabCounts();
            
            wx.showToast({
              title: '已删除',
              icon: 'success'
            });
          } else {
            wx.showToast({
              title: '删除失败',
              icon: 'none'
            });
          }
        }
      }
    });
    
    // 阻止事件冒泡
    return false;
  },
  
  // 更新标签页计数
  updateTabCounts() {
    // 获取历史记录数据
    const historyData = historyManager.getAllHistory(this.data.activeTab);
    
    // 更新标签页计数
    this.setData({
      tabs: historyData.tabs
    });
  },
  
  // 清空所有历史记录
  clearAllHistory() {
    // 如果是游客模式，提示不能清空
    if (this.data.isGuestMode) {
      wx.showModal({
        title: '提示',
        content: '游客模式下不能清空历史记录',
        showCancel: false
      });
      return;
    }
    
    wx.showModal({
      title: '确认清空',
      content: '确定要清空' + (this.data.activeTab === 'all' ? '所有' : this.data.tabs.find(t => t.id === this.data.activeTab).name) + '历史记录吗？这将无法恢复！',
      success: (res) => {
        if (res.confirm) {
          // 使用历史记录管理器清空记录
          const success = historyManager.clearHistory(this.data.activeTab);
          
          if (success) {
            // 如果是游客模式，需要重新创建测试数据
            if (this.data.isGuestMode) {
              wx.removeStorageSync('hasCreatedTestData');
              historyManager.createTestData();
            }
            
            // 更新视图
            this.loadHistoryData();
            
            wx.showToast({
              title: '已清空',
              icon: 'success'
            });
          } else {
            wx.showToast({
              title: '清空失败',
              icon: 'none'
            });
          }
        }
      }
    });
  }
})