/**
 * 全局配置文件
 * 此文件仅作为兼容旧代码的入口，实际配置已移至 utils/config-manager.js
 */

// 导入配置管理器
const configManager = require('./utils/config-manager');

// 获取完整配置
const config = configManager.getConfig();

// 导出配置（兼容旧代码）
module.exports = {
  // API服务地址
  apiBaseUrl: config.apiBaseUrl,
  
  // 音乐服务API地址
  musicApiBaseUrl: config.musicApiBaseUrl,
  
  // AI模型配置
  modelConfig: config.modelConfig,
  
  // 备选模型
  fallbackModels: config.fallbackModels,
  
  // 图像识别模型配置
  imageModelConfig: config.imageModelConfig,
  
  // 请求配置
  requestConfig: config.requestConfig,
  
  // 语音配置
  voiceConfig: config.voiceConfig,
  
  // 工具函数：安全拼接URL路径
  joinUrl: configManager.joinUrl
};