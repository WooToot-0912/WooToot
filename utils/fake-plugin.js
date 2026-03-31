/**
 * WechatSI plugin mock file
 * Used to replace the removed WeChat speech translation plugin
 */

// Create a fake recording recognition manager
const createFakeRecordManager = () => {
  return {
    // Mock methods
    start: (options) => {
      console.log('[Mock] Fake record manager - start', options);
    },
    stop: () => {
      console.log('[Mock] Fake record manager - stop');
      // If onStop callback is set, call it with delay
      if (this.onStop) {
        setTimeout(() => {
          this.onStop({
            result: 'This is a simulated speech recognition result. Actual functionality is disabled.'
          });
        }, 1000);
      }
    },
    // Mock event handlers
    onRecognize: null,
    onStop: null,
    onStart: null,
    onError: null,
    // Mock recognize method
    recognize: (options) => {
      console.log('[Mock] Fake record manager - recognize', options);
      // If onStop callback is set, call it with delay
      if (this.onStop) {
        setTimeout(() => {
          this.onStop({
            result: 'This is a simulated speech recognition result. Actual functionality is disabled.'
          });
        }, 1000);
      }
    }
  };
};

// Create a fake translation manager
const createFakeTranslateManager = () => {
  return {
    translate: (options) => {
      console.log('[Mock] Fake translate manager - translate', options);
      // If callback function exists, call it
      if (options && options.success) {
        setTimeout(() => {
          options.success({
            translateResult: 'This is a simulated translation result. Actual functionality is disabled.'
          });
        }, 500);
      }
    }
  };
};

// Export fake plugin module
module.exports = {
  // Get fake recording recognition manager
  getRecordRecognitionManager: () => {
    console.log('[Mock] Getting fake recording recognition manager');
    return createFakeRecordManager();
  },
  
  // Get fake translation manager
  getTranslateManager: () => {
    console.log('[Mock] Getting fake translation manager');
    return createFakeTranslateManager();
  }
}; 