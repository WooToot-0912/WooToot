/**
 * UI辅助工具
 * 提供统一的UI交互、加载状态管理、用户体验优化
 */

class UIHelper {
  constructor() {
    this.loadingStates = new Map();
    this.toastQueue = [];
    this.isShowingToast = false;
  }

  /**
   * 显示加载状态
   */
  showLoading(title = '加载中...', key = 'default') {
    if (this.loadingStates.has(key)) {
      return; // 避免重复显示
    }

    this.loadingStates.set(key, true);
    
    wx.showLoading({
      title,
      mask: true
    });
  }

  /**
   * 隐藏加载状态
   */
  hideLoading(key = 'default') {
    if (!this.loadingStates.has(key)) {
      return;
    }

    this.loadingStates.delete(key);
    
    // 只有当所有加载状态都结束时才隐藏loading
    if (this.loadingStates.size === 0) {
      wx.hideLoading();
    }
  }

  /**
   * 显示成功提示
   */
  showSuccess(title, duration = 2000) {
    this.addToToastQueue({
      title,
      icon: 'success',
      duration
    });
  }

  /**
   * 显示错误提示
   */
  showError(title, duration = 3000) {
    this.addToToastQueue({
      title,
      icon: 'error',
      duration
    });
  }

  /**
   * 显示警告提示
   */
  showWarning(title, duration = 2500) {
    this.addToToastQueue({
      title,
      icon: 'none',
      duration
    });
  }

  /**
   * 显示信息提示
   */
  showInfo(title, duration = 2000) {
    this.addToToastQueue({
      title,
      icon: 'none',
      duration
    });
  }

  /**
   * 添加到Toast队列
   */
  addToToastQueue(options) {
    this.toastQueue.push(options);
    this.processToastQueue();
  }

  /**
   * 处理Toast队列
   */
  processToastQueue() {
    if (this.isShowingToast || this.toastQueue.length === 0) {
      return;
    }

    this.isShowingToast = true;
    const options = this.toastQueue.shift();

    wx.showToast({
      ...options,
      complete: () => {
        setTimeout(() => {
          this.isShowingToast = false;
          this.processToastQueue();
        }, options.duration || 2000);
      }
    });
  }

  /**
   * 显示确认对话框
   */
  showConfirm(options) {
    const defaultOptions = {
      title: '确认',
      content: '确定要执行此操作吗？',
      confirmText: '确定',
      cancelText: '取消',
      confirmColor: '#3A7FED'
    };

    return new Promise((resolve) => {
      wx.showModal({
        ...defaultOptions,
        ...options,
        success: (res) => {
          resolve(res.confirm);
        },
        fail: () => {
          resolve(false);
        }
      });
    });
  }

  /**
   * 显示操作菜单
   */
  showActionSheet(itemList, title = '') {
    return new Promise((resolve) => {
      wx.showActionSheet({
        itemList,
        title,
        success: (res) => {
          resolve(res.tapIndex);
        },
        fail: () => {
          resolve(-1);
        }
      });
    });
  }

  /**
   * 防抖函数
   */
  debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * 节流函数
   */
  throttle(func, limit = 300) {
    let inThrottle;
    return function executedFunction(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 格式化时间
   */
  formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    // 小于1分钟
    if (diff < 60000) {
      return '刚刚';
    }

    // 小于1小时
    if (diff < 3600000) {
      return Math.floor(diff / 60000) + '分钟前';
    }

    // 小于1天
    if (diff < 86400000) {
      return Math.floor(diff / 3600000) + '小时前';
    }

    // 小于7天
    if (diff < 604800000) {
      return Math.floor(diff / 86400000) + '天前';
    }

    // 超过7天显示具体日期
    return date.toLocaleDateString();
  }

  /**
   * 格式化音频时长
   */
  formatDuration(seconds) {
    if (!seconds || seconds < 0) return '00:00';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  /**
   * 复制到剪贴板
   */
  copyToClipboard(text) {
    return new Promise((resolve) => {
      wx.setClipboardData({
        data: text,
        success: () => {
          this.showSuccess('已复制到剪贴板');
          resolve(true);
        },
        fail: () => {
          this.showError('复制失败');
          resolve(false);
        }
      });
    });
  }

  /**
   * 震动反馈
   */
  vibrate(type = 'light') {
    try {
      if (type === 'heavy') {
        wx.vibrateShort({ type: 'heavy' });
      } else if (type === 'medium') {
        wx.vibrateShort({ type: 'medium' });
      } else {
        wx.vibrateShort({ type: 'light' });
      }
    } catch (error) {
      console.warn('震动反馈失败:', error);
    }
  }

  /**
   * 检查网络状态
   */
  checkNetworkStatus() {
    return new Promise((resolve) => {
      wx.getNetworkType({
        success: (res) => {
          const networkType = res.networkType;
          const isConnected = networkType !== 'none';
          const isWifi = networkType === 'wifi';
          
          resolve({
            isConnected,
            isWifi,
            networkType
          });
        },
        fail: () => {
          resolve({
            isConnected: false,
            isWifi: false,
            networkType: 'unknown'
          });
        }
      });
    });
  }

  /**
   * 预加载图片
   */
  preloadImage(src) {
    return new Promise((resolve) => {
      wx.getImageInfo({
        src,
        success: () => resolve(true),
        fail: () => resolve(false)
      });
    });
  }

  /**
   * 批量预加载图片
   */
  async preloadImages(srcList) {
    const results = await Promise.allSettled(
      srcList.map(src => this.preloadImage(src))
    );
    
    const successCount = results.filter(result => 
      result.status === 'fulfilled' && result.value
    ).length;
    
    return {
      total: srcList.length,
      success: successCount,
      failed: srcList.length - successCount
    };
  }

  /**
   * 获取系统信息
   */
  getSystemInfo() {
    try {
      return wx.getSystemInfoSync();
    } catch (error) {
      console.warn('获取系统信息失败:', error);
      return {};
    }
  }

  /**
   * 检查是否为iPhone X系列（有刘海屏）
   */
  isIPhoneX() {
    const systemInfo = this.getSystemInfo();
    const { model, screenHeight, screenWidth } = systemInfo;
    
    if (!model) return false;
    
    // iPhone X系列特征检测
    return model.includes('iPhone X') || 
           model.includes('iPhone 11') || 
           model.includes('iPhone 12') || 
           model.includes('iPhone 13') || 
           model.includes('iPhone 14') ||
           (screenHeight === 812 && screenWidth === 375) ||
           (screenHeight === 896 && screenWidth === 414);
  }
}

module.exports = new UIHelper();
