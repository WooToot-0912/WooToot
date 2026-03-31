const app = getApp()
const apiClient = require('../../utils/api-client')
const errorHandler = require('../../utils/error-handler')
const uiHelper = require('../../utils/ui-helper')
const validators = require('../../utils/validators')
const security = require('../../utils/security')

Page({
  data: {
    messages: [],
    inputMessage: '',
    scrollToMessage: '',
    userInfo: null,         // 用户信息
    userAvatar: '/images/user-avatar.png',  // 默认头像
    recording: false,
    isAiTyping: false,
    inputFocus: false,
    currentDate: '',
    chatHistory: [], // 用于保存聊天上下文
    isGuestMode: false, // 是否是游客模式
    // 添加模型选择相关数据
    availableModels: [], // 可用模型列表
    currentModel: '', // 当前选择的模型
    showModelSelector: false // 是否显示模型选择器
  },

  onLoad() {
    // 设置当前日期
    this.setCurrentDate();
    
    // 获取用户信息
    this.getUserInfo();
    
    // 检查是否是游客模式
    const isGuestMode = wx.getStorageSync('isGuestMode') || false;
    this.setData({ isGuestMode });
    
    // 获取当前模型和可用模型列表
    this.getModelInfo();
    
    // 初始化聊天记录
    const initialMessage = {
      id: 1,
      type: 'ai',
      content: '你好！我是AI助手，有什么我可以帮你的吗？',
      time: this.formatTime(new Date())
    };
    
    this.setData({
      messages: [initialMessage],
      chatHistory: [
        { role: 'assistant', content: initialMessage.content }
      ]
    });
  },
  
  // 获取当前模型和可用模型列表
  getModelInfo() {
    const currentModel = app.globalData.modelConfig.model;
    this.setData({ currentModel });
    
    // 获取可用模型列表
    wx.request({
      url: `${app.globalData.apiBaseUrl}/api/tags`,
      timeout: 5000,
      success: (res) => {
        if (res.data && res.data.models) {
          const availableModels = res.data.models.map(model => model.name);
          console.log('可用模型列表:', availableModels);
          
          // 获取配置中的备选模型
          const config = require('../../config');
          const preferredModels = config.fallbackModels || [];
          
          // 将配置的模型排在前面
          const sortedModels = [];
          
          // 首先添加当前使用的模型
          if (availableModels.includes(currentModel)) {
            sortedModels.push(currentModel);
          }
          
          // 然后添加偏好模型
          preferredModels.forEach(model => {
            if (model !== currentModel && availableModels.includes(model)) {
              sortedModels.push(model);
            }
          });
          
          // 最后添加其他模型
          availableModels.forEach(model => {
            if (!sortedModels.includes(model)) {
              sortedModels.push(model);
            }
          });
          
          this.setData({ availableModels: sortedModels });
        }
      },
      fail: (error) => {
        console.error('获取模型列表失败:', error);
      }
    });
  },
  
  // 显示/隐藏模型选择器
  toggleModelSelector() {
    this.setData({
      showModelSelector: !this.data.showModelSelector
    });
  },
  
  // 切换模型
  switchModel(e) {
    const { model } = e.currentTarget.dataset;
    if (model === this.data.currentModel) {
      // 如果选择的是当前模型，则只关闭选择器
      this.setData({ showModelSelector: false });
      return;
    }
    
    // 更新全局模型配置
    app.globalData.modelConfig.model = model;
    
    // 更新温度和生成长度设置
    const config = require('../../config');
    if (model === 'gemma3:12b') {
      app.globalData.modelConfig.temperature = 0.4;
      app.globalData.modelConfig.num_predict = 2000;
    } else if (model.includes('deepseek-r1:14b')) {
      app.globalData.modelConfig.temperature = 0.5;
      app.globalData.modelConfig.num_predict = 1500;
    } else {
      app.globalData.modelConfig.temperature = 0.7;
      app.globalData.modelConfig.num_predict = 1000;
    }
    
    // 更新界面
    this.setData({
      currentModel: model,
      showModelSelector: false
    });
    
    // 显示切换成功提示
    wx.showToast({
      title: `已切换到 ${model}`,
      icon: 'none',
      duration: 1500
    });
    
    // 向用户显示当前使用的模型
    const infoMessage = {
      id: Date.now(),
      type: 'info',
      content: `已切换到模型: ${model}`,
      time: this.formatTime(new Date())
    };
    
    this.setData({
      messages: [...this.data.messages, infoMessage],
      scrollToMessage: `msg-${infoMessage.id}`
    });
  },
  
  // 获取用户信息
  getUserInfo() {
    const app = getApp();
    const userInfo = app.getUserInfo();
    
    if (userInfo) {
      this.setData({ userInfo });
      console.log('获取到用户信息:', userInfo.nickName);
    } else {
      // 使用默认游客头像
      console.log('未获取到用户信息，使用默认头像');
    }
  },
  
  // 设置当前日期
  setCurrentDate() {
    const now = new Date();
    const days = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
    const date = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 ${days[now.getDay()]}`;
    this.setData({ currentDate: date });
  },
  
  // 页面显示时
  onShow() {
    // 每次显示页面时重新获取用户信息
    this.getUserInfo();
    
    // 检查是否是游客模式
    const isGuestMode = wx.getStorageSync('isGuestMode') || false;
    if (isGuestMode !== this.data.isGuestMode) {
      this.setData({ isGuestMode });
    }
  },
  
  // 格式化时间
  formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  },

  // 处理输入
  onInput(e) {
    this.setData({
      inputMessage: e.detail.value
    });
  },

  // 发送消息
  sendMessage() {
    const content = this.data.inputMessage.trim();
    if (!content) return;

    // 输入验证和安全过滤
    const validation = validators.isString(content, 1, 1000);
    if (!validation.valid) {
      uiHelper.showError(validation.message);
      return;
    }

    const sanitizedContent = security.sanitizeInput(content);

    const now = new Date();
    const timestamp = now.getTime();

    const userMessage = {
      id: timestamp,
      type: 'user',
      content: sanitizedContent,
      time: this.formatTime(now),
      timestamp: timestamp
    };

    // 添加用户消息到列表和聊天历史
    const updatedHistory = [...this.data.chatHistory, { role: 'user', content: sanitizedContent }];

    this.setData({
      messages: [...this.data.messages, userMessage],
      inputMessage: '',
      chatHistory: updatedHistory,
      scrollToMessage: `msg-${userMessage.id}`
    });

    // 获取AI回复
    this.getAIResponse(updatedHistory, userMessage);
  },

  // 获取AI回复
  getAIResponse(chatHistory, userMessage) {
    this.setData({
      isAiTyping: true
    });
    
    // 添加重试机制
    let retryCount = 0;
    const config = require('../../config');
    const maxRetries = config.requestConfig.retryCount;
    
    const callWithRetry = () => {
      return this.callOllamaAPI(chatHistory)
        .then(response => {
          this.setData({
            isAiTyping: false
          });
          
          const now = new Date();
          const timestamp = now.getTime();
          
          const aiMessage = {
            id: timestamp,
            type: 'ai',
            content: response,
            time: this.formatTime(now),
            timestamp: timestamp,
            parsedContent: this.parseMessageContent(response)
          };

          const updatedHistory = [...this.data.chatHistory, { role: 'assistant', content: response }];
          
          this.setData({
            messages: [...this.data.messages, aiMessage],
            chatHistory: updatedHistory,
            scrollToMessage: `msg-${aiMessage.id}`
          });
          
          // 保存聊天记录到本地存储（非游客模式下）
          this.saveChatHistory(userMessage, aiMessage);
        })
        .catch(error => {
          // 如果还有重试次数，则重试
          if (retryCount < maxRetries) {
            retryCount++;
            console.log(`API请求失败，正在重试(${retryCount}/${maxRetries})...`);
            
            wx.showToast({
              title: `请求超时，正在重试(${retryCount}/${maxRetries})`,
              icon: 'none',
              duration: 1500
            });
            
            return new Promise(resolve => {
              setTimeout(() => {
                resolve(callWithRetry());
              }, config.requestConfig.retryDelay);
            });
          }
          
          // 如果已经用完所有重试次数，则显示错误
          this.setData({
            isAiTyping: false
          });
          
          console.error('API响应失败:', error);
          wx.showToast({
            title: '获取回复失败，请稍后再试',
            icon: 'none',
            duration: 3000
          });
        });
    };
    
    return callWithRetry();
  },
  
  // 保存聊天记录到本地存储
  saveChatHistory(userMessage, aiMessage) {
    // 检查是否是游客模式
    if (this.data.isGuestMode) {
      console.log('游客模式，不保存聊天记录');
      return;
    }
    
    // 检查是否有app全局方法
    if (app && app.canSaveHistory && !app.canSaveHistory()) {
      console.log('根据全局设置，不保存聊天记录');
      return;
    }
    
    try {
      // 获取现有的聊天历史记录
      const existingHistory = wx.getStorageSync('chatHistory') || [];
      
      // 创建一个新的历史记录条目
      const historyItem = {
        id: `chat_${Date.now()}`,
        query: userMessage.content,
        result: aiMessage.content,
        timestamp: aiMessage.timestamp || Date.now(),
        content: userMessage.content
      };
      
      // 添加到历史记录并保存
      const updatedHistory = [historyItem, ...existingHistory].slice(0, 50); // 只保留最近50条
      wx.setStorageSync('chatHistory', updatedHistory);
      
      console.log('聊天记录已保存');
    } catch (error) {
      console.error('保存聊天记录失败:', error);
    }
  },

  // 解析消息内容，识别代码块
  parseMessageContent(content) {
    const blocks = [];
    const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // 添加代码块之前的普通文本
      if (match.index > lastIndex) {
        blocks.push({
          isCode: false,
          content: content.slice(lastIndex, match.index)
        });
      }

      // 添加代码块
      blocks.push({
        isCode: true,
        language: match[1] || 'code',
        content: match[2]
      });

      lastIndex = match.index + match[0].length;
    }

    // 添加最后一部分普通文本
    if (lastIndex < content.length) {
      blocks.push({
        isCode: false,
        content: content.slice(lastIndex)
      });
    }

    return blocks.length > 0 ? blocks : null;
  },

  copyCode(e) {
    const { code } = e.currentTarget.dataset;
    wx.setClipboardData({
      data: code,
      success: () => {
        wx.showToast({
          title: '代码已复制',
          icon: 'success'
        });
      }
    });
  },

  copyMessage(e) {
    const { content } = e.currentTarget.dataset;
    wx.setClipboardData({
      data: content,
      success: () => {
        wx.showToast({
          title: '已复制',
          icon: 'success'
        });
      }
    });
  },

  // 检查模型状态 - 修改以整合模型切换功能
  checkModelStatus() {
    // 检查全局模型配置
    if (!app.globalData.modelConfig) {
      console.error('无法获取模型配置');
      return;
    }
    
    // 获取当前模型名称
    const currentModel = app.globalData.modelConfig.model;
    console.log('当前使用模型:', currentModel);
    
    // 如果没有可用模型，提示用户
    if (!currentModel) {
      wx.showModal({
        title: '未找到可用模型',
        content: '系统未检测到可用的AI模型，请确认Ollama服务正常运行并安装了必要的模型',
        showCancel: false
      });
      return;
    }
    
    // 更新当前模型
    this.setData({ currentModel });
    
    // 向用户显示当前使用的模型
    const infoMessage = {
      id: Date.now(),
      type: 'info',
      content: `当前使用模型: ${currentModel}`,
      time: this.formatTime(new Date())
    };
    
    this.setData({
      messages: [...this.data.messages, infoMessage],
      scrollToMessage: `msg-${infoMessage.id}`
    });
    
    // 检查模型是否可用，并获取可用模型列表
    wx.request({
      url: `${app.globalData.apiBaseUrl}/api/tags`,
      timeout: 5000,
      success: (res) => {
        if (res.data && res.data.models) {
          const availableModels = res.data.models.map(model => model.name);
          
          // 更新可用模型列表
          this.setData({ 
            availableModels: availableModels 
          });
          
          if (!availableModels.includes(currentModel)) {
            console.warn(`当前配置的模型 ${currentModel} 不可用`);
            
            // 显示警告消息
            const warningMessage = {
              id: Date.now(),
              type: 'warning',
              content: `警告: 当前配置的模型 ${currentModel} 不可用，将尝试使用其他可用模型`,
              time: this.formatTime(new Date())
            };
            
            this.setData({
              messages: [...this.data.messages, warningMessage],
              scrollToMessage: `msg-${warningMessage.id}`
            });
          }
        }
      },
      fail: (error) => {
        console.error('检查模型状态失败:', error);
      }
    });
  },

  callOllamaAPI(chatHistory) {
    const recentHistory = chatHistory.slice(-10); // 只使用最近的10条消息作为上下文
    
    // 使用全局配置的模型
    const apiUrl = `${app.globalData.apiBaseUrl}/api/chat`;
    const modelConfig = app.globalData.modelConfig;
    
    console.log(`请求API ${apiUrl}，使用模型 ${modelConfig.model}`);
    
    return new Promise((resolve, reject) => {
      wx.request({
        url: apiUrl,
        method: 'POST',
        timeout: 30000, // 30秒超时
        data: {
          model: modelConfig.model,
          messages: recentHistory,
          stream: false,
          options: {
            temperature: modelConfig.temperature,
            num_predict: modelConfig.num_predict
          }
        },
        success: (res) => {
          if (res.statusCode === 200 && res.data) {
            console.log('API响应:', res.data);
            
            if (res.data.message && res.data.message.content) {
              // 新版Ollama API的响应格式
              resolve(res.data.message.content);
            } else if (res.data.response) {
              // 旧版Ollama API的响应格式
              resolve(res.data.response);
            } else {
              console.error('无法解析API响应:', res.data);
              reject(new Error('无法解析API响应'));
            }
          } else {
            console.error('API请求失败:', res.statusCode, res.data);
            
            if (res.statusCode === 404 || res.statusCode === 400) {
              // 可能是模型不存在，尝试使用备选模型
              console.log('尝试使用备选模型');
              this.tryFallbackModel(app, chatHistory)
                .then(response => resolve(response))
                .catch(error => reject(error));
            } else {
              reject(new Error(`API请求失败: ${res.statusCode}`));
            }
          }
        },
        fail: (error) => {
          console.error('请求失败:', error);
          reject(error);
        }
      });
    });
  },

  // 尝试使用备用模型
  tryFallbackModel(app, chatHistory) {
    // 从配置中获取备选模型列表
    const config = require('../../config');
    const fallbackModels = config.fallbackModels || ['deepseek-r1:8b', 'deepseek-r1:14b'];
    let foundAlternative = false;
    
    return new Promise((resolve, reject) => {
      // 检查可用模型
      wx.request({
        url: `${app.globalData.apiBaseUrl}/api/tags`,
        timeout: 5000,
        success: (res) => {
          if (res.data && res.data.models && res.data.models.length > 0) {
            const availableModels = res.data.models.map(model => model.name);
            console.log('可用模型:', availableModels);
            
            // 尝试从备选列表中找到一个可用的
            for (const model of fallbackModels) {
              if (availableModels.includes(model)) {
                console.log(`找到可用的备选模型: ${model}`);
                app.globalData.modelConfig.model = model;
                foundAlternative = true;
                
                // 提示用户已切换模型
                wx.showToast({
                  title: `已切换到模型: ${model}`,
                  icon: 'none',
                  duration: 2000
                });
                
                // 使用新模型重新发送请求
                this.callOllamaAPI(chatHistory)
                  .then(response => resolve(response))
                  .catch(error => reject(error));
                
                break;
              }
            }
            
            // 如果没有找到可用的备选模型
            if (!foundAlternative) {
              if (availableModels.length > 0) {
                const firstAvailable = availableModels[0];
                console.log(`使用第一个可用模型: ${firstAvailable}`);
                app.globalData.modelConfig.model = firstAvailable;
                
                wx.showToast({
                  title: `已切换到模型: ${firstAvailable}`,
                  icon: 'none', 
                  duration: 2000
                });
                
                // 使用第一个可用模型重新发送请求
                this.callOllamaAPI(chatHistory)
                  .then(response => resolve(response))
                  .catch(error => reject(error));
              } else {
                // 没有可用模型
                wx.showModal({
                  title: '没有可用模型',
                  content: '找不到可用的AI模型，请确认Ollama服务正常运行',
                  showCancel: false
                });
                reject(new Error('没有可用模型'));
              }
            }
          } else {
            // 没有可用模型
            wx.showModal({
              title: '没有可用模型',
              content: '请确认Ollama服务正常运行',
              showCancel: false
            });
            reject(new Error('没有可用模型'));
          }
        },
        fail: (error) => {
          console.error('获取模型列表失败:', error);
          reject(error);
        }
      });
    });
  },

  startVoiceInput() {
    // 检查是否有录音权限
    wx.authorize({
      scope: 'scope.record',
      success: () => {
        this.setData({ recording: true });
        
        // 使用新版录音API
        const recorderManager = wx.getRecorderManager();
        recorderManager.start({
          duration: 60000, // 最长录音时间，单位ms
          sampleRate: 16000,
          numberOfChannels: 1,
          encodeBitRate: 48000,
          format: 'mp3'
        });
        
        // 监听录音结束
        recorderManager.onStop(res => {
          this.setData({ recording: false });
          if (res.tempFilePath) {
            this.recognizeVoice(res.tempFilePath);
          }
        });
        
        // 点击停止录音
        wx.showModal({
          title: '录音中',
          content: '点击确定结束录音',
          success: (res) => {
            if (res.confirm || res.cancel) {
              recorderManager.stop();
            }
          }
        });
      },
      fail: () => {
        wx.showToast({
          title: '请授权录音权限',
          icon: 'none'
        });
      }
    });
  },

  async recognizeVoice(tempFilePath) {
    try {
      wx.showLoading({
        title: '识别中...',
      });
      
      // 使用模拟数据替代真实API调用
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // 模拟识别结果
      const text = "这是语音识别的模拟结果。API功能已临时禁用。";
      wx.hideLoading();
      
      // 设置输入框内容并聚焦
      this.setData({ 
        inputMessage: text, 
        inputFocus: true 
      });
      
      wx.showToast({
        title: '使用模拟数据',
        icon: 'none',
        duration: 1500
      });
      
    } catch (error) {
      wx.hideLoading();
      wx.showToast({
        title: '语音识别失败',
        icon: 'none'
      });
      console.error('语音识别失败:', error);
    }
  },

  loadMoreMessages() {
    // 实现加载更多历史消息的逻辑
    wx.showToast({
      title: '没有更多消息',
      icon: 'none'
    })
  },
  
  // 清空聊天记录
  clearChat() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空所有聊天记录吗？',
      success: (res) => {
        if (res.confirm) {
          const initialMessage = {
            id: Date.now(),
            type: 'ai',
            content: '聊天记录已清空，有什么我可以帮你的吗？',
            time: this.formatTime(new Date())
          };
          
          this.setData({
            messages: [initialMessage],
            chatHistory: [{ role: 'assistant', content: initialMessage.content }]
          });
        }
      }
    });
  }
}) 