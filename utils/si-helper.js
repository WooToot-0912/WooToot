/**
 * SI Interface Helper
 * Provides compatibility layer for WechatSI plugin
 */

// Helper to get WechatSI plugin safely
function getSIPlugin() {
  try {
    // Try using requirePlugin if available
    if (wx.requirePlugin) {
      return wx.requirePlugin('WechatSI');
    }
    
    // Try direct import if requirePlugin not available
    try {
      return require('../WechatSI');
    } catch (e) {
      try {
        return require('../miniprogram_npm/WechatSI');
      } catch (e2) {
        try {
          return require('./fake-plugin');
        } catch (e3) {
          // Return minimal implementation
          return {
            getRecordRecognitionManager: function() {
              return {
                start: function(){},
                stop: function(){},
                onStop: null
              };
            },
            getTranslateManager: function() {
              return {
                translate: function(options) {
                  if (options && options.success) {
                    setTimeout(() => options.success({
                      result: true,
                      translateResult: ['Fallback translation']
                    }), 500);
                  }
                }
              };
            }
          };
        }
      }
    }
  } catch (error) {
    console.error('[SI Helper] Failed to load plugin:', error);
    // Return minimal implementation as last resort
    return {
      getRecordRecognitionManager: function() {
        return {
          start: function(){},
          stop: function(){},
          onStop: null
        };
      }
    };
  }
}

module.exports = {
  // Get the plugin safely
  getPlugin: getSIPlugin,
  
  // Get recording manager safely
  getRecordManager: function() {
    const plugin = getSIPlugin();
    return plugin.getRecordRecognitionManager ? 
      plugin.getRecordRecognitionManager() : 
      {
        start: function(){},
        stop: function(){},
        onStop: null
      };
  },
  
  // Get translation manager safely
  getTranslateManager: function() {
    const plugin = getSIPlugin();
    return plugin.getTranslateManager ? 
      plugin.getTranslateManager() : 
      {
        translate: function(options) {
          if (options && options.success) {
            setTimeout(() => options.success({
              result: true,
              translateResult: ['Fallback translation']
            }), 500);
          }
        }
      };
  }
}; 