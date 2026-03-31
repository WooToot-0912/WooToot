/**
 * 安全工具类
 * 提供数据加密、输入过滤、安全验证等功能
 */

class Security {
  constructor() {
    this.sensitiveKeys = ['password', 'token', 'secret', 'key', 'auth'];
  }

  /**
   * 简单的字符串加密（基于Base64，仅用于非敏感数据）
   */
  encode(str) {
    try {
      return wx.arrayBufferToBase64(
        new TextEncoder().encode(str).buffer
      );
    } catch (error) {
      console.warn('编码失败:', error);
      return str;
    }
  }

  /**
   * 简单的字符串解密
   */
  decode(encodedStr) {
    try {
      const buffer = wx.base64ToArrayBuffer(encodedStr);
      return new TextDecoder().decode(buffer);
    } catch (error) {
      console.warn('解码失败:', error);
      return encodedStr;
    }
  }

  /**
   * 过滤敏感信息
   */
  filterSensitiveData(obj) {
    if (typeof obj !== 'object' || obj === null) {
      return obj;
    }

    const filtered = Array.isArray(obj) ? [] : {};

    for (const [key, value] of Object.entries(obj)) {
      const lowerKey = key.toLowerCase();
      const isSensitive = this.sensitiveKeys.some(sensitiveKey => 
        lowerKey.includes(sensitiveKey)
      );

      if (isSensitive) {
        filtered[key] = '***';
      } else if (typeof value === 'object' && value !== null) {
        filtered[key] = this.filterSensitiveData(value);
      } else {
        filtered[key] = value;
      }
    }

    return filtered;
  }

  /**
   * 输入内容过滤和清理
   */
  sanitizeInput(input) {
    if (typeof input !== 'string') {
      return input;
    }

    // 移除潜在的恶意脚本标签
    let sanitized = input.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    
    // 移除其他潜在危险的HTML标签
    sanitized = sanitized.replace(/<[^>]*>/g, '');
    
    // 转义特殊字符
    sanitized = sanitized
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');

    // 限制长度
    if (sanitized.length > 10000) {
      sanitized = sanitized.substring(0, 10000) + '...';
    }

    return sanitized.trim();
  }

  /**
   * 验证URL安全性
   */
  isUrlSafe(url) {
    if (typeof url !== 'string') {
      return false;
    }

    // 检查协议
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return false;
    }

    // 检查是否包含危险字符
    const dangerousPatterns = [
      /javascript:/i,
      /data:/i,
      /vbscript:/i,
      /file:/i,
      /<script/i,
      /onload=/i,
      /onerror=/i
    ];

    return !dangerousPatterns.some(pattern => pattern.test(url));
  }

  /**
   * 生成随机字符串
   */
  generateRandomString(length = 16) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    return result;
  }

  /**
   * 验证文件类型安全性
   */
  isFileTypeSafe(filename, allowedTypes = []) {
    if (typeof filename !== 'string') {
      return false;
    }

    const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
    
    // 危险的文件扩展名
    const dangerousExtensions = [
      '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
      '.app', '.deb', '.pkg', '.dmg', '.iso', '.msi', '.run', '.sh'
    ];

    if (dangerousExtensions.includes(extension)) {
      return false;
    }

    // 如果指定了允许的类型，检查是否在允许列表中
    if (allowedTypes.length > 0) {
      return allowedTypes.includes(extension);
    }

    return true;
  }

  /**
   * 检查请求频率限制
   */
  checkRateLimit(key, maxRequests = 10, timeWindow = 60000) {
    const now = Date.now();
    const storageKey = `rate_limit_${key}`;
    
    try {
      let requestLog = wx.getStorageSync(storageKey) || [];
      
      // 清理过期的请求记录
      requestLog = requestLog.filter(timestamp => now - timestamp < timeWindow);
      
      // 检查是否超过限制
      if (requestLog.length >= maxRequests) {
        return {
          allowed: false,
          remainingTime: timeWindow - (now - requestLog[0])
        };
      }
      
      // 添加当前请求
      requestLog.push(now);
      wx.setStorageSync(storageKey, requestLog);
      
      return {
        allowed: true,
        remainingRequests: maxRequests - requestLog.length
      };
    } catch (error) {
      console.warn('频率限制检查失败:', error);
      return { allowed: true };
    }
  }

  /**
   * 验证Token有效性
   */
  validateToken(token) {
    if (!token || typeof token !== 'string') {
      return false;
    }

    // 检查Token格式（这里使用简单的长度和字符检查）
    if (token.length < 10 || token.length > 500) {
      return false;
    }

    // 检查是否包含非法字符
    const validTokenPattern = /^[A-Za-z0-9._-]+$/;
    return validTokenPattern.test(token);
  }

  /**
   * 安全的JSON解析
   */
  safeJsonParse(jsonString, defaultValue = null) {
    try {
      if (typeof jsonString !== 'string') {
        return defaultValue;
      }

      // 检查JSON字符串长度
      if (jsonString.length > 1000000) { // 1MB限制
        console.warn('JSON字符串过长，可能存在安全风险');
        return defaultValue;
      }

      const parsed = JSON.parse(jsonString);
      
      // 过滤敏感数据
      return this.filterSensitiveData(parsed);
    } catch (error) {
      console.warn('JSON解析失败:', error);
      return defaultValue;
    }
  }

  /**
   * 安全的存储设置
   */
  secureSetStorage(key, value) {
    try {
      // 过滤敏感数据
      const filteredValue = this.filterSensitiveData(value);
      
      // 检查存储大小
      const serialized = JSON.stringify(filteredValue);
      if (serialized.length > 1048576) { // 1MB限制
        console.warn('存储数据过大');
        return false;
      }

      wx.setStorageSync(key, filteredValue);
      return true;
    } catch (error) {
      console.error('安全存储失败:', error);
      return false;
    }
  }

  /**
   * 安全的存储获取
   */
  secureGetStorage(key, defaultValue = null) {
    try {
      const value = wx.getStorageSync(key);
      return value !== '' ? value : defaultValue;
    } catch (error) {
      console.warn('安全获取存储失败:', error);
      return defaultValue;
    }
  }

  /**
   * 清理调试信息
   */
  cleanDebugInfo(obj) {
    if (typeof obj !== 'object' || obj === null) {
      return obj;
    }

    const cleaned = { ...obj };
    
    // 移除调试相关的字段
    const debugKeys = ['debug', 'trace', 'stack', 'error', 'warning'];
    debugKeys.forEach(key => {
      if (cleaned.hasOwnProperty(key)) {
        delete cleaned[key];
      }
    });

    return cleaned;
  }
}

module.exports = new Security();
