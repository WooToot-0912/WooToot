/**
 * 统一的API客户端
 * 封装所有API请求逻辑，提供统一的错误处理和重试机制
 */

const config = require('../config');

class ApiClient {
  constructor() {
    this.baseUrl = config.apiBaseUrl;
    this.musicBaseUrl = config.musicApiBaseUrl;
    this.retryCount = config.requestConfig.retryCount || 2;
    this.retryDelay = config.requestConfig.retryDelay || 1000;
  }

  /**
   * 通用请求方法
   */
  async request(options) {
    const app = getApp();
    const token = wx.getStorageSync('token');
    
    const defaultOptions = {
      timeout: config.requestConfig.timeout || 60000,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header
      }
    };

    const finalOptions = { ...defaultOptions, ...options };
    
    return this._requestWithRetry(finalOptions, this.retryCount);
  }

  /**
   * 带重试的请求
   */
  async _requestWithRetry(options, retryCount) {
    try {
      return await this._makeRequest(options);
    } catch (error) {
      if (retryCount > 0 && this._shouldRetry(error)) {
        console.log(`请求失败，${this.retryDelay}ms后重试，剩余重试次数：${retryCount}`);
        await this._delay(this.retryDelay);
        return this._requestWithRetry(options, retryCount - 1);
      }
      throw error;
    }
  }

  /**
   * 执行实际请求
   */
  _makeRequest(options) {
    return new Promise((resolve, reject) => {
      wx.request({
        ...options,
        success: (res) => {
          if (res.statusCode === 401) {
            // token过期，跳转到登录页
            wx.removeStorageSync('token');
            wx.redirectTo({ url: '/pages/login/login' });
            reject(new Error('Token expired'));
          } else if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data);
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${res.data?.message || 'Request failed'}`));
          }
        },
        fail: reject
      });
    });
  }

  /**
   * 判断是否应该重试
   */
  _shouldRetry(error) {
    // 网络错误或超时错误可以重试
    return error.errMsg && (
      error.errMsg.includes('timeout') ||
      error.errMsg.includes('fail') ||
      error.errMsg.includes('network')
    );
  }

  /**
   * 延迟函数
   */
  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Ollama API调用
   */
  async callOllama(data) {
    return this.request({
      url: `${this.baseUrl}/api/generate`,
      method: 'POST',
      data
    });
  }

  /**
   * 音乐API调用
   */
  async searchMusic(keyword, platform = 'local') {
    return this.request({
      url: `${this.musicBaseUrl}/api/search?keyword=${encodeURIComponent(keyword)}&platform=${platform}`,
      method: 'GET'
    });
  }

  /**
   * 获取音乐服务状态
   */
  async getMusicStatus() {
    return this.request({
      url: `${this.musicBaseUrl}/api/status`,
      method: 'GET'
    });
  }
}

module.exports = new ApiClient();
