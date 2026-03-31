const app = getApp()

// 支持的语言列表
const languages = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: '英语' },
  { code: 'ja', name: '日语' },
  { code: 'ko', name: '韩语' },
  { code: 'fr', name: '法语' },
  { code: 'de', name: '德语' },
  { code: 'es', name: '西班牙语' },
  { code: 'it', name: '意大利语' },
  { code: 'ru', name: '俄语' },
  { code: 'pt', name: '葡萄牙语' }
]

// 支持的模型列表
const models = [
  {name: 'Qwen2.5VL 7B', value: 'qwen2.5vl:7b'},
  {name: 'LLaVA Latest', value: 'llava:latest'},
  {name: 'Bakllava 7B', value: 'bakllava:7b'},
  {name: 'Gemma 3', value: 'gemma3:12b'},
  {name: 'DeepSeek 8B', value: 'deepseek-r1:8b'},
  {name: 'DeepSeek 14B', value: 'deepseek-r1:14b'}
]

// Ollama API配置
const API = {
  endpoints: {
    generate: '/api/generate',
    chat: '/api/chat',
    tags: '/api/tags'
  }
}

// 获取基础URL
function getBaseUrl() {
  const app = getApp();
  return app.globalData.apiBaseUrl;
}

Page({
  data: {
    languages,
    models,
    selectedModel: 'Qwen2.5VL 7B', // 默认选择的模型名称
    selectedModelValue: 'qwen2.5vl:7b', // 默认选择的模型值
    sourceLanguage: languages[0], // 默认源语言为中文
    targetLanguage: languages[1], // 默认目标语言为英语
    inputText: '',
    translatedText: '',
    translateHistory: [],
    showLanguagePicker: false,
    showModelPicker: false, // 新增：模型选择器显示状态
    isSelectingSource: true,
    isRecording: false,
    showLoading: false,
    networkAvailable: true
  },

  onLoad(options) {
    // 检查网络状态
    this.checkNetworkStatus()
    
    // 监听网络状态变化
    wx.onNetworkStatusChange((result) => {
      this.setData({
        networkAvailable: result.isConnected
      })
      if (!result.isConnected) {
        wx.showToast({
          title: '网络连接已断开',
          icon: 'error'
        })
      }
    })
    
    // 处理从其他页面传递过来的文本
    if (options && options.text) {
      const text = decodeURIComponent(options.text);
      this.setData({
        inputText: text
      });
      
      // 自动翻译传入的文本
      setTimeout(() => {
        this.translate();
      }, 500);
    }

    // 初始化录音管理器
    this.recorderManager = wx.getRecorderManager()
    
    // 监听录音结束事件
    this.recorderManager.onStop((res) => {
      if (!this.data.networkAvailable) {
        wx.showToast({
          title: '请检查网络连接',
          icon: 'error'
        })
        return
      }

      this.setData({ 
        isRecording: false,
        showLoading: true
      })
      
      const { tempFilePath } = res
      
      // 将音频转换为文本
      // 注意：目前不直接支持语音识别，这里需要其他服务配合
      wx.showToast({
        title: '语音识别暂不可用',
        icon: 'error'
      })
      this.setData({ showLoading: false })
    })

    // 加载历史记录
    const history = wx.getStorageSync('translateHistory') || []
    this.setData({ translateHistory: history })
  },

  // 新增：切换模型
  switchModel() {
    this.setData({
      showModelPicker: true
    });
  },

  // 新增：隐藏模型选择器
  hideModelPicker() {
    this.setData({
      showModelPicker: false
    });
  },

  // 新增：选择模型
  selectModel(e) {
    const modelIndex = e.currentTarget.dataset.index;
    const selectedModel = this.data.models[modelIndex];
    
    this.setData({
      selectedModel: selectedModel.name,
      selectedModelValue: selectedModel.value,
      showModelPicker: false
    });
    
    wx.showToast({
      title: `已切换到${selectedModel.name}`,
      icon: 'none'
    });
  },

  // 检查网络状态
  checkNetworkStatus() {
    wx.getNetworkType({
      success: (res) => {
        const networkAvailable = res.networkType !== 'none'
        this.setData({ networkAvailable })
        if (!networkAvailable) {
          wx.showToast({
            title: '请检查网络连接',
            icon: 'error'
          })
        }
      }
    })
  },

  // 处理API错误
  handleApiError(error) {
    console.error('API错误：', error)
    if (!this.data.networkAvailable) {
      wx.showToast({
        title: '请检查网络连接',
        icon: 'error'
      })
    } else if (error.errMsg && error.errMsg.includes('timeout')) {
      wx.showToast({
        title: '请求超时',
        icon: 'error'
      })
    } else if (error.errMsg && error.errMsg.includes('domain')) {
      wx.showToast({
        title: '域名配置错误',
        icon: 'error'
      })
    } else {
      wx.showToast({
        title: '网络错误',
        icon: 'error'
      })
    }
  },

  // 显示源语言选择器
  showSourceLanguages() {
    this.setData({
      showLanguagePicker: true,
      isSelectingSource: true
    })
  },

  // 显示目标语言选择器
  showTargetLanguages() {
    this.setData({
      showLanguagePicker: true,
      isSelectingSource: false
    })
  },

  // 隐藏语言选择器
  hideLanguagePicker() {
    this.setData({
      showLanguagePicker: false
    })
  },

  // 选择语言
  selectLanguage(e) {
    const language = e.currentTarget.dataset.language
    if (this.data.isSelectingSource) {
      if (language.code === this.data.targetLanguage.code) {
        this.switchLanguages()
      } else {
        this.setData({ sourceLanguage: language })
      }
    } else {
      if (language.code === this.data.sourceLanguage.code) {
        this.switchLanguages()
      } else {
        this.setData({ targetLanguage: language })
      }
    }
    this.hideLanguagePicker()
  },

  // 切换源语言和目标语言
  switchLanguages() {
    const { sourceLanguage, targetLanguage, inputText, translatedText } = this.data
    this.setData({
      sourceLanguage: targetLanguage,
      targetLanguage: sourceLanguage,
      inputText: translatedText,
      translatedText: inputText
    })
  },

  // 输入文本变化
  onInput(e) {
    this.setData({
      inputText: e.detail.value
    })
  },

  // 开始语音输入
  startVoiceInput() {
    // 检查录音权限
    wx.authorize({
      scope: 'scope.record',
      success: () => {
        this.setData({ isRecording: true })
        this.recorderManager.start({
          duration: 60000,
          sampleRate: 16000,
          numberOfChannels: 1,
          encodeBitRate: 48000,
          format: 'mp3'
        })
      },
      fail: () => {
        wx.showModal({
          title: '提示',
          content: '需要您授权录音权限',
          success: (res) => {
            if (res.confirm) {
              wx.openSetting()
            }
          }
        })
      }
    })
  },

  // 结束语音输入
  stopVoiceInput() {
    if (this.data.isRecording) {
      this.recorderManager.stop()
    }
  },

  // 清空输入
  clearInput() {
    this.setData({
      inputText: '',
      translatedText: ''
    })
  },

  // 格式化时间
  formatTime(date) {
    const hour = date.getHours();
    const minute = date.getMinutes();
    
    return `${hour < 10 ? '0' + hour : hour}:${minute < 10 ? '0' + minute : minute}`;
  },
  
  // 执行翻译
  translate() {
    if (!this.data.inputText) return
    
    if (!this.data.networkAvailable) {
      wx.showToast({
        title: '请检查网络连接',
        icon: 'error'
      })
      return
    }

    this.setData({ showLoading: true })
    
    // 从全局配置获取基础URL
    const baseUrl = getBaseUrl();
    const ollamaUrl = `${baseUrl}/api/generate`;
    
    // 获取当前选择的模型
    const modelName = this.data.selectedModel;
    const modelValue = this.data.selectedModelValue || 'llava:latest';
    
    console.log('开始翻译请求 (Ollama):', {
      url: ollamaUrl,
      model: modelValue,
      modelName: modelName,
      sourceLanguage: this.data.sourceLanguage.name,
      targetLanguage: this.data.targetLanguage.name,
      inputText: this.data.inputText
    });

    // 调用Ollama API进行翻译
    wx.request({
      url: ollamaUrl,  // 直接使用完整URL
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: {
        model: modelValue,  // 使用选择的模型
        prompt: `Translate the following text from ${this.data.sourceLanguage.name} to ${this.data.targetLanguage.name}. Only provide the translation, no explanations:\n\n${this.data.inputText}`,
        stream: false,
        options: {
          temperature: 0.7,
          num_predict: 2000
        }
      },
      timeout: 30000,
      success: (res) => {
        try {
          console.log('Ollama API响应:', res.data);
          
          // 解析Ollama格式的响应
          let translation = '';
          if (res.data && res.data.response) {
            translation = res.data.response.trim();
          } else {
            throw new Error('无法解析翻译结果');
          }
          
          // 更新翻译结果
          const now = new Date();
          this.setData({
            translatedText: translation,
            translateHistory: [{
              from: this.data.sourceLanguage.name,
              to: this.data.targetLanguage.name,
              source: this.data.inputText,
              result: translation,
              time: this.formatTime(now),
              model: modelName, // 添加使用的模型名称
              modelValue: modelValue // 添加使用的模型值
            }, ...this.data.translateHistory].slice(0, 20) // 保留最近20条记录
          })
          
          // 保存到本地存储
          wx.setStorageSync('translateHistory', this.data.translateHistory)
          
        } catch (error) {
          console.error('翻译结果处理失败:', error);
          wx.showToast({
            title: '翻译结果解析失败',
            icon: 'error'
          });
        }
      },
      fail: (error) => {
        console.error('Ollama API调用失败:', error);
        
        // 尝试重新检测服务连接
        const app = getApp();
        app.checkOllamaService();
        
        wx.showModal({
          title: '连接错误',
          content: '无法连接到Ollama服务，请确保服务已启动: ' + (error.errMsg || '未知错误'),
          showCancel: false
        });
      },
      complete: () => {
        this.setData({ showLoading: false });
      }
    });
  },

  // 播放翻译结果语音
  playTranslation() {
    if (!this.data.translatedText) return
    
    if (!this.data.networkAvailable) {
      wx.showToast({
        title: '请检查网络连接',
        icon: 'error'
      })
      return
    }
    
    // 文本转语音功能暂不可用
    wx.showToast({
      title: '语音播放暂不可用',
      icon: 'none',
      duration: 2000
    })
  },

  // 复制翻译结果
  copyResult() {
    wx.setClipboardData({
      data: this.data.translatedText,
      success: () => {
        wx.showToast({
          title: '已复制',
          icon: 'success'
        })
      }
    })
  },
  
  // 分享翻译结果
  shareResult() {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },
  
  // 复制历史记录项
  copyHistoryItem(e) {
    const index = e.currentTarget.dataset.index;
    const item = this.data.translateHistory[index];
    
    wx.setClipboardData({
      data: item.result,
      success: () => {
        wx.showToast({
          title: '已复制',
          icon: 'success'
        })
      }
    });
    
    // 阻止事件冒泡
    return false;
  },

  // 清空历史记录
  clearHistory() {
    wx.showModal({
      title: '提示',
      content: '确定要清空所有记录吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({
            translateHistory: []
          })
          wx.setStorageSync('translateHistory', [])
        }
      }
    })
  },

  // 选择历史记录项
  selectHistoryItem(e) {
    const index = e.currentTarget.dataset.index
    const item = this.data.translateHistory[index]
    
    // 设置语言、文本和模型
    this.setData({
      sourceLanguage: this.data.languages.find(lang => lang.name === item.from),
      targetLanguage: this.data.languages.find(lang => lang.name === item.to),
      inputText: item.source,
      translatedText: item.result
    })
    
    // 如果历史记录中有模型信息，则设置当前模型
    if (item.model && item.modelValue) {
      this.setData({
        selectedModel: item.model,
        selectedModelValue: item.modelValue
      });
    }
  },

  // 阻止事件冒泡
  stopPropagation() {
    // Do nothing
  }
})