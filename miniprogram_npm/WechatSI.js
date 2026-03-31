/**
 * Simplified WechatSI plugin mock
 */

// Create basic record recognition manager
function createBasicRecordManager() {
  return {
    start: function() {
      console.log('[Basic Mock] Start recording');
    },
    stop: function() {
      console.log('[Basic Mock] Stop recording');
      if (typeof this.onStop === 'function') {
        setTimeout(() => {
          this.onStop({
            result: 'Simulated recognition result'
          });
        }, 500);
      }
    },
    onRecognize: null,
    onStop: null,
    onStart: null,
    onError: null
  };
}

// Basic module exports
module.exports = {
  getRecordRecognitionManager: function() {
    return createBasicRecordManager();
  },
  
  getTranslateManager: function() {
    return {
      translate: function(options) {
        if (options && typeof options.success === 'function') {
          setTimeout(() => {
            options.success({
              result: true,
              from: options.lfrom || 'en_US',
              to: options.lto || 'zh_CN',
              translateResult: ['Simulated translation result']
            });
          }, 500);
        }
      }
    };
  },
  
  textToSpeech: function(options) {
    if (options && typeof options.success === 'function') {
      setTimeout(() => {
        options.success({ result: true });
      }, 500);
    }
  },
  
  getTextToSpeechManager: function() {
    return {
      speak: function() {},
      stop: function() {}
    };
  }
}; 