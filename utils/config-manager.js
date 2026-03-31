/**
 * 配置管理器
 * 统一管理项目配置，支持环境区分和配置覆盖
 */

// 环境配置
const ENV = {
  DEV: 'development',
  TEST: 'testing',
  PROD: 'production'
};

// 当前环境，默认为开发环境
let currentEnv = ENV.DEV;

// 判断是否在开发者工具中运行
const inDevTool = wx.getSystemInfoSync().platform === 'devtools';

// 基础配置
const baseConfig = {
  // API服务地址 - 开发环境默认使用localhost
  apiBaseUrl: 'http://127.0.0.1:11434',
  musicApiBaseUrl: 'http://127.0.0.1:5000',
  
  // AI模型配置
  modelConfig: {
    model: 'gemma3:12b',
    temperature: 0.5,
    num_predict: 1000,
    system_prompt: "你是一个有用的AI助手。回答要简洁、专业。对于代码问题，给出简短但实用的示例。"
  },
  
  // 备选模型（当配置的模型不可用时）
  fallbackModels: [
    'gemma3:12b',
    'deepseek-r1:14b',
    'deepseek-r1:8b'
  ],
  
  // 图像识别模型配置
  imageModelConfig: {
    defaultModel: 'gemma3:12b',
    temperature: 0.3,
    num_predict: 2000,
    // 不同模型的配置
    models: {
      'gemma3:12b': {
        label: 'Gemma 3 (高精度)',
        temperature: 0.3,
        num_predict: 2000,
        apiEndpoint: '/api/chat',
        supportsVision: true
      },
      'deepseek-r1:14b': {
        label: 'DeepSeek 14B (通用)',
        temperature: 0.5,
        num_predict: 1500,
        apiEndpoint: '/api/generate',
        supportsVision: false
      },
      'deepseek-r1:8b': {
        label: 'DeepSeek 8B (快速)',
        temperature: 0.7,
        num_predict: 1000,
        apiEndpoint: '/api/generate',
        supportsVision: false
      }
    }
  },
  
  // 请求配置
  requestConfig: {
    timeout: 60000,
    retryCount: 2,
    retryDelay: 1000,
    maxImageSize: 5 * 1024 * 1024, // 5MB
    imageSplitSize: 1024 * 1024, // 1MB 分块大小
  },
  
  // 语音配置
  voiceConfig: {
    enabled: false,
    method: 'local',
    timeout: 10000
  },
  
  // 历史记录配置
  historyConfig: {
    maxChatHistory: 10,
    maxTranslateHistory: 20,
    maxImageHistory: 15,
    maxVoiceHistory: 15,
    autoCleanup: true
  },
  
  // 离线模式配置
  offlineMode: {
    enabled: false,
    retryInterval: 30000, // 30秒重试一次
    features: {
      chat: false,
      translate: true,
      image: false,
      voice: true
    }
  },
  
  // 安全配置
  securityConfig: {
    encryptApiKeys: true,
    encryptionKey: 'wx_mini_app_secure_key',
    apiAccessControl: true,
    maxFailedAttempts: 5
  }
};

// 环境特定配置
const envConfigs = {
  [ENV.DEV]: {
    // 开发环境特定配置
    apiBaseUrl: 'http://127.0.0.1:11434',
    musicApiBaseUrl: 'http://127.0.0.1:5000',
    debug: true
  },
  [ENV.TEST]: {
    // 测试环境特定配置
    apiBaseUrl: 'http://172.20.10.3:11434',
    musicApiBaseUrl: 'http://172.20.10.3:5000',
    debug: true
  },
  [ENV.PROD]: {
    // 生产环境特定配置
    apiBaseUrl: 'http://172.20.10.3:11434',
    musicApiBaseUrl: 'http://172.20.10.3:5000',
    debug: false
  }
};

// 用户自定义配置（从本地存储加载）
let userConfig = {};
try {
  const savedUserConfig = wx.getStorageSync('userConfig');
  if (savedUserConfig) {
    userConfig = JSON.parse(savedUserConfig);
  }
} catch (error) {
  console.error('加载用户配置失败:', error);
}

// 合并配置
const mergeConfig = () => {
  // 根据环境选择配置
  const envConfig = envConfigs[currentEnv] || {};
  
  // 合并配置 (基础配置 < 环境配置 < 用户配置)
  return {
    ...baseConfig,
    ...envConfig,
    ...userConfig
  };
};

// 配置管理器
const configManager = {
  // 获取当前完整配置
  getConfig() {
    return mergeConfig();
  },
  
  // 获取特定配置项
  get(key) {
    const config = mergeConfig();
    return key.split('.').reduce((obj, k) => obj && obj[k] !== undefined ? obj[k] : undefined, config);
  },
  
  // 设置用户配置
  set(key, value) {
    // 支持对象形式设置多个值
    if (typeof key === 'object') {
      userConfig = { ...userConfig, ...key };
    } else {
      // 设置单个值，支持嵌套路径如 'requestConfig.timeout'
      const keys = key.split('.');
      const lastKey = keys.pop();
      let current = userConfig;
      
      keys.forEach(k => {
        if (!current[k] || typeof current[k] !== 'object') {
          current[k] = {};
        }
        current = current[k];
      });
      
      current[lastKey] = value;
    }
    
    // 保存到本地存储
    try {
      wx.setStorageSync('userConfig', JSON.stringify(userConfig));
    } catch (error) {
      console.error('保存用户配置失败:', error);
    }
    
    return this;
  },
  
  // 重置用户配置
  reset() {
    userConfig = {};
    try {
      wx.removeStorageSync('userConfig');
    } catch (error) {
      console.error('重置用户配置失败:', error);
    }
    return this;
  },
  
  // 设置当前环境
  setEnvironment(env) {
    if (Object.values(ENV).includes(env)) {
      currentEnv = env;
      return true;
    }
    return false;
  },
  
  // 获取当前环境
  getEnvironment() {
    return currentEnv;
  },
  
  // 检测当前是否为开发者工具
  isDevTool() {
    return inDevTool;
  },
  
  // 工具函数：安全拼接URL路径
  joinUrl(base, path) {
    // 确保基础URL没有尾随斜杠
    if (base.endsWith('/')) {
      base = base.slice(0, -1);
    }
    
    // 确保路径以斜杠开头
    if (!path.startsWith('/')) {
      path = '/' + path;
    }
    
    // 避免/api重复
    if (base.endsWith('/api') && path.startsWith('/api')) {
      return base + path.substring(4);
    }
    
    return base + path;
  },
  
  // 自动检测并设置最佳环境
  autoDetectEnvironment() {
    try {
      const systemInfo = wx.getSystemInfoSync();
      
      // 根据系统信息判断环境
      if (systemInfo.platform === 'devtools') {
        this.setEnvironment(ENV.DEV);
      } else {
        // 可以根据网络状态、设备信息等进一步判断
        const network = wx.getNetworkType({
          success: (res) => {
            if (res.networkType === 'wifi') {
              // WiFi环境可能是测试环境
              this.setEnvironment(ENV.TEST);
            } else {
              // 其他网络环境可能是生产环境
              this.setEnvironment(ENV.PROD);
            }
          },
          fail: () => {
            // 默认使用生产环境
            this.setEnvironment(ENV.PROD);
          }
        });
      }
    } catch (error) {
      console.error('自动检测环境失败:', error);
      // 默认使用开发环境
      this.setEnvironment(ENV.DEV);
    }
  }
};

// 初始化时自动检测环境
configManager.autoDetectEnvironment();

module.exports = configManager; 