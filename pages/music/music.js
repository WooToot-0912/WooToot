// pages/music/music.js
const config = require('../../config');

Page({
  data: {
    keyword: '',
    searchResults: [],
    currentSong: null,
    isPlaying: false,
    progress: 0,
    duration: 0,
    loading: false,
    history: [],
    apiBaseUrl: config.musicApiBaseUrl, // 使用音乐服务的API地址
    platform: 'local', // 默认使用本地平台
    playMode: 'preview', // 默认使用预览模式，避免文件过大
    showFullPlayer: false, // 是否显示全屏播放器
    isSeeking: false // 是否正在拖动进度条
  },
  
  // 辅助函数：安全拼接URL，防止/api重复
  joinUrl(base, path) {
    return config.joinUrl(base, path);
  },
  
  onLoad() {
    // 从本地存储加载历史记录
    const history = wx.getStorageSync('musicHistory') || [];
    this.setData({ history });
    
    // 初始化音频播放器 - 使用更可靠的后台音频播放器
    this.initAudioPlayer();
    
    console.log('音乐页面加载完成');
    console.log('使用音乐API地址:', this.data.apiBaseUrl);
    
    // 测试API连接
    this.testApiConnection();
  },
  
  // 初始化音频播放器
  initAudioPlayer() {
    // 使用背景音频播放器替代普通播放器，增强真机兼容性
    if (!this.backgroundAudioManager) {
      const backgroundAudioManager = wx.getBackgroundAudioManager();
      this.backgroundAudioManager = backgroundAudioManager;
      
      // 设置监听器
      backgroundAudioManager.onPlay(() => {
        console.log('背景音频开始播放');
        this.setData({ isPlaying: true });
        this.startProgressTimer();
      });
      
      backgroundAudioManager.onPause(() => {
        console.log('背景音频暂停播放');
        this.setData({ isPlaying: false });
        this.clearProgressTimer();
      });
      
      backgroundAudioManager.onStop(() => {
        console.log('背景音频停止播放');
        this.setData({ isPlaying: false, progress: 0 });
        this.clearProgressTimer();
      });
      
      backgroundAudioManager.onEnded(() => {
        console.log('背景音频播放结束');
        this.setData({ isPlaying: false, progress: 0 });
        this.clearProgressTimer();
      });
      
      backgroundAudioManager.onTimeUpdate(() => {
        // 更新进度，但仅在不拖动进度条时更新
        if (!this.data.isSeeking) {
          this.setData({
            progress: backgroundAudioManager.currentTime || 0,
            duration: backgroundAudioManager.duration || 0
          });
        }
      });
      
      backgroundAudioManager.onError((err) => {
        console.error('背景音频播放错误:', err);
        wx.showToast({
          title: '音频播放失败: ' + (err.errMsg || '未知错误'),
          icon: 'none',
          duration: 3000
        });
        this.setData({ isPlaying: false });
        this.clearProgressTimer();
      });
      
      console.log('背景音频播放器初始化完成');
    }
    
    // 仍然保留内部播放器用于兼容性
    if (!this.audioContext) {
      this.audioContext = wx.createInnerAudioContext();
      this.setupAudioListeners();
    }
  },
  
  // 测试API连接
  testApiConnection() {
    const url = this.joinUrl(this.data.apiBaseUrl, '/api/status');
    console.log('测试API连接URL:', url);
    
    wx.request({
      url: url,
      success: (res) => {
        console.log('API状态检查成功:', res.data);
      },
      fail: (err) => {
        console.error('API状态检查失败:', err);
        // 显示错误提示
        wx.showToast({
          title: 'API连接失败，请检查网络',
          icon: 'none',
          duration: 3000
        });
      }
    });
  },
  
  onShow() {
    // 页面显示时检查播放状态
    if (this.audioContext && !this.audioContext.paused) {
      this.startProgressTimer();
    }
  },
    
  onHide() {
    this.clearProgressTimer();
  },
    
  onUnload() {
    this.clearProgressTimer();
    if (this.audioContext) {
      this.audioContext.stop();
      this.audioContext.destroy();
      this.audioContext = null;
    }
  },
  
  // 设置音频监听器
  setupAudioListeners() {
    this.audioContext.onPlay(() => {
      console.log('开始播放音频');
      this.setData({ isPlaying: true });
      this.startProgressTimer();
    });
    
    this.audioContext.onPause(() => {
      console.log('暂停播放音频');
      this.setData({ isPlaying: false });
      this.clearProgressTimer();
    });
    
    this.audioContext.onStop(() => {
      console.log('停止播放音频');
      this.setData({ isPlaying: false });
      this.clearProgressTimer();
    });
    
    this.audioContext.onEnded(() => {
      console.log('音频播放结束');
      this.setData({
        isPlaying: false,
        progress: 0
      });
      this.clearProgressTimer();
    });
      
    this.audioContext.onError((err) => {
      console.error('音频播放错误:', err);
      wx.showToast({
        title: '音频播放失败',
        icon: 'none'
      });
    });
      
    this.audioContext.onCanplay(() => {
      console.log('音频就绪,可以播放');
      console.log('音频时长:', this.audioContext.duration);
      this.setData({
        duration: this.audioContext.duration || 0
      });
    });
    
    this.audioContext.onTimeUpdate(() => {
      // 更新进度，但仅在不拖动进度条时更新
      if (!this.data.isSeeking) {
        this.setData({
          progress: this.audioContext.currentTime || 0,
          duration: this.audioContext.duration || 0
        });
      }
    });
  },
    
  // 进度更新定时器
  startProgressTimer() {
    this.clearProgressTimer();
    this.progressTimer = setInterval(() => {
      if (this.audioContext && !this.data.isSeeking) {
        this.setData({
          progress: this.audioContext.currentTime || 0
        });
      }
    }, 1000);
  },
    
  clearProgressTimer() {
    if (this.progressTimer) {
      clearInterval(this.progressTimer);
      this.progressTimer = null;
    }
  },
  
  // 滚动条事件处理
  onSliderChanging(e) {
    // 正在拖动滚动条时，设置isSeeking为true，暂停进度自动更新
    this.setData({
      isSeeking: true,
      progress: e.detail.value
    });
  },
  
  onSliderChange(e) {
    const position = e.detail.value;
    
    // 更新进度
    this.setData({
      progress: position,
      isSeeking: false
    });
    
    // 根据当前使用的播放器设置播放进度
    if (this.backgroundAudioManager && this.data.currentSong) {
      this.backgroundAudioManager.seek(position);
    } else if (this.audioContext) {
      this.audioContext.seek(position);
    }
    
    // 如果当前不在播放，自动开始播放
    if (!this.data.isPlaying) {
      this.togglePlay();
    }
  },
  
  // 切换全屏播放器
  showFullPlayer() {
    this.setData({
      showFullPlayer: true
    });
  },
  
  hideFullPlayer() {
    this.setData({
      showFullPlayer: false
    });
  },
  
  // 切换播放模式
  togglePlayMode() {
    const modes = ['preview', 'full'];
    const currentMode = this.data.playMode;
    const nextMode = currentMode === 'preview' ? 'full' : 'preview';
    
    this.setData({
      playMode: nextMode
    });
    
    wx.showToast({
      title: nextMode === 'preview' ? '预览模式' : '完整模式',
      icon: 'none'
    });
    
    // 如果当前正在播放，重新加载当前歌曲
    if (this.data.currentSong && this.data.isPlaying) {
      this.playSong(null, this.data.currentSong);
    }
  },
    
  // 输入框内容变化
  onInputChange(e) {
    this.setData({
      keyword: e.detail.value
    });
  },
  
  // 切换音乐平台
  togglePlatform() {
    const platforms = ['gequbao', 'kugou', 'netease'];
    const currentIndex = platforms.indexOf(this.data.platform);
    const nextIndex = (currentIndex + 1) % platforms.length;
    const nextPlatform = platforms[nextIndex];
    
    this.setData({
      platform: nextPlatform
    });
    
    // 显示平台切换提示
    let platformName = '歌曲宝音乐';
    if (nextPlatform === 'kugou') platformName = '酷狗音乐';
    if (nextPlatform === 'netease') platformName = '网易云音乐';
    
    wx.showToast({
      title: `已切换到${platformName}`,
      icon: 'none'
    });
  },
    
  // 搜索音乐
  search() {
    const keyword = this.data.keyword.trim();
    if (!keyword) {
      wx.showToast({
        title: '请输入搜索关键词',
        icon: 'none'
      });
      return;
    }

    // 添加到历史记录
    this.addToHistory(keyword);
    
    // 显示加载中
    this.setData({ loading: true });
    
    console.log('发送搜索请求:', this.joinUrl(this.data.apiBaseUrl, '/api/search'));
    
    // 发起请求
    wx.request({
      url: this.joinUrl(this.data.apiBaseUrl, '/api/search'),
      data: {
        keyword: keyword,
        platform: this.data.platform
      },
      success: res => {
        console.log('搜索结果:', res);
        if (res.statusCode === 200 && res.data && res.data.data) {
          this.setData({
            searchResults: res.data.data
          });
          
          // 如果没有结果，显示提示
          if (res.data.data.length === 0) {
            wx.showToast({
              title: '未找到相关音乐',
              icon: 'none'
            });
          }
        } else {
          console.error('搜索结果解析错误:', res);
          wx.showToast({
            title: '搜索失败，请重试',
            icon: 'none'
          });
        }
      },
      fail: err => {
        console.error('搜索失败:', keyword, err);
        wx.showToast({
          title: '搜索服务连接失败',
          icon: 'none',
          duration: 2000
        });
        
        // 检查是否是API地址问题
        wx.showModal({
          title: '音乐服务未启动',
          content: '请确保本地音乐服务已启动，并检查config.js中的musicApiBaseUrl配置是否正确。详情请查看README_MUSIC.md',
          showCancel: false
        });
      },
      complete: () => {
        this.setData({ loading: false });
      }
    });
  },
    
  // 保存搜索历史
  saveSearchHistory(keyword) {
    let history = this.data.history;
    history = history.filter(item => item !== keyword);
    history.unshift(keyword);
    if (history.length > 10) {
      history = history.slice(0, 10);
    }
    
    this.setData({ history });
    wx.setStorageSync('musicHistory', history);
  },
    
  // 清除历史记录
  clearHistory() {
    wx.showModal({
      title: '提示',
      content: '确定要清除搜索历史吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({ history: [] });
          wx.setStorageSync('musicHistory', []);
        }
      }
    });
  },
    
  // 点击历史记录
  onHistoryTap(e) {
    const keyword = e.currentTarget.dataset.keyword;
    this.setData({ keyword });
    this.search();
  },
  
  // 播放音乐
  playSong(e, directSong) {
    let index;
    let song;
    
    if (directSong) {
      // 直接传入歌曲对象
      song = directSong;
    } else {
      // 从点击事件中获取歌曲索引
      index = e.currentTarget.dataset.index;
      song = this.data.searchResults[index];
    }
    
    if (!song) {
      console.error('未找到要播放的歌曲');
      return;
    }
    
    // 修复封面URL，使用本地默认图片
    let coverUrl = '/images/music-cover.png'; // 使用本地默认图片
    
    // 更新当前歌曲，同时设置处理过的封面URL
    this.setData({
      currentSong: {
        ...song,
        cover_url: coverUrl
      },
      showFullPlayer: true // 自动显示全屏播放器
    });
    
    // 根据平台和播放模式获取播放URL
    const baseUrl = this.data.apiBaseUrl;
    // 使用api/play路径，这是已经确认工作的路径
    const playUrl = this.joinUrl(baseUrl, `/api/play/${song.id}`);
    
    console.log('播放URL:', playUrl);
    
    // 使用背景音频管理器播放
    if (this.backgroundAudioManager) {
      this.backgroundAudioManager.title = song.title || '未知歌曲';
      this.backgroundAudioManager.singer = song.singer || '未知歌手';
      this.backgroundAudioManager.coverImgUrl = coverUrl;
      
      // 设置音频源前停止当前播放
      this.backgroundAudioManager.stop();
      
      // 延迟设置src，避免可能的问题
      setTimeout(() => {
        try {
          this.backgroundAudioManager.src = playUrl;
          console.log('成功设置背景音频源');
          
          this.setData({
            isPlaying: true,
            progress: 0,
            duration: 0
          });
        } catch (err) {
          console.error('设置音频源出错:', err);
          wx.showToast({
            title: '播放失败，请稍后再试',
            icon: 'none'
          });
        }
      }, 100);
    } else {
      // 备用方案：使用内部音频上下文
      try {
        this.audioContext.stop();
        this.audioContext.title = song.title;
        this.audioContext.singer = song.singer;
        this.audioContext.coverImgUrl = coverUrl;
        this.audioContext.src = playUrl;
        this.audioContext.play();
        
        this.setData({
          isPlaying: true,
          progress: 0,
          duration: 0
        });
      } catch (err) {
        console.error('使用内部音频上下文播放出错:', err);
        wx.showToast({
          title: '播放失败，请稍后再试',
          icon: 'none'
        });
      }
    }
  },
  
  // 检查音频文件大小
  checkAudioSize(url, callback) {
    wx.request({
      url: url,
      method: 'HEAD',
      success: (res) => {
        const contentLength = res.header['Content-Length'] || res.header['content-length'] || 0;
        console.log('音频文件大小:', contentLength);
        callback(parseInt(contentLength));
      },
      fail: (err) => {
        console.error('获取音频文件大小失败:', err);
        callback(0); // 失败时假设文件大小为0
      }
    });
  },
  
  // 切换播放/暂停
  togglePlay() {
    if (!this.data.currentSong) {
      wx.showToast({
        title: '请先选择歌曲',
        icon: 'none'
      });
      return;
    }
    
    if (this.data.isPlaying) {
      // 暂停播放
      if (this.backgroundAudioManager) {
        this.backgroundAudioManager.pause();
      } else if (this.audioContext) {
        this.audioContext.pause();
      }
    } else {
      // 继续播放
      if (this.backgroundAudioManager) {
        this.backgroundAudioManager.play();
      } else if (this.audioContext) {
        this.audioContext.play();
      }
    }
  },
  
  // 停止播放
  stopMusic() {
    if (this.backgroundAudioManager) {
      this.backgroundAudioManager.stop();
    } else if (this.audioContext) {
      this.audioContext.stop();
    }
    
    this.setData({
      isPlaying: false,
      progress: 0,
      showFullPlayer: false // 停止播放时隐藏全屏播放器
    });
    
    this.clearProgressTimer();
  },
  
  // 格式化时间
  formatTime(seconds) {
    seconds = Math.floor(seconds || 0);
    let minutes = Math.floor(seconds / 60);
    seconds = seconds % 60;
    return `${minutes < 10 ? '0' + minutes : minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
  },

  // 添加到历史记录
  addToHistory(keyword) {
    let history = this.data.history;
    history = history.filter(item => item !== keyword);
    history.unshift(keyword);
    if (history.length > 10) {
      history = history.slice(0, 10);
    }
    
    this.setData({ history });
    wx.setStorageSync('musicHistory', history);
  }
})