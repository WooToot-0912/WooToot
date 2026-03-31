/**
 * 统一错误处理器
 * 提供全局错误处理、日志记录和用户友好的错误提示
 */

class ErrorHandler {
  constructor() {
    this.errorLog = [];
    this.maxLogSize = 100; // 最大日志条目数
    this.reportUrl = null; // 错误上报地址
  }

  /**
   * 处理错误
   */
  handle(error, context = '', showToUser = true) {
    const errorInfo = this._parseError(error, context);
    
    // 记录日志
    this._log(errorInfo);
    
    // 上报错误（如果配置了上报地址）
    this._report(errorInfo);
    
    // 显示用户友好的错误提示
    if (showToUser) {
      this._showUserError(errorInfo);
    }
    
    return errorInfo;
  }

  /**
   * 解析错误信息
   */
  _parseError(error, context) {
    const timestamp = new Date().toISOString();
    let errorType = 'unknown';
    let message = '未知错误';
    let userMessage = '操作失败，请稍后重试';
    let stack = '';

    if (error instanceof Error) {
      errorType = error.name || 'Error';
      message = error.message;
      stack = error.stack || '';
    } else if (typeof error === 'string') {
      message = error;
      errorType = 'StringError';
    } else if (error && error.errMsg) {
      // 微信API错误
      errorType = 'WechatAPIError';
      message = error.errMsg;
      
      // 根据微信错误类型提供友好提示
      if (error.errMsg.includes('network')) {
        userMessage = '网络连接失败，请检查网络设置';
      } else if (error.errMsg.includes('timeout')) {
        userMessage = '请求超时，请稍后重试';
      } else if (error.errMsg.includes('permission')) {
        userMessage = '权限不足，请检查应用权限设置';
      }
    }

    // 根据上下文调整用户提示
    if (context.includes('ollama') || context.includes('ai')) {
      userMessage = 'AI服务暂时不可用，请稍后重试';
    } else if (context.includes('music')) {
      userMessage = '音乐服务连接失败，请检查网络';
    } else if (context.includes('image')) {
      userMessage = '图像处理失败，请重新选择图片';
    } else if (context.includes('voice')) {
      userMessage = '语音识别失败，请重新录音';
    }

    return {
      timestamp,
      errorType,
      message,
      userMessage,
      context,
      stack,
      level: this._getErrorLevel(errorType, message)
    };
  }

  /**
   * 获取错误级别
   */
  _getErrorLevel(errorType, message) {
    if (errorType === 'NetworkError' || message.includes('timeout')) {
      return 'warning';
    } else if (errorType === 'WechatAPIError') {
      return 'info';
    } else {
      return 'error';
    }
  }

  /**
   * 记录日志
   */
  _log(errorInfo) {
    // 添加到内存日志
    this.errorLog.unshift(errorInfo);
    
    // 限制日志大小
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize);
    }

    // 控制台输出
    const logMethod = errorInfo.level === 'error' ? 'error' : 
                     errorInfo.level === 'warning' ? 'warn' : 'info';
    
    console[logMethod](`[${errorInfo.timestamp}] ${errorInfo.context}: ${errorInfo.message}`);
    
    if (errorInfo.stack) {
      console.error('Stack trace:', errorInfo.stack);
    }

    // 保存到本地存储（仅保存重要错误）
    if (errorInfo.level === 'error') {
      try {
        const savedErrors = wx.getStorageSync('error_log') || [];
        savedErrors.unshift(errorInfo);
        
        // 只保存最近20条错误
        const trimmedErrors = savedErrors.slice(0, 20);
        wx.setStorageSync('error_log', trimmedErrors);
      } catch (e) {
        console.warn('保存错误日志失败:', e);
      }
    }
  }

  /**
   * 上报错误
   */
  _report(errorInfo) {
    if (!this.reportUrl || errorInfo.level === 'info') {
      return;
    }

    // 异步上报，不影响用户体验
    setTimeout(() => {
      wx.request({
        url: this.reportUrl,
        method: 'POST',
        data: {
          ...errorInfo,
          userAgent: wx.getSystemInfoSync(),
          appVersion: wx.getAccountInfoSync()?.miniProgram?.version || 'unknown'
        },
        fail: (err) => {
          console.warn('错误上报失败:', err);
        }
      });
    }, 100);
  }

  /**
   * 显示用户错误提示
   */
  _showUserError(errorInfo) {
    const { level, userMessage } = errorInfo;
    
    if (level === 'error') {
      wx.showModal({
        title: '操作失败',
        content: userMessage,
        showCancel: false,
        confirmText: '我知道了'
      });
    } else if (level === 'warning') {
      wx.showToast({
        title: userMessage,
        icon: 'none',
        duration: 3000
      });
    } else {
      wx.showToast({
        title: userMessage,
        icon: 'none',
        duration: 2000
      });
    }
  }

  /**
   * 获取错误日志
   */
  getErrorLog() {
    return this.errorLog;
  }

  /**
   * 清空错误日志
   */
  clearErrorLog() {
    this.errorLog = [];
    try {
      wx.removeStorageSync('error_log');
    } catch (e) {
      console.warn('清空错误日志失败:', e);
    }
  }

  /**
   * 设置错误上报地址
   */
  setReportUrl(url) {
    this.reportUrl = url;
  }

  /**
   * 包装异步函数，自动处理错误
   */
  wrapAsync(fn, context = '') {
    return async (...args) => {
      try {
        return await fn(...args);
      } catch (error) {
        this.handle(error, context);
        throw error;
      }
    };
  }

  /**
   * 包装同步函数，自动处理错误
   */
  wrapSync(fn, context = '') {
    return (...args) => {
      try {
        return fn(...args);
      } catch (error) {
        this.handle(error, context);
        throw error;
      }
    };
  }
}

module.exports = new ErrorHandler();
