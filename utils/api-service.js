/**
 * API服务
 * 统一处理网络请求、错误处理和重试逻辑
 */

const configManager = require('./config-manager');

// 网络状态监听器
let networkType = 'unknown';
let networkAvailable = true;
let networkListener = null;

// 初始化网络监听
const initNetworkListener = () => {
  // 获取当前网络状态
  wx.getNetworkType({
    success: (res) => {
      networkType = res.networkType;
      networkAvailable = res.networkType !== 'none';
    }
  });
  
  // 监听网络状态变化
  if (!networkListener) {
    networkListener = wx.onNetworkStatusChange((res) => {
      networkType = res.networkType;
      networkAvailable = res.isConnected;
      
      // 网络恢复时尝试重新连接服务
      if (networkAvailable && pendingRequests.length > 0) {
        processPendingRequests();
      }
      
      // 网络状态变化时触发事件
      if (typeof onNetworkStatusChange === 'function') {
        onNetworkStatusChange(res);
      }
    });
  }
};

// 网络状态变化回调
let onNetworkStatusChange = null;

// 待处理的请求队列
const pendingRequests = [];

// 处理待处理的请求
const processPendingRequests = () => {
  if (!networkAvailable || pendingRequests.length === 0) return;
  
  // 复制队列并清空原队列
  const requests = [...pendingRequests];
  pendingRequests.length = 0;
  
  // 处理每个请求
  requests.forEach(({ options, resolve, reject }) => {
    request(options).then(resolve).catch(reject);
  });
};

// 基本请求函数
const request = (options) => {
  // 获取配置
  const config = configManager.getConfig();
  const requestConfig = config.requestConfig || {};
  
  // 设置默认值
  options = {
    timeout: requestConfig.timeout || 60000,
    retryCount: requestConfig.retryCount || 2,
    retryDelay: requestConfig.retryDelay || 1000,
    showError: true,
    ...options
  };
  
  // 检查网络状态
  if (!networkAvailable) {
    // 如果启用了离线模式，检查请求的功能是否支持离线
    const offlineConfig = config.offlineMode || {};
    if (offlineConfig.enabled && canHandleOffline(options)) {
      return handleOfflineRequest(options);
    }
    
    // 否则将请求添加到待处理队列
    return new Promise((resolve, reject) => {
      pendingRequests.push({ options, resolve, reject });
      
      if (options.showError) {
        wx.showToast({
          title: '网络不可用，请求已加入队列',
          icon: 'none',
          duration: 2000
        });
      }
    });
  }
  
  // 执行请求
  return executeRequest(options);
};

// 执行请求（包含重试逻辑）
const executeRequest = (options, currentRetry = 0) => {
  // 获取完整URL
  const baseUrl = options.baseUrl || configManager.get('apiBaseUrl');
  const url = options.url.startsWith('http') 
    ? options.url 
    : configManager.joinUrl(baseUrl, options.url);
  
  // 获取token
  const token = wx.getStorageSync('token') || '';
  
  return new Promise((resolve, reject) => {
    // 请求开始时间
    const startTime = Date.now();
    
    // 显示加载提示
    if (options.showLoading) {
      wx.showLoading({
        title: options.loadingText || '加载中...',
        mask: options.loadingMask || false
      });
    }
    
    wx.request({
      url,
      data: options.data,
      method: options.method || 'GET',
      header: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': options.contentType || 'application/json',
        ...options.header
      },
      timeout: options.timeout,
      success: (res) => {
        // 请求完成时间
        const endTime = Date.now();
        const duration = endTime - startTime;
        
        // 记录请求日志
        if (configManager.get('debug')) {
          console.log(`[API] ${options.method || 'GET'} ${url} - ${res.statusCode} (${duration}ms)`, 
            { request: options.data, response: res.data });
        }
        
        // 处理HTTP状态码
        if (res.statusCode >= 200 && res.statusCode < 300) {
          // 成功响应
          resolve(res.data);
        } else if (res.statusCode === 401) {
          // 未授权，可能需要重新登录
          handleUnauthorized(options, reject);
        } else if (res.statusCode === 429 || res.statusCode === 503) {
          // 限流或服务不可用，尝试重试
          handleRetry(options, currentRetry, resolve, reject);
        } else {
          // 其他错误
          handleError(res, options, reject);
        }
      },
      fail: (error) => {
        // 请求失败
        console.error(`[API] Request failed: ${url}`, error);
        
        // 检查是否需要重试
        if (currentRetry < options.retryCount) {
          handleRetry(options, currentRetry, resolve, reject);
        } else {
          // 超过重试次数，处理错误
          handleRequestFail(error, options, reject);
        }
      },
      complete: () => {
        // 隐藏加载提示
        if (options.showLoading) {
          wx.hideLoading();
        }
      }
    });
  });
};

