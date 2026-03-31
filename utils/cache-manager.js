/**
 * 缓存管理器
 * 提供统一的缓存策略，包括内存缓存和本地存储缓存
 */

class CacheManager {
  constructor() {
    this.memoryCache = new Map();
    this.maxMemorySize = 50; // 最大内存缓存条目数
    this.defaultTTL = 5 * 60 * 1000; // 默认5分钟过期
  }

  /**
   * 设置缓存
   */
  set(key, value, ttl = this.defaultTTL, useStorage = false) {
    const expireTime = Date.now() + ttl;
    const cacheItem = {
      value,
      expireTime,
      timestamp: Date.now()
    };

    if (useStorage) {
      try {
        wx.setStorageSync(`cache_${key}`, cacheItem);
      } catch (error) {
        console.warn('设置本地缓存失败:', error);
      }
    } else {
      // 内存缓存大小控制
      if (this.memoryCache.size >= this.maxMemorySize) {
        this._evictOldest();
      }
      this.memoryCache.set(key, cacheItem);
    }
  }

  /**
   * 获取缓存
   */
  get(key, useStorage = false) {
    let cacheItem;

    if (useStorage) {
      try {
        cacheItem = wx.getStorageSync(`cache_${key}`);
      } catch (error) {
        console.warn('获取本地缓存失败:', error);
        return null;
      }
    } else {
      cacheItem = this.memoryCache.get(key);
    }

    if (!cacheItem) {
      return null;
    }

    // 检查是否过期
    if (Date.now() > cacheItem.expireTime) {
      this.delete(key, useStorage);
      return null;
    }

    return cacheItem.value;
  }

  /**
   * 删除缓存
   */
  delete(key, useStorage = false) {
    if (useStorage) {
      try {
        wx.removeStorageSync(`cache_${key}`);
      } catch (error) {
        console.warn('删除本地缓存失败:', error);
      }
    } else {
      this.memoryCache.delete(key);
    }
  }

  /**
   * 清空所有缓存
   */
  clear() {
    this.memoryCache.clear();
    
    try {
      const storageInfo = wx.getStorageInfoSync();
      const cacheKeys = storageInfo.keys.filter(key => key.startsWith('cache_'));
      cacheKeys.forEach(key => {
        wx.removeStorageSync(key);
      });
    } catch (error) {
      console.warn('清空本地缓存失败:', error);
    }
  }

  /**
   * 移除最旧的缓存项
   */
  _evictOldest() {
    let oldestKey = null;
    let oldestTime = Date.now();

    for (const [key, item] of this.memoryCache) {
      if (item.timestamp < oldestTime) {
        oldestTime = item.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.memoryCache.delete(oldestKey);
    }
  }

  /**
   * 获取缓存统计信息
   */
  getStats() {
    const memorySize = this.memoryCache.size;
    let storageSize = 0;

    try {
      const storageInfo = wx.getStorageInfoSync();
      storageSize = storageInfo.keys.filter(key => key.startsWith('cache_')).length;
    } catch (error) {
      console.warn('获取存储缓存统计失败:', error);
    }

    return {
      memorySize,
      storageSize,
      maxMemorySize: this.maxMemorySize
    };
  }

  /**
   * 缓存API响应
   */
  async cacheApiResponse(key, apiCall, ttl = this.defaultTTL, useStorage = false) {
    // 先尝试从缓存获取
    const cached = this.get(key, useStorage);
    if (cached) {
      console.log(`缓存命中: ${key}`);
      return cached;
    }

    // 缓存未命中，执行API调用
    try {
      const result = await apiCall();
      this.set(key, result, ttl, useStorage);
      console.log(`缓存设置: ${key}`);
      return result;
    } catch (error) {
      console.error(`API调用失败: ${key}`, error);
      throw error;
    }
  }

  /**
   * 生成缓存键
   */
  generateKey(prefix, ...params) {
    return `${prefix}_${params.join('_')}`;
  }
}

module.exports = new CacheManager();
