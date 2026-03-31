// app.js
// 导入服务和配置
const configManager = require('./utils/config-manager');
const apiService = require('./utils/api-service');
const historyManager = require('./utils/history-manager');

// Add mock requirePlugin method to wx object
if (!wx.requirePlugin) {
  wx.requirePlugin = function(name) {
    console.log('[Mock] requirePlugin:', name);
    if (name === 'WechatSI') {
      try {
        // First try loading the simplified plugin from root directory
        const rootPlugin = require('./WechatSI');
        console.log('[Mock] Successfully loaded WechatSI mock from root directory');
        return rootPlugin;
      } catch (rootError) {
        console.error('[Mock] Failed to load root mock plugin:', rootError);
        
        try {
          // Then try loading the plugin from npm directory
          const fakePlugin = require('./miniprogram_npm/WechatSI');
          console.log('[Mock] Successfully loaded WechatSI mock from npm directory');
          return fakePlugin;
        } catch (error) {
          console.error('[Mock] Failed to load npm directory mock plugin:', error);
          // Try loading backup plugin
          try {
            const backupPlugin = require('./utils/fake-plugin');
            console.log('[Mock] Successfully loaded backup mock plugin');
            return backupPlugin;
          } catch (backupError) {
            console.error('[Mock] Failed to load backup mock plugin:', backupError);
            // Return simplest mock implementation
            console.log('[Mock] Using inline mock plugin');
            return {
              getRecordRecognitionManager: function() {
                return {
                  start: function() { console.log('[Mock] Starting recording'); },
                  stop: function() { console.log('[Mock] Stopping recording'); },
                  onStop: null
                };
              },
              getTranslateManager: function() {
                return {
                  translate: function(options) {
                    if (options && typeof options.success === 'function') {
                      setTimeout(() => {
                        options.success({
                          result: true,
                          translateResult: ['Inline mock translation result']
                        });
                      }, 500);
                    }
                  }
                };
              }
            };
          }
        }
      }
    }
    console.warn('[Mock] Unknown plugin:', name);
    return {};
  };
}