// 处理未授权错误
const handleUnauthorized = (options, reject) => {
  // 清除token
  wx.removeStorageSync('token');
  
  // 显示错误提示
  if (options.showError) {
    wx.showModal({
      title: '登录已过期',
      content: '您的登录状态已过期，请重新登录',
      showCancel: false,
      success: () => {
        // 跳转到登录页
        wx.redirectTo({
          url: '/pages/login/login'
        });
      }
    });
  }
  
  reject({ errCode: 401, errMsg: '未授权，请重新登录' });
};

// 处理请求错误
const handleError = (res, options, reject) => {
  let errMsg = `请求失败 (${res.statusCode})`;
  
  // 尝试从响应中获取错误信息
  if (res.data) {
    if (typeof res.data === 'string') {
      errMsg = res.data;
    } else if (res.data.error || res.data.message || res.data.msg) {
      errMsg = res.data.error || res.data.message || res.data.msg;
    }
  }
  
  // 显示错误提示
  if (options.showError) {
    wx.showToast({
      title: errMsg,
      icon: 'none',
      duration: 2000
    });
  }
  
  reject({ errCode: res.statusCode, errMsg, data: res.data });
};

// 处理请求失败
const handleRequestFail = (error, options, reject) => {
  let errMsg = '请求失败';
  let errCode = 'UNKNOWN';
  
  if (error.errMsg) {
    if (error.errMsg.includes('timeout')) {
      errMsg = '请求超时，请检查网络';
      errCode = 'TIMEOUT';
    } else if (error.errMsg.includes('fail')) {
      errMsg = '网络连接失败';
      errCode = 'NETWORK_ERROR';
    }
  }
  
  // 显示错误提示
  if (options.showError) {
    wx.showToast({
      title: errMsg,
      icon: 'none',
      duration: 2000
    });
  }
  
  reject({ errCode, errMsg, error });
};

// 处理重试逻辑
const handleRetry = (options, currentRetry, resolve, reject) => {
  const retryCount = currentRetry + 1;
  const retryDelay = options.retryDelay || 1000;
  
  console.log(`[API] Retrying request (${retryCount}/${options.retryCount})...`);
  
  // 显示重试提示
  if (options.showError) {
    wx.showToast({
      title: `请求失败，正在重试 (${retryCount}/${options.retryCount})`,
      icon: 'none',
      duration: retryDelay
    });
  }
  
  // 延迟后重试
  setTimeout(() => {
    executeRequest(options, retryCount).then(resolve).catch(reject);
  }, retryDelay);
};

// 检查是否可以离线处理请求
const canHandleOffline = (options) => {
  const offlineConfig = configManager.get('offlineMode') || {};
  const features = offlineConfig.features || {};
  
  // 根据URL判断请求类型
  const url = options.url.toLowerCase();
  
  if (url.includes('/chat') || url.includes('/generate')) {
    return features.chat === true;
  } else if (url.includes('/translate')) {
    return features.translate === true;
  } else if (url.includes('/image') || url.includes('/vision')) {
    return features.image === true;
  } else if (url.includes('/voice') || url.includes('/audio')) {
    return features.voice === true;
  }
  
  return false;
};

// 处理离线请求
const handleOfflineRequest = (options) => {
  // 这里可以实现离线模式的模拟响应
  return new Promise((resolve, reject) => {
    // 模拟延迟
    setTimeout(() => {
      const url = options.url.toLowerCase();
      
      if (url.includes('/translate')) {
        // 离线翻译（简单实现）
        const text = options.data && (options.data.text || options.data.content);
        if (text) {
          resolve({
            success: true,
            result: `[离线翻译] ${text}`,
            offline: true
          });
          return;
        }
      } else if (url.includes('/voice')) {
        // 离线语音识别
        resolve({
          success: true,
          result: '离线模式下无法使用语音识别',
          offline: true
        });
        return;
      }
      
      // 其他请求返回离线提示
      reject({
        errCode: 'OFFLINE',
        errMsg: '当前处于离线模式，无法完成请求',
        offline: true
      });
    }, 500);
  });
};

