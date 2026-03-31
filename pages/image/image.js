const app = getApp()

Page({
  data: {
    imagePath: '',
    recognitionResult: '',
    imageHistory: [],
    showLoading: false,
    initialized: true,
    selectedModel: 'Qwen2.5VL 7B',
    selectedModelValue: 'qwen2.5vl:7b',
    processingProgress: 0,
    showProgressBar: false,
    customPrompt: '',
    isGuestMode: false
  },

  onLoad() {
    console.log('图像页面加载');
    
    try {
      // 检查是否是游客模式
      const isGuestMode = wx.getStorageSync('isGuestMode') || false;
      this.setData({ isGuestMode });
      
      // 初始化默认模型值
      this.setData({
        selectedModel: 'Qwen2.5VL 7B',
        selectedModelValue: 'qwen2.5vl:7b'
      });
      
      // 加载历史记录
      const history = wx.getStorageSync('imageHistory') || []
      this.setData({ imageHistory: history })
      
    } catch (error) {
      console.error('页面加载出错:', error);
      wx.showToast({
        title: '页面初始化错误',
        icon: 'none'
      });
    }
  },
  
  onShow() {
    // 每次显示页面时重新检查游客模式
    const isGuestMode = wx.getStorageSync('isGuestMode') || false;
    if (isGuestMode !== this.data.isGuestMode) {
      this.setData({ isGuestMode });
    }
  },

  // 切换模型 - 添加更多多模态模型选项
  switchModel() {
    // 多模态模型列表 - 只保留用户本地实际部署的模型
    const models = [
      {name: 'Qwen2.5VL 7B', value: 'qwen2.5vl:7b'},
      {name: 'LLaVA Latest', value: 'llava:latest'},
      {name: 'Bakllava 7B', value: 'bakllava:7b'},
      {name: 'Gemma 3', value: 'gemma3:12b'},
      {name: 'DeepSeek 8B', value: 'deepseek-r1:8b'},
      {name: 'DeepSeek 14B', value: 'deepseek-r1:14b'}
    ];
    
    // 获取当前选中的模型名称
    const currentName = this.data.selectedModel;
    const currentIndex = models.findIndex(m => m.name === currentName);
    const nextIndex = (currentIndex + 1) % models.length;
    
    // 更新选中的模型
    this.setData({ 
      selectedModel: models[nextIndex].name,
      selectedModelValue: models[nextIndex].value
    });
    
    wx.showToast({
      title: `已切换到${models[nextIndex].name}`,
      icon: 'none'
    });
  },

  // 选择图片
  chooseImage(e) {
    const source = e.currentTarget.dataset.source
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: [source],
      success: (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath
        this.setData({ 
          imagePath: tempFilePath,
          showLoading: false,
          processingProgress: 0,
          showProgressBar: true
        })
        
        // 模拟进度条增长
        this.startProgressSimulation();
        
        // 压缩图片后转换为Base64
        this.compressAndConvertImage(tempFilePath);
      }
    })
  },
  
  // 新增：压缩并转换图片
  compressAndConvertImage(imagePath) {
    // 先压缩图片
    wx.compressImage({
      src: imagePath,
      quality: 50, // 压缩质量，范围0-100
      success: (res) => {
        try {
          const fs = wx.getFileSystemManager();
          const base64 = fs.readFileSync(res.tempFilePath, 'base64');
          
          // 调用图像识别API
          this.recognizeImage(imagePath, base64);
        } catch (error) {
          console.error('转换压缩图片失败:', error);
          // 如果压缩失败，尝试直接使用原图
          this.convertImageToBase64(imagePath);
        }
      },
      fail: (error) => {
        console.error('压缩图片失败:', error);
        // 如果压缩失败，尝试直接使用原图
        this.convertImageToBase64(imagePath);
      }
    });
  },
  
  // 模拟进度条增长
  startProgressSimulation() {
    let progress = 0;
    const simulateProgress = () => {
      // 随机增加1-5%的进度
      progress += Math.random() * 4 + 1;
      
      // 确保不超过95%（最后5%留给实际完成）
      if (progress > 95) progress = 95;
      
      this.setData({ processingProgress: progress });
      
      // 继续模拟，直到接近完成
      if (progress < 95 && this.data.showProgressBar) {
        setTimeout(simulateProgress, 300);
      }
    };
    
    // 确保进度条显示
    this.setData({ showProgressBar: true });
    simulateProgress();
  },
  
  // 完成进度条
  completeProgress() {
    this.setData({ 
      processingProgress: 100
    });
    
    // 延迟隐藏进度条，让用户看到100%的状态
    setTimeout(() => {
      this.setData({ showProgressBar: false });
    }, 500);
  },
  
  // 将图片转换为Base64 (作为备用方法)
  convertImageToBase64(imagePath) {
    try {
      const fs = wx.getFileSystemManager();
      const base64 = fs.readFileSync(imagePath, 'base64');
      
      // 调用图像识别API
      this.recognizeImage(imagePath, base64);
    } catch (error) {
      console.error('转换图片失败:', error);
      wx.showToast({
        title: '图片处理失败',
        icon: 'error'
      });
      this.setData({ 
        showLoading: false,
        showProgressBar: false
      });
    }
  },
  
  // 识别图像 - 使用选择的模型
  recognizeImage(imagePath, imageBase64) {
    const modelName = this.data.selectedModel;
    const modelValue = this.data.selectedModelValue || 'gemma3:12b'; // 默认使用gemma3
    
    console.log(`开始图像识别请求 (使用 ${modelName})`);
    
    // 使用Ollama API进行图像识别
    const baseUrl = app.globalData.apiBaseUrl;
    
    // 使用通用API端点
    const ollamaUrl = `${baseUrl}/api/generate`;
    
    // 准备多模态格式的提示词
    const prompt = `<image>data:image/jpeg;base64,${imageBase64}</image>
    
请详细描述这张图片中包含的内容。使用中文回答。
请描述图片中的:
1. 主要物体/人物
2. 场景/背景
3. 颜色/氛围
4. 可见的文字/标志
5. 任何其他重要细节`;
    
    // 通用请求数据
    const requestData = {
      model: modelValue,
      prompt: prompt,
      stream: false,
      options: {
        temperature: 0.7,
        num_predict: 2000
      }
    };
    
    // 显示请求细节
    console.log(`请求API: ${ollamaUrl}`);
    console.log(`使用模型: ${modelValue}`);
    
    wx.request({
      url: ollamaUrl,
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: requestData,
      timeout: 60000,
      success: (res) => {
        try {
          console.log('Ollama API响应:', res.data);
          
          // 解析Ollama格式的响应
          let description = '';
          
          if (res.data && res.data.response) {
            description = res.data.response.trim();
          } else {
            throw new Error('无法解析识别结果');
          }
          
          // 处理响应中可能包含的"无法解析图片"信息
          if (description.includes('无法解析') || description.includes('无法识别') || description.includes('不能识别') || description.includes('无法处理图像')) {
            description = "识别结果: 当前模型无法直接解析图片内容。\n\n建议:\n1. 检查Ollama版本是否支持多模态\n2. 确认gemma3:12b模型支持图像识别\n3. 尝试使用其他支持图像的模型";
          }
          
          // 完成进度条
          this.completeProgress();
          
          // 更新识别结果
          this.setData({
            recognitionResult: description
          });
          
          // 保存到历史记录
          this.saveImageHistory(imagePath, description);
          
        } catch (error) {
          console.error('识别结果处理失败:', error);
          wx.showToast({
            title: '识别结果解析失败',
            icon: 'error'
          });
        }
      },
      fail: (error) => {
        console.error('Ollama API调用失败:', error);
        
        // 尝试重新检测服务连接
        app.checkOllamaService();
        
        wx.showModal({
          title: '连接错误',
          content: '无法连接到Ollama服务，请确保服务已启动: ' + (error.errMsg || '未知错误'),
          showCancel: false
        });
      },
      complete: () => {
        this.setData({ 
          showLoading: false
        });
      }
    });
  },

  // 预览图片
  previewImage() {
    if (this.data.imagePath) {
      wx.previewImage({
        urls: [this.data.imagePath]
      })
    }
  },

  // 复制识别结果
  copyResult() {
    wx.setClipboardData({
      data: this.data.recognitionResult,
      success: () => {
        wx.showToast({
          title: '已复制',
          icon: 'success'
        })
      }
    })
  },

  // 清空历史记录
  clearHistory() {
    // 如果是游客模式，不允许清空
    if (this.data.isGuestMode) {
      wx.showModal({
        title: '提示',
        content: '游客模式下不能清空历史记录',
        showCancel: false
      });
      return;
    }
    
    wx.showModal({
      title: '提示',
      content: '确定要清空所有记录吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({
            imageHistory: []
          })
          wx.setStorageSync('imageHistory', [])
        }
      }
    })
  },

  // 选择历史记录项
  selectHistoryItem(e) {
    const index = e.currentTarget.dataset.index
    const item = this.data.imageHistory[index]
    this.setData({
      imagePath: item.imagePath,
      recognitionResult: item.result
    })
  },
  
  // 复制历史记录项内容
  copyHistoryItem(e) {
    const index = e.currentTarget.dataset.index
    const item = this.data.imageHistory[index]
    
    wx.setClipboardData({
      data: item.result,
      success: () => {
        wx.showToast({
          title: '已复制',
          icon: 'success'
        })
      }
    })
    
    // 阻止事件冒泡
    return false;
  },
  
  // 重置图片和识别结果
  resetImage() {
    this.setData({
      imagePath: '',
      recognitionResult: '',
      customPrompt: ''
    })
  },
  
  // 翻译识别结果
  translateResult() {
    if (!this.data.recognitionResult) return;
    
    // 直接显示翻译功能已禁用的提示
    wx.showToast({
      title: '翻译功能已禁用',
      icon: 'none',
      duration: 2000
    });
    
    // 不再跳转到翻译页面
  },
  
  // 新增：更新自定义提示词
  updateCustomPrompt(e) {
    this.setData({
      customPrompt: e.detail.value
    });
  },
  
  // 新增：使用预设提示模板
  usePromptTemplate(e) {
    const prompt = e.currentTarget.dataset.prompt;
    this.setData({
      customPrompt: prompt
    });
  },
  
  // 新增：发送自定义分析请求 - 修改为使用压缩图片
  sendCustomAnalysis() {
    // 检查是否有图片和提示词
    if (!this.data.imagePath) {
      wx.showToast({
        title: '请先选择图片',
        icon: 'none'
      });
      return;
    }
    
    if (!this.data.customPrompt.trim()) {
      wx.showToast({
        title: '请输入分析要求',
        icon: 'none'
      });
      return;
    }
    
    // 显示加载状态
    this.setData({
      showLoading: false,
      processingProgress: 0,
      showProgressBar: true
    });
    
    // 启动进度条模拟
    this.startProgressSimulation();
    
    // 压缩并转换图片为Base64
    wx.compressImage({
      src: this.data.imagePath,
      quality: 50,
      success: (res) => {
        try {
          const fs = wx.getFileSystemManager();
          const imageBase64 = fs.readFileSync(res.tempFilePath, 'base64');
          
          // 调用自定义分析API
          this.analyzeImageWithCustomPrompt(this.data.imagePath, imageBase64);
        } catch (error) {
          console.error('处理压缩图片失败:', error);
          // 如果压缩失败，尝试直接使用原图
          const fs = wx.getFileSystemManager();
          const imageBase64 = fs.readFileSync(this.data.imagePath, 'base64');
          this.analyzeImageWithCustomPrompt(this.data.imagePath, imageBase64);
        }
      },
      fail: (error) => {
        console.error('压缩图片失败:', error);
        // 如果压缩失败，尝试直接使用原图
        try {
          const fs = wx.getFileSystemManager();
          const imageBase64 = fs.readFileSync(this.data.imagePath, 'base64');
          this.analyzeImageWithCustomPrompt(this.data.imagePath, imageBase64);
        } catch (err) {
          console.error('处理图片失败:', err);
          this.setData({
            showLoading: false,
            showProgressBar: false
          });
          
          wx.showToast({
            title: '图片处理失败',
            icon: 'error'
          });
        }
      }
    });
  },
  
  // 新增：使用自定义提示词分析图像 - 使用选择的模型
  analyzeImageWithCustomPrompt(imagePath, imageBase64) {
    if (!this.data.customPrompt.trim()) {
      wx.showToast({
        title: '请输入分析提示词',
        icon: 'none'
      });
      return;
    }
    
    const modelName = this.data.selectedModel;
    const modelValue = this.data.selectedModelValue || 'gemma3:12b'; // 默认使用gemma3
    
    this.setData({ 
      showLoading: false,
      processingProgress: 0,
      showProgressBar: true
    });
    
    // 模拟进度条增长
    this.startProgressSimulation();
    
    console.log(`开始自定义图像分析请求 (使用 ${modelName})`);
    
    // 使用Ollama API进行图像识别
    const baseUrl = app.globalData.apiBaseUrl;
    const ollamaUrl = `${baseUrl}/api/generate`;
    
    // 准备多模态格式的自定义提示词
    const customPrompt = this.data.customPrompt.trim();
    const prompt = `<image>data:image/jpeg;base64,${imageBase64}</image>
    
${customPrompt}`;
    
    // 通用请求数据
    const requestData = {
      model: modelValue,
      prompt: prompt,
      stream: false,
      options: {
        temperature: 0.7,
        num_predict: 2000
      }
    };
    
    // 显示请求细节
    console.log(`请求API: ${ollamaUrl}`);
    console.log(`使用模型: ${modelValue}`);
    
    wx.request({
      url: ollamaUrl,
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: requestData,
      timeout: 60000,
      success: (res) => {
        try {
          console.log('Ollama API响应:', res.data);
          
          // 解析Ollama格式的响应
          let analysis = '';
          
          if (res.data && res.data.response) {
            analysis = res.data.response.trim();
          } else {
            throw new Error('无法解析分析结果');
          }
          
          // 处理响应中可能包含的"无法解析图片"信息
          if (analysis.includes('无法解析') || analysis.includes('无法识别') || analysis.includes('不能识别') || analysis.includes('无法处理图像')) {
            analysis = "分析结果: 当前模型无法直接解析图片内容。\n\n建议:\n1. 检查Ollama版本是否支持多模态\n2. 确认gemma3:12b模型支持图像分析\n3. 尝试使用其他支持图像的模型";
          }
          
          // 完成进度条
          this.completeProgress();
          
          // 更新识别结果
          this.setData({
            recognitionResult: analysis
          });
          
          // 保存到历史记录，包含自定义提示词
          this.saveImageHistory(imagePath, analysis);
          
        } catch (error) {
          console.error('分析结果处理失败:', error);
          wx.showToast({
            title: '分析结果解析失败',
            icon: 'error'
          });
        }
      },
      fail: (error) => {
        console.error('Ollama API调用失败:', error);
        
        // 尝试重新检测服务连接
        app.checkOllamaService();
        
        wx.showModal({
          title: '连接错误',
          content: '无法连接到Ollama服务，请确保服务已启动: ' + (error.errMsg || '未知错误'),
          showCancel: false
        });
      },
      complete: () => {
        this.setData({ 
          showLoading: false
        });
      }
    });
  },
  
  // 格式化时间
  formatTime(date) {
    const hour = date.getHours()
    const minute = date.getMinutes()
    
    return `${hour < 10 ? '0' + hour : hour}:${minute < 10 ? '0' + minute : minute}`
  },

  // 保存图像识别历史记录
  saveImageHistory(imagePath, description) {
    // 如果是游客模式，不保存记录
    if (this.data.isGuestMode) {
      console.log('游客模式，不保存图像识别记录');
      return;
    }
    
    // 检查是否有app全局方法
    const app = getApp();
    if (app && app.canSaveHistory && !app.canSaveHistory()) {
      console.log('根据全局设置，不保存图像识别记录');
      return;
    }
    
    try {
      const now = new Date();
      const timestamp = now.getTime();
      
      // 获取当前使用的模型名称
      const modelName = this.data.selectedModel || 'LLaVA Latest';
      const modelValue = this.data.selectedModelValue || 'llava:latest';
      
      // 创建新的历史记录
      const newHistory = [{
        id: `image_${timestamp}`,
        imagePath: imagePath,
        result: description,
        time: this.formatTime(now),
        timestamp: timestamp,
        model: modelName,
        modelValue: modelValue, // 添加模型值
        query: '识别图片内容', // 默认查询文本
        content: '识别图片内容'
      }, ...this.data.imageHistory].slice(0, 10); // 只保留最近10条记录
      
      // 更新状态和本地存储
      this.setData({ imageHistory: newHistory });
      wx.setStorageSync('imageHistory', newHistory);
      
      console.log(`图像识别记录已保存 (使用模型: ${modelName})`);
    } catch (error) {
      console.error('保存图像识别记录失败:', error);
    }
  }
}) 