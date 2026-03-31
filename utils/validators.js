/**
 * 数据验证器
 * 提供统一的数据验证和类型检查
 */

class Validators {
  /**
   * 验证是否为空
   */
  static isEmpty(value) {
    return value === null || value === undefined || value === '' || 
           (Array.isArray(value) && value.length === 0) ||
           (typeof value === 'object' && Object.keys(value).length === 0);
  }

  /**
   * 验证字符串
   */
  static isString(value, minLength = 0, maxLength = Infinity) {
    if (typeof value !== 'string') {
      return { valid: false, message: '必须是字符串类型' };
    }
    
    if (value.length < minLength) {
      return { valid: false, message: `长度不能少于${minLength}个字符` };
    }
    
    if (value.length > maxLength) {
      return { valid: false, message: `长度不能超过${maxLength}个字符` };
    }
    
    return { valid: true };
  }

  /**
   * 验证数字
   */
  static isNumber(value, min = -Infinity, max = Infinity) {
    if (typeof value !== 'number' || isNaN(value)) {
      return { valid: false, message: '必须是有效数字' };
    }
    
    if (value < min) {
      return { valid: false, message: `数值不能小于${min}` };
    }
    
    if (value > max) {
      return { valid: false, message: `数值不能大于${max}` };
    }
    
    return { valid: true };
  }

  /**
   * 验证URL
   */
  static isUrl(value) {
    if (typeof value !== 'string') {
      return { valid: false, message: 'URL必须是字符串类型' };
    }
    
    const urlPattern = /^https?:\/\/.+/;
    if (!urlPattern.test(value)) {
      return { valid: false, message: 'URL格式不正确' };
    }
    
    return { valid: true };
  }

  /**
   * 验证文件路径
   */
  static isFilePath(value) {
    if (typeof value !== 'string') {
      return { valid: false, message: '文件路径必须是字符串类型' };
    }
    
    if (this.isEmpty(value)) {
      return { valid: false, message: '文件路径不能为空' };
    }
    
    return { valid: true };
  }

  /**
   * 验证音频文件扩展名
   */
  static isAudioFile(filename) {
    if (typeof filename !== 'string') {
      return { valid: false, message: '文件名必须是字符串类型' };
    }
    
    const audioExtensions = ['.mp3', '.wav', '.m4a', '.flac', '.aac'];
    const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
    
    if (!audioExtensions.includes(extension)) {
      return { valid: false, message: '不支持的音频文件格式' };
    }
    
    return { valid: true };
  }

  /**
   * 验证图片文件扩展名
   */
  static isImageFile(filename) {
    if (typeof filename !== 'string') {
      return { valid: false, message: '文件名必须是字符串类型' };
    }
    
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];
    const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
    
    if (!imageExtensions.includes(extension)) {
      return { valid: false, message: '不支持的图片文件格式' };
    }
    
    return { valid: true };
  }

  /**
   * 验证对象结构
   */
  static validateObject(obj, schema) {
    const errors = [];
    
    for (const [key, rules] of Object.entries(schema)) {
      const value = obj[key];
      
      // 检查必填字段
      if (rules.required && this.isEmpty(value)) {
        errors.push(`${key}是必填字段`);
        continue;
      }
      
      // 如果字段为空且非必填，跳过其他验证
      if (this.isEmpty(value) && !rules.required) {
        continue;
      }
      
      // 类型验证
      if (rules.type) {
        let typeValid = false;
        let typeMessage = '';
        
        switch (rules.type) {
          case 'string':
            const stringResult = this.isString(value, rules.minLength, rules.maxLength);
            typeValid = stringResult.valid;
            typeMessage = stringResult.message;
            break;
          case 'number':
            const numberResult = this.isNumber(value, rules.min, rules.max);
            typeValid = numberResult.valid;
            typeMessage = numberResult.message;
            break;
          case 'url':
            const urlResult = this.isUrl(value);
            typeValid = urlResult.valid;
            typeMessage = urlResult.message;
            break;
          case 'array':
            typeValid = Array.isArray(value);
            typeMessage = '必须是数组类型';
            break;
          case 'object':
            typeValid = typeof value === 'object' && value !== null && !Array.isArray(value);
            typeMessage = '必须是对象类型';
            break;
        }
        
        if (!typeValid) {
          errors.push(`${key}: ${typeMessage}`);
        }
      }
      
      // 自定义验证函数
      if (rules.validator && typeof rules.validator === 'function') {
        const customResult = rules.validator(value);
        if (!customResult.valid) {
          errors.push(`${key}: ${customResult.message}`);
        }
      }
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * 验证API响应
   */
  static validateApiResponse(response) {
    if (!response) {
      return { valid: false, message: '响应为空' };
    }
    
    if (typeof response !== 'object') {
      return { valid: false, message: '响应格式不正确' };
    }
    
    // 检查常见的API响应格式
    if (response.hasOwnProperty('code') && response.hasOwnProperty('message')) {
      if (response.code !== 200 && response.code !== '200') {
        return { valid: false, message: response.message || '请求失败' };
      }
    }
    
    return { valid: true };
  }

  /**
   * 验证配置对象
   */
  static validateConfig(config) {
    const schema = {
      apiBaseUrl: { required: true, type: 'url' },
      musicApiBaseUrl: { required: true, type: 'url' },
      modelConfig: { required: true, type: 'object' },
      requestConfig: { required: false, type: 'object' }
    };
    
    return this.validateObject(config, schema);
  }

  /**
   * 验证用户信息
   */
  static validateUserInfo(userInfo) {
    const schema = {
      nickName: { required: true, type: 'string', minLength: 1, maxLength: 50 },
      avatarUrl: { required: false, type: 'string' },
      gender: { required: false, type: 'number', min: 0, max: 2 }
    };
    
    return this.validateObject(userInfo, schema);
  }

  /**
   * 验证音乐信息
   */
  static validateMusicInfo(musicInfo) {
    const schema = {
      id: { required: true, type: 'string' },
      title: { required: true, type: 'string', minLength: 1 },
      singer: { required: true, type: 'string', minLength: 1 },
      album: { required: false, type: 'string' },
      duration: { required: false, type: 'number', min: 0 }
    };
    
    return this.validateObject(musicInfo, schema);
  }
}

module.exports = Validators;
