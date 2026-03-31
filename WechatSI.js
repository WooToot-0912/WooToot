/**
 * Ultra-simple WechatSI mock
 */

module.exports = {
  // Mock recording recognition manager
  getRecordRecognitionManager: function() {
    return {
      start: function(){},
      stop: function(){},
      onStart: null,
      onStop: null,
      onError: null,
      onRecognize: null
    };
  },
  
  // Mock translation manager
  getTranslateManager: function() {
    return {
      translate: function(options) {
        if (options && typeof options.success === 'function') {
          setTimeout(() => options.success({
            result: true,
            translateResult: ['Mock result']
          }), 100);
        }
      }
    };
  },
  
  // Mock text to speech
  textToSpeech: function(options) {
    if (options && typeof options.success === 'function') {
      setTimeout(() => options.success({}), 100);
    }
  },
  
  // Mock text to speech manager
  getTextToSpeechManager: function() {
    return {
      speak: function(){},
      stop: function(){}
    };
  }
} 