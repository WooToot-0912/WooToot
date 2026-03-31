const app = getApp();
// Import the helper instead of direct plugin
const siHelper = require('../../utils/si-helper');

Page({
  data: {
    recording: false,
    recordStatus: '按住说话',
    voiceList: [],
    currentTranscript: '',
    showLoading: false,
    recognitionMethod: 'local', // 默认使用本地模拟
    recognitionMethods: [
      { id: 'local', name: '本地模拟' }
    ]
  },

  onLoad() {
    // 初始化录音管理器
    this.recorderManager = wx.getRecorderManager()
    
    // 监听录音结束事件
    this.recorderManager.onStop((res) => {
      this.setData({ 
        recording: false,
        recordStatus: '按住说话',
        showLoading: true 
      })
      
      const { tempFilePath, duration } = res
      console.log('录音文件：', tempFilePath)
      console.log('录音时长：', duration)

      // 检查录音时长是否太短
      if (duration < 500) {
        this.setData({ showLoading: false })
        wx.showToast({
          title: '录音时间太短',
          icon: 'none'
        })
        return
      }

      // 调用语音识别API
      this.recognizeVoice(tempFilePath)
    })

    // 监听录音错误事件
    this.recorderManager.onError((res) => {
      console.error('录音错误：', res)
      this.setData({
        recording: false,
        recordStatus: '按住说话',
        showLoading: false
      })
      wx.showToast({
        title: '录音失败',
        icon: 'error'
      })
    })

    // 加载历史记录
    const history = wx.getStorageSync('voiceHistory') || []
    this.setData({ voiceList: history })
    
    // 加载识别方式配置
    const method = wx.getStorageSync('recognitionMethod') || 'local'
    this.setData({ recognitionMethod: method })
  },

  // 开始录音
  startRecord() {
    // 检查录音权限
    wx.authorize({
      scope: 'scope.record',
      success: () => {
        this.setData({
          recording: true,
          recordStatus: '松开结束'
        })
        
        this.recorderManager.start({
          duration: 60000, // 最长录音时间，单位ms
          sampleRate: 16000, // 采样率
          numberOfChannels: 1, // 录音通道数
          encodeBitRate: 48000, // 编码码率
          format: 'mp3' // 音频格式
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

  // 结束录音
  stopRecord() {
    if (this.data.recording) {
      this.recorderManager.stop()
    }
  },

  // 清空记录
  clearHistory() {
    wx.showModal({
      title: '提示',
      content: '确定要清空所有记录吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({
            voiceList: [],
            currentTranscript: ''
          })
          wx.setStorageSync('voiceHistory', [])
        }
      }
    })
  },

  copyText() {
    wx.setClipboardData({
      data: this.data.currentTranscript,
      success: () => {
        wx.showToast({
          title: '已复制',
          icon: 'success'
        })
      }
    })
  },

  clearText() {
    this.setData({ currentTranscript: '' })
  },

  // 切换语音识别方式
  switchRecognitionMethod() {
    const methods = this.data.recognitionMethods;
    const currentIndex = methods.findIndex(m => m.id === this.data.recognitionMethod);
    const nextIndex = (currentIndex + 1) % methods.length;
    const nextMethod = methods[nextIndex].id;
    
    this.setData({ recognitionMethod: nextMethod });
    wx.setStorageSync('recognitionMethod', nextMethod);
    
    wx.showToast({
      title: `已切换到${methods[nextIndex].name}`,
      icon: 'none'
    });
  },

  // 调用语音识别API
  recognizeVoice(tempFilePath) {
    try {
      console.log('开始识别语音:', tempFilePath);
      
      // 使用模拟的微信语音识别
      this.recognizeWithWechat(tempFilePath);
    } catch (error) {
      console.error('语音识别调用失败:', error);
      
      // 使用默认模拟结果
      const transcript = "语音识别调用失败，使用默认结果。";
      const now = new Date();
      
      this.setData({
        voiceList: [{
          text: transcript,
          time: this.formatTime(now)
        }, ...this.data.voiceList],
        currentTranscript: transcript,
        showLoading: false
      });
      
      // 保存到本地存储
      wx.setStorageSync('voiceHistory', this.data.voiceList);
      
      wx.showToast({
        title: '使用模拟数据',
        icon: 'none',
        duration: 1500
      });
    }
  },
  
  // 使用微信内置语音识别
  recognizeWithWechat(tempFilePath) {
    console.log('使用模拟的微信语音识别');
    
    try {
      // 使用辅助函数获取插件API
      const manager = siHelper.getRecordManager();
      
      // 设置回调
      manager.onStop = (res) => {
        console.log('模拟识别结束:', res);
        if (res.result) {
          const now = new Date();
          this.setData({
            voiceList: [{
              text: res.result,
              time: this.formatTime(now)
            }, ...this.data.voiceList],
            currentTranscript: res.result,
            showLoading: false
          });
          
          // 保存到本地存储
          wx.setStorageSync('voiceHistory', this.data.voiceList);
        } else {
          wx.showToast({
            title: '未能识别语音',
            icon: 'none'
          });
          this.setData({ showLoading: false });
        }
      };
      
      // 设置错误回调
      manager.onError = (res) => {
        console.error('模拟识别错误:', res);
        wx.showToast({
          title: '语音识别失败',
          icon: 'none'
        });
        this.setData({ showLoading: false });
      };
      
      // 直接模拟识别结果
      setTimeout(() => {
        manager.onStop({
          result: "This is a simulated voice recognition result."
        });
      }, 1000);
    } catch (error) {
      console.error('模拟插件调用失败:', error);
      
      // 使用默认模拟结果
      const transcript = "Mock plugin call failed, using default result.";
      const now = new Date();
      
      this.setData({
        voiceList: [{
          text: transcript,
          time: this.formatTime(now)
        }, ...this.data.voiceList],
        currentTranscript: transcript,
        showLoading: false
      });
      
      // 保存到本地存储
      wx.setStorageSync('voiceHistory', this.data.voiceList);
    }
  },
  
  // 使用百度语音识别API
  recognizeWithBaidu(tempFilePath) {
    // 百度语音识别API配置
    const baiduConfig = {
      apiKey: '', // 请填入您的百度API Key
      secretKey: '', // 请填入您的百度Secret Key
      cuid: wx.getSystemInfoSync().brand + wx.getSystemInfoSync().model,
      url: 'https://vop.baidu.com/server_api'
    };
    
    // 检查API密钥
    if (!baiduConfig.apiKey || !baiduConfig.secretKey) {
      console.warn('百度API密钥未配置，使用微信语音识别');
      
      wx.showToast({
        title: '百度API未配置，使用微信识别',
        icon: 'none',
        duration: 2000
      });
      
      // 切换回微信识别
      this.setData({ 
        recognitionMethod: 'wx',
        showLoading: false
      });
      wx.setStorageSync('recognitionMethod', 'wx');
      
      // 使用微信识别重试
      setTimeout(() => {
        this.recognizeWithWechat(tempFilePath);
      }, 1000);
      
      return;
    }

    // 获取访问令牌
    this.getBaiduToken(baiduConfig.apiKey, baiduConfig.secretKey).then(token => {
      // 读取音频文件并转换为Base64
      wx.getFileSystemManager().readFile({
        filePath: tempFilePath,
        encoding: 'base64',
        success: (res) => {
          const base64Data = res.data;
          
          // 调用百度语音识别API
          wx.request({
            url: `${baiduConfig.url}?cuid=${baiduConfig.cuid}&token=${token}`,
            method: 'POST',
            data: {
              format: 'pcm',
              rate: 16000,
              channel: 1,
              cuid: baiduConfig.cuid,
              token: token,
              speech: base64Data,
              len: base64Data.length
            },
            header: {
              'Content-Type': 'application/json'
            },
            success: (res) => {
              console.log('百度识别结果：', res.data);
              
              if (res.data && res.data.result && res.data.result.length > 0) {
                const result = res.data.result[0];
                const now = new Date();
                
                this.setData({
                  voiceList: [{
                    text: result,
                    time: this.formatTime(now)
                  }, ...this.data.voiceList],
                  currentTranscript: result,
                  showLoading: false
                });
                
                // 保存到本地存储
                wx.setStorageSync('voiceHistory', this.data.voiceList);
              } else {
                wx.showToast({
                  title: '未能识别语音',
                  icon: 'none'
                });
                this.setData({ showLoading: false });
              }
            },
            fail: (err) => {
              console.error('百度API调用失败：', err);
              
              wx.showToast({
                title: '识别失败，请重试',
                icon: 'none'
              });
              
              this.setData({ showLoading: false });
            }
          });
        },
        fail: (err) => {
          console.error('读取文件失败：', err);
          this.setData({ showLoading: false });
        }
      });
    }).catch(err => {
      console.error('获取百度token失败：', err);
      
      wx.showToast({
        title: '连接百度服务失败',
        icon: 'none'
      });
      
      this.setData({ showLoading: false });
    });
  },
  
  // 获取百度API访问令牌
  getBaiduToken(apiKey, secretKey) {
    return new Promise((resolve, reject) => {
      // 先尝试从缓存获取token
      const cachedToken = wx.getStorageSync('baiduToken');
      const tokenExpiry = wx.getStorageSync('baiduTokenExpiry');
      
      // 如果token有效且未过期，直接使用
      if (cachedToken && tokenExpiry && new Date().getTime() < tokenExpiry) {
        resolve(cachedToken);
        return;
      }
      
      // 否则重新获取token
      wx.request({
        url: `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${apiKey}&client_secret=${secretKey}`,
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        success: (res) => {
          if (res.data && res.data.access_token) {
            const token = res.data.access_token;
            const expiresIn = res.data.expires_in || 2592000; // 默认30天
            
            // 缓存token和过期时间
            wx.setStorageSync('baiduToken', token);
            wx.setStorageSync('baiduTokenExpiry', new Date().getTime() + expiresIn * 1000);
            
            resolve(token);
          } else {
            reject(new Error('获取百度token失败'));
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
  },
  
  // 翻译文本
  translateText() {
    if (!this.data.currentTranscript) return;
    
    // 显示禁用消息
    wx.showToast({
      title: '翻译功能已禁用',
      icon: 'none',
      duration: 2000
    });
    
    // 不再跳转到翻译页面
  },
  
  // 选择历史记录项
  selectHistoryItem(e) {
    const index = e.currentTarget.dataset.index;
    const item = this.data.voiceList[index];
    
    this.setData({
      currentTranscript: item.text
    });
  },
  
  // 复制历史记录项
  copyHistoryItem(e) {
    const index = e.currentTarget.dataset.index;
    const item = this.data.voiceList[index];
    
    wx.setClipboardData({
      data: item.text,
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

  formatTime(date) {
    const hour = date.getHours()
    const minute = date.getMinutes()
    
    return `${hour < 10 ? '0' + hour : hour}:${minute < 10 ? '0' + minute : minute}`
  }
}) 