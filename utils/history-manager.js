/**
 * 历史记录管理器
 * 统一管理聊天、翻译、图像和语音历史记录
 */

const configManager = require('./config-manager');

// 历史记录类型
const HISTORY_TYPES = {
  CHAT: 'chat',
  TRANSLATE: 'translate',
  IMAGE: 'image',
  VOICE: 'voice'
};

// 获取历史记录存储键
const getStorageKey = (type) => `${type}History`;

// 生成唯一ID
const generateId = (type) => {
  return `${type}_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
};

// 格式化时间
const formatTime = (date) => {
  const now = new Date();
  const diff = now - date;
  
  // 今天内的显示时间
  if (diff < 24 * 60 * 60 * 1000 && 
      date.getDate() === now.getDate()) {
    const hours = date.getHours();
    const minutes = date.getMinutes();
    return `${hours < 10 ? '0' + hours : hours}:${minutes < 10 ? '0' + minutes : minutes}`;
  }
  
  // 昨天的显示"昨天"
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (date.getDate() === yesterday.getDate() &&
      date.getMonth() === yesterday.getMonth() &&
      date.getFullYear() === yesterday.getFullYear()) {
    return '昨天';
  }
  
  // 一周内的显示星期几
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
    return weekdays[date.getDay()];
  }
  
  // 其他显示日期
  return `${date.getMonth() + 1}月${date.getDate()}日`;
};

// 历史记录管理器
const historyManager = {
  /**
   * 获取指定类型的历史记录
   * @param {string} type 历史记录类型
   * @returns {Array} 历史记录数组
   */
  getHistory(type) {
    const key = getStorageKey(type);
    try {
      return wx.getStorageSync(key) || [];
    } catch (error) {
      console.error(`获取${type}历史记录失败:`, error);
      return [];
    }
  },
  
  /**
   * 获取所有历史记录
   * @param {string} [activeTab='all'] 当前激活的标签
   * @returns {Object} 包含历史记录和标签计数的对象
   */
  getAllHistory(activeTab = 'all') {
    // 获取所有历史记录
    const chatHistory = this.getHistory(HISTORY_TYPES.CHAT);
    const translateHistory = this.getHistory(HISTORY_TYPES.TRANSLATE);
    const imageHistory = this.getHistory(HISTORY_TYPES.IMAGE);
    const voiceHistory = this.getHistory(HISTORY_TYPES.VOICE);
    
    // 更新标签页数量
    const tabs = [
      { id: 'all', name: '全部', count: chatHistory.length + translateHistory.length + imageHistory.length + voiceHistory.length },
      { id: 'chat', name: '对话', count: chatHistory.length },
      { id: 'translate', name: '翻译', count: translateHistory.length },
      { id: 'image', name: '图像', count: imageHistory.length },
      { id: 'voice', name: '语音', count: voiceHistory.length }
    ];
    
    // 获取当前标签名称
    let currentTabName = '全部';
    for (let i = 0; i < tabs.length; i++) {
      if (tabs[i].id === activeTab) {
        currentTabName = tabs[i].name;
        break;
      }
    }
    
    // 合并所有历史记录，并添加类型标识
    let allHistory = [];
    
    if (activeTab === 'all' || activeTab === 'chat') {
      allHistory = [...allHistory, ...chatHistory.map(item => ({ 
        ...item, 
        type: 'chat', 
        typeText: '对话',
        time: formatTime(new Date(item.timestamp || Date.now()))
      }))];
    }
    
    if (activeTab === 'all' || activeTab === 'translate') {
      allHistory = [...allHistory, ...translateHistory.map(item => ({ 
        ...item, 
        type: 'translate', 
        typeText: '翻译',
        time: formatTime(new Date(item.timestamp || Date.now()))
      }))];
    }
    
    if (activeTab === 'all' || activeTab === 'image') {
      allHistory = [...allHistory, ...imageHistory.map(item => ({ 
        ...item, 
        type: 'image', 
        typeText: '图像',
        time: formatTime(new Date(item.timestamp || Date.now()))
      }))];
    }
    
    if (activeTab === 'all' || activeTab === 'voice') {
      allHistory = [...allHistory, ...voiceHistory.map(item => ({ 
        ...item, 
        type: 'voice', 
        typeText: '语音',
        time: formatTime(new Date(item.timestamp || Date.now()))
      }))];
    }
    
    // 按时间排序（从新到旧）
    allHistory.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
    
    return {
      historyList: allHistory,
      tabs,
      currentTabName,
      isEmpty: allHistory.length === 0
    };
  },
  
  /**
   * 添加历史记录
   * @param {string} type 历史记录类型
   * @param {Object} item 历史记录项
   * @returns {string} 新记录的ID
   */
  addHistory(type, item) {
    // 检查是否可以保存历史记录
    if (!this.canSaveHistory()) {
      console.log('游客模式，不保存历史记录');
      return null;
    }
    
    try {
      // 获取现有历史记录
      const history = this.getHistory(type);
      
      // 生成ID和时间戳
      const id = item.id || generateId(type);
      const timestamp = item.timestamp || Date.now();
      
      // 新记录
      const newItem = {
        ...item,
        id,
        timestamp
      };
      
      // 添加到历史记录
      const newHistory = [newItem, ...history];
      
      // 限制历史记录数量
      const config = configManager.getConfig();
      const historyConfig = config.historyConfig || {};
      const maxItems = historyConfig[`max${type.charAt(0).toUpperCase() + type.slice(1)}History`] || 20;
      
      if (newHistory.length > maxItems) {
        newHistory.splice(maxItems);
      }
      
      // 保存到存储
      wx.setStorageSync(getStorageKey(type), newHistory);
      
      return id;
    } catch (error) {
      console.error(`添加${type}历史记录失败:`, error);
      return null;
    }
  },
  
  /**
   * 更新历史记录
   * @param {string} type 历史记录类型
   * @param {string} id 记录ID
   * @param {Object} updates 更新内容
   * @returns {boolean} 是否更新成功
   */
  updateHistory(type, id, updates) {
    try {
      // 获取现有历史记录
      const history = this.getHistory(type);
      
      // 查找记录
      const index = history.findIndex(item => item.id === id);
      if (index === -1) {
        console.warn(`未找到${type}历史记录:`, id);
        return false;
      }
      
      // 更新记录
      history[index] = {
        ...history[index],
        ...updates,
        id // 确保ID不变
      };
      
      // 保存到存储
      wx.setStorageSync(getStorageKey(type), history);
      
      return true;
    } catch (error) {
      console.error(`更新${type}历史记录失败:`, error);
      return false;
    }
  },
  
  /**
   * 删除历史记录
   * @param {string} type 历史记录类型
   * @param {string} id 记录ID
   * @returns {boolean} 是否删除成功
   */
  deleteHistory(type, id) {
    try {
      // 获取现有历史记录
      const history = this.getHistory(type);
      
      // 过滤掉要删除的记录
      const newHistory = history.filter(item => item.id !== id);
      
      // 如果长度相同，说明没有找到记录
      if (newHistory.length === history.length) {
        console.warn(`未找到${type}历史记录:`, id);
        return false;
      }
      
      // 保存到存储
      wx.setStorageSync(getStorageKey(type), newHistory);
      
      return true;
    } catch (error) {
      console.error(`删除${type}历史记录失败:`, error);
      return false;
    }
  },
  
  /**
   * 清空指定类型的历史记录
   * @param {string} type 历史记录类型，如果为'all'则清空所有类型
   * @returns {boolean} 是否清空成功
   */
  clearHistory(type) {
    try {
      if (type === 'all') {
        // 清空所有类型的历史记录
        wx.removeStorageSync(getStorageKey(HISTORY_TYPES.CHAT));
        wx.removeStorageSync(getStorageKey(HISTORY_TYPES.TRANSLATE));
        wx.removeStorageSync(getStorageKey(HISTORY_TYPES.IMAGE));
        wx.removeStorageSync(getStorageKey(HISTORY_TYPES.VOICE));
      } else {
        // 清空指定类型的历史记录
        wx.removeStorageSync(getStorageKey(type));
      }
      
      return true;
    } catch (error) {
      console.error(`清空${type}历史记录失败:`, error);
      return false;
    }
  },
  
  /**
   * 根据ID获取历史记录项
   * @param {string} type 历史记录类型
   * @param {string} id 记录ID
   * @returns {Object|null} 历史记录项或null
   */
  getHistoryById(type, id) {
    try {
      const history = this.getHistory(type);
      return history.find(item => item.id === id) || null;
    } catch (error) {
      console.error(`获取${type}历史记录项失败:`, error);
      return null;
    }
  },
  
  /**
   * 创建测试数据（仅用于演示）
   */
  createTestData() {
    // 检查是否已创建测试数据
    const hasCreatedTestData = wx.getStorageSync('hasCreatedTestData');
    if (hasCreatedTestData) return;
    
    try {
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
          imagePath: '/images/default-avatar.png'
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
      wx.setStorageSync(getStorageKey(HISTORY_TYPES.CHAT), chatHistory);
      wx.setStorageSync(getStorageKey(HISTORY_TYPES.TRANSLATE), translateHistory);
      wx.setStorageSync(getStorageKey(HISTORY_TYPES.IMAGE), imageHistory);
      wx.setStorageSync(getStorageKey(HISTORY_TYPES.VOICE), voiceHistory);
      wx.setStorageSync('hasCreatedTestData', true);
      
      console.log('已创建测试数据');
    } catch (error) {
      console.error('创建测试数据失败:', error);
    }
  },
  
  /**
   * 检查是否可以保存历史记录（非游客模式）
   * @returns {boolean} 是否可以保存
   */
  canSaveHistory() {
    const isGuestMode = wx.getStorageSync('isGuestMode') || false;
    return !isGuestMode;
  },
  
  // 导出历史记录类型常量
  HISTORY_TYPES
};

module.exports = historyManager; 