// API服务
const apiService = {
  // 初始化
  init() {
    initNetworkListener();
    return this;
  },
  
  // 获取网络状态
  getNetworkStatus() {
    return {
      type: networkType,
      available: networkAvailable
    };
  },
  
  // 设置网络状态变化回调
  onNetworkStatusChange(callback) {
    onNetworkStatusChange = callback;
    return this;
  },
  
  // 基本请求方法
  request,
  
  // GET请求
  get(url, data, options = {}) {
    return request({
      url,
      method: 'GET',
      data,
      ...options
    });
  },
  
  // POST请求
  post(url, data, options = {}) {
    return request({
      url,
      method: 'POST',
      data,
      ...options
    });
  },
  
  // 上传文件
  upload(url, filePath, name = 'file', formData = {}, options = {}) {
    const baseUrl = options.baseUrl || configManager.get('apiBaseUrl');
    const fullUrl = url.startsWith('http') ? url : configManager.joinUrl(baseUrl, url);
    const token = wx.getStorageSync('token') || '';
    
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: fullUrl,
        filePath,
        name,
        formData,
        header: {
          'Authorization': token ? `Bearer ${token}` : '',
          ...options.header
        },
        success: (res) => {
          // 尝试解析JSON响应
          try {
            const data = JSON.parse(res.data);
            resolve(data);
          } catch (e) {
            resolve(res.data);
          }
        },
        fail: (error) => {
          reject(error);
        }
      });
    });
  },
  
  // 处理大型图片上传（分块处理）
  uploadLargeImage(url, filePath, options = {}) {
    return new Promise((resolve, reject) => {
      // 读取文件信息
      wx.getFileInfo({
        filePath,
        success: (fileInfo) => {
          const fileSize = fileInfo.size;
          const maxSize = configManager.get('requestConfig.maxImageSize') || 5 * 1024 * 1024;
          
          // 如果文件大小超过限制，需要压缩
          if (fileSize > maxSize) {
            console.log(`[API] 图片大小(${fileSize})超过限制(${maxSize})，进行压缩`);
            
            // 压缩图片
            wx.compressImage({
              src: filePath,
              quality: 80,
              success: (res) => {
                // 上传压缩后的图片
                this.upload(url, res.tempFilePath, 'image', {}, options)
                  .then(resolve)
                  .catch(reject);
              },
              fail: (error) => {
                reject({
                  errCode: 'COMPRESS_FAIL',
                  errMsg: '图片压缩失败',
                  error
                });
              }
            });
          } else {
            // 直接上传
            this.upload(url, filePath, 'image', {}, options)
              .then(resolve)
              .catch(reject);
          }
        },
        fail: (error) => {
          reject({
            errCode: 'FILE_INFO_FAIL',
            errMsg: '获取文件信息失败',
            error
          });
        }
      });
    });
  },
  
  // 检查服务可用性
  checkServiceAvailability(baseUrl, options = {}) {
    return request({
      url: '/api/tags',
      baseUrl,
      method: 'GET',
      timeout: options.timeout || 10000,
      retryCount: options.retryCount || 1,
      showError: options.showError !== false,
      showLoading: false
    });
  },
  
  // 获取可用模型列表
  getAvailableModels(baseUrl, options = {}) {
    return this.checkServiceAvailability(baseUrl, options)
      .then(res => {
        if (res && res.models) {
          return res.models.map(model => model.name);
        }
        return [];
      })
      .catch(() => []);
  },
  
  // Ollama聊天API
  chat(messages, modelConfig = {}, options = {}) {
    const config = configManager.getConfig();
    const defaultModelConfig = config.modelConfig || {};
    
    // 合并模型配置
    const mergedConfig = {
      ...defaultModelConfig,
      ...modelConfig
    };
    
    return request({
      url: '/api/chat',
      method: 'POST',
      data: {
        messages,
        ...mergedConfig
      },
      ...options
    });
  },
  
  // Ollama图像识别API
  imageRecognition(base64Image, prompt, modelConfig = {}, options = {}) {
    const config = configManager.getConfig();
    const imageModelConfig = config.imageModelConfig || {};
    const defaultModel = imageModelConfig.defaultModel || 'gemma3:12b';
    
    // 获取模型特定配置
    const modelSpecificConfig = (imageModelConfig.models && imageModelConfig.models[defaultModel]) || {};
    
    // 合并模型配置
    const mergedConfig = {
      ...imageModelConfig,
      ...modelSpecificConfig,
      ...modelConfig,
      model: modelConfig.model || defaultModel
    };
    
    // 构建消息
    const messages = [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt || '请描述这张图片' },
          { type: 'image', image: base64Image }
        ]
      }
    ];
    
    return request({
      url: '/api/chat',
      method: 'POST',
      data: {
        messages,
        ...mergedConfig
      },
      ...options
    });
  },
  
  // 音乐服务API
  music: {
    // 获取音乐列表
    getList(options = {}) {
      const musicApiBaseUrl = configManager.get('musicApiBaseUrl');
      
      return request({
        url: '/api/songs',
        baseUrl: musicApiBaseUrl,
        method: 'GET',
        ...options
      });
    },
    
    // 获取音乐详情
    getDetail(id, options = {}) {
      const musicApiBaseUrl = configManager.get('musicApiBaseUrl');
      
      return request({
        url: `/api/songs/${id}`,
        baseUrl: musicApiBaseUrl,
        method: 'GET',
        ...options
      });
    },
    
    // 上传音乐
    upload(filePath, metadata = {}, options = {}) {
      const musicApiBaseUrl = configManager.get('musicApiBaseUrl');
      
      return this.upload(
        '/api/songs/upload',
        filePath,
        'file',
        metadata,
        {
          baseUrl: musicApiBaseUrl,
          ...options
        }
      );
    }
  }
};

// 初始化API服务
apiService.init();

module.exports = apiService; 