App({
    globalData: {
      userInfo: null,
      // 配置API接口地址 - 使用配置管理器
      apiBaseUrl: configManager.get('apiBaseUrl'),
      // Ollama API配置
      modelConfig: configManager.get('modelConfig'),
      // 是否是游客模式
      isGuestMode: false
    },
  
    onLaunch() {
      // 初始化全局错误处理
      this.initErrorHandler();
      
      // 检查是否是游客模式
      const isGuestMode = wx.getStorageSync('isGuestMode');
      this.globalData.isGuestMode = isGuestMode === true;
      
      // 首先检查模拟器环境，并创建一个默认的游客账号用于测试
      const isSimulator = this.checkIsSimulator();
      if (isSimulator) {
        console.log('检测到模拟器环境，创建游客账号');
        const guestUserInfo = {
          nickName: '游客用户',
          avatarUrl: '/images/default-avatar.png',
          gender: 0
        };
        
        // 保存游客信息
        wx.setStorageSync('userInfo', guestUserInfo);
        this.globalData.userInfo = guestUserInfo;
        
        // 生成游客token
        const guestToken = 'guest_token_' + Date.now();
        wx.setStorageSync('token', guestToken);
        
        // 标记为游客模式
        wx.setStorageSync('isGuestMode', true);
        this.globalData.isGuestMode = true;
      }
      
      // 检查是否已登录
      const token = wx.getStorageSync('token');
      if (!token) {
        // 如果没有token，需要跳转到登录页
        setTimeout(() => {
          wx.redirectTo({
            url: '/pages/login/login'
          });
        }, 100);
      } else {
        // 已登录，尝试获取用户信息
        this.getUserInfo();
      }
      
      // 检测网络环境，尝试连接Ollama服务
      this.checkOllamaService();
    },
    
    // 初始化全局错误处理
    initErrorHandler() {
      // 捕获全局JS错误
      wx.onError((res) => {
        console.error('全局错误:', res);
        
        // 检查是否包含路由错误
        if (res && 
            (res.message && res.message.includes('route') || 
             res.includes && res.includes('route'))) {
          this.handleRouteError(res);
        }
      });
      
      // 捕获Promise未处理的拒绝
      wx.onUnhandledRejection((res) => {
        console.error('未处理的Promise拒绝:', res);
      });
      
      // 定义全局route变量防止undefined错误
      if (typeof global !== 'undefined' && typeof global.route === 'undefined') {
        global.route = {
          is: function() { return false; },
          _: {} 
        };
      }
      
      // 定义全局route变量防止undefined错误 (微信环境)
      if (typeof getApp !== 'undefined') {
        const app = getApp() || this;
        if (!app.route) {
          app.route = {
            is: function() { return false; },
            _: {}
          };
        }
      }
    },
    
    // 检查是否在模拟器中运行
    checkIsSimulator() {
      try {
        // 获取系统信息
        const systemInfo = wx.getSystemInfoSync();
        console.log('当前系统信息:', systemInfo);
        
        // 模拟器通常会有特定标识
        return systemInfo.platform === 'devtools';
      } catch (error) {
        console.error('获取系统信息失败:', error);
        return false;
      }
    },
    
    // 检测Ollama服务连接状态
    checkOllamaService() {
      // 使用API服务检查Ollama服务可用性
      apiService.checkServiceAvailability(this.globalData.apiBaseUrl, {
        timeout: 10000,
        retryCount: 1,
        showError: false
      }).then(res => {
        console.log('Ollama服务连接成功:', res);
        
        // 获取可用模型列表
        if (res && res.models) {
          const availableModels = res.models.map(model => model.name);
          console.log('可用模型:', availableModels);
          
          // 获取配置的模型
          const configModel = configManager.get('modelConfig.model');
          
          // 检查是否有 gemma3:12b 模型
          const hasGemma = availableModels.includes('gemma3:12b');
          const hasDeepseek14b = availableModels.includes('deepseek-r1:14b');
          const hasDeepseek8b = availableModels.includes('deepseek-r1:8b');
          
          // 根据可用模型优先选择
          let selectedModel;
          if (hasGemma) {
            selectedModel = 'gemma3:12b';
            console.log('检测到 gemma3:12b 模型可用，将优先使用');
          } else if (hasDeepseek14b) {
            selectedModel = 'deepseek-r1:14b';
            console.log('未发现 gemma3:12b 模型，将使用 deepseek-r1:14b');
          } else if (hasDeepseek8b) {
            selectedModel = 'deepseek-r1:8b';
            console.log('未发现 gemma3 或 deepseek-r1:14b 模型，将使用 deepseek-r1:8b');
          } else if (availableModels.length > 0) {
            selectedModel = availableModels[0];
            console.log(`未找到推荐模型，将使用可用的 ${selectedModel} 模型`);
          } else {
            // 没有任何可用模型
            this.showModelInstallTip(configModel);
            return;
          }
          
          // 设置全局模型配置
          this.globalData.modelConfig.model = selectedModel;
          
          // 根据不同模型调整参数
          if (selectedModel === 'gemma3:12b') {
            this.globalData.modelConfig.temperature = 0.4;
            this.globalData.modelConfig.num_predict = 2000;
          } else if (selectedModel.includes('deepseek-r1:14b')) {
            this.globalData.modelConfig.temperature = 0.5;
            this.globalData.modelConfig.num_predict = 1500;
          } else {
            this.globalData.modelConfig.temperature = 0.7;
            this.globalData.modelConfig.num_predict = 1000;
          }
          
          // 显示使用的模型信息
          wx.showToast({
            title: `使用模型: ${selectedModel}`,
            icon: 'none',
            duration: 2000
          });
        } else {
          // 响应格式异常，可能Ollama服务有问题
          console.error('Ollama响应格式异常:', res);
          
          wx.showModal({
            title: 'Ollama服务异常',
            content: '服务响应格式不正确。请确保Ollama版本兼容(建议使用v0.1.17+)',
            showCancel: false
          });
        }
      }).catch(error => {
        console.error('Ollama服务连接失败:', error);
        
        // 如果连接失败，尝试使用localhost（适用于电脑模拟器环境）
        if (this.globalData.apiBaseUrl.indexOf('localhost') === -1 &&
            this.globalData.apiBaseUrl.indexOf('127.0.0.1') === -1) {
          const localUrl = 'http://127.0.0.1:11434';
          console.log('尝试连接本地服务:', localUrl);
          
          apiService.checkServiceAvailability(localUrl, {
            timeout: 5000,
            retryCount: 0,
            showError: false
          }).then(() => {
            this.globalData.apiBaseUrl = localUrl;
            console.log('切换到本地服务地址:', localUrl);
            
            wx.showToast({
              title: '已切换到本地服务',
              icon: 'none',
              duration: 2000
            });
            
            // 重新检查服务
            setTimeout(() => {
              this.checkOllamaService();
            }, 1000);
          }).catch(() => {
            console.error('Ollama服务无法连接');
            
            // 显示故障排除提示
            wx.showModal({
              title: 'Ollama连接失败',
              content: '请确认:\n1. Ollama服务已启动\n2. 端口11434可访问\n3. 尝试使用 ollama serve 命令重启服务\n\n故障排除指南:\n1. 检查防火墙设置\n2. 确认网络连接正常\n3. 尝试重启电脑或服务器',
              showCancel: false
            });
            
            // 启用离线模式
            configManager.set('offlineMode.enabled', true);
          });
        } else {
          // 已经是本地地址但仍然失败
          wx.showModal({
            title: 'Ollama服务未响应',
            content: '服务可能未启动或已崩溃，请尝试重启Ollama服务\n\n故障排除步骤:\n1. 打开命令提示符\n2. 运行 ollama serve 命令\n3. 等待服务启动后重试',
            showCancel: false
          });
          
          // 启用离线模式
          configManager.set('offlineMode.enabled', true);
        }
      });
    },
  
    getUserInfo() {
      const userInfo = wx.getStorageSync('userInfo')
      if (userInfo) {
        this.globalData.userInfo = userInfo
        return userInfo
      }
      
      // 如果没有缓存的用户信息，但有token，尝试重新获取
      const token = wx.getStorageSync('token')
      if (token) {
        // 这里可以添加从服务器获取用户信息的逻辑
        // 由于我们使用的是本地模型，这里模拟一个用户信息
        const mockUserInfo = {
          nickName: '微信用户',
          avatarUrl: '/images/default-avatar.png',
          gender: 1
        };
        this.globalData.userInfo = mockUserInfo;
        wx.setStorageSync('userInfo', mockUserInfo);
        return mockUserInfo;
      }
      
      return null;
    },
    
    // 更新用户头像
    updateUserAvatar(avatarUrl) {
      const userInfo = this.globalData.userInfo || {};
      userInfo.avatarUrl = avatarUrl;
      
      this.globalData.userInfo = userInfo;
      wx.setStorageSync('userInfo', userInfo);
      
      // 广播头像更新事件，让其他页面可以接收
      wx.getBackgroundAudioManager().title = 'avatarUpdated';
      
      return userInfo;
    },
    
    // 更新用户信息
    updateUserInfo(userInfo) {
      this.globalData.userInfo = userInfo;
      wx.setStorageSync('userInfo', userInfo);
      return userInfo;
    },
  
    // 封装请求方法 - 使用API服务
    request(options) {
      return apiService.request(options);
    },
  
    // 显示模型安装提示
    showModelInstallTip(modelName) {
      const fallbackModels = configManager.get('fallbackModels') || ['gemma3:12b', 'deepseek-r1:8b', 'deepseek-r1:14b'];
      
      // 检查配置的模型是否在备选列表中
      const suggestedModel = fallbackModels.includes(modelName) ? modelName : fallbackModels[0];
      
      wx.showModal({
        title: '需要安装AI模型',
        content: `未找到可用的AI模型。推荐安装以下模型之一:\n- gemma3:12b (推荐)\n- deepseek-r1:14b\n- deepseek-r1:8b\n\n请确保Ollama服务正在运行。\n\n安装命令:\nollama pull ${suggestedModel}`,
        confirmText: '我知道了',
        showCancel: false,
        success: (res) => {
          if (res.confirm) {
            // 尝试切换到一个可能存在的模型
            console.log(`尝试更换为备选模型: ${suggestedModel}`);
            this.globalData.modelConfig.model = suggestedModel;
            
            // 启用离线模式
            configManager.set('offlineMode.enabled', true);
          }
        }
      });
    },
  
    // 处理路由错误
    handleRouteError: function(error) {
      console.error('Route error detected:', error);
      
      // 尝试关闭所有页面，返回到首页
      wx.reLaunch({
        url: '/pages/index/index',
        fail: function(reLaunchError) {
          console.error('Failed to reLaunch to index:', reLaunchError);
          
          // 如果重定向到首页失败，尝试重定向到登录页
          wx.reLaunch({
            url: '/pages/login/login',
            fail: function(loginError) {
              console.error('Failed to reLaunch to login:', loginError);
              
              // 如果所有重定向都失败，显示错误提示
              wx.showModal({
                title: 'Navigation Error',
                content: 'The app encountered a navigation error. Please restart the app.',
                showCancel: false
              });
            }
          });
        }
      });
    },
    
    // 判断是否可以保存历史记录
    canSaveHistory() {
      return historyManager.canSaveHistory();
    }
